import time
from typing import Optional, Callable

import pandas as pd
from pydantic import Field

from hummingbot.smart_components.executors.position_executor.position_executor import PositionExecutor
from hummingbot.smart_components.strategy_frameworks.data_types import OrderLevel
from hummingbot.smart_components.strategy_frameworks.directional_trading.directional_trading_controller_base import (
    DirectionalTradingControllerBase,
    DirectionalTradingControllerConfigBase,
)


class SuperTrendMTConfig(DirectionalTradingControllerConfigBase):
    strategy_name: str = "supertrend_multitimeframe"
    length: int = Field(default=20, ge=5, le=200)
    multiplier: float = Field(default=4.0, ge=2.0, le=7.0)
    percentage_threshold: float = Field(default=0.01, ge=0.005, le=0.05)


class SuperTrendMT(DirectionalTradingControllerBase):
    def __init__(self, config: SuperTrendMTConfig):
        super().__init__(config)
        self.config = config

    def early_stop_condition(self, executor: PositionExecutor, order_level: OrderLevel) -> bool:
        # If an executor has an active position, should we close it based on a condition. This feature is not available
        # for the backtesting yet
        return False

    def cooldown_condition(self, executor: PositionExecutor, order_level: OrderLevel) -> bool:
        # After finishing an order, the executor will be in cooldown for a certain amount of time.
        # This prevents the executor from creating a new order immediately after finishing one and execute a lot
        # of orders in a short period of time from the same side.
        if executor.close_timestamp and executor.close_timestamp + order_level.cooldown_time > time.time():
            return True
        return False

    @staticmethod
    def get_minutes_from_interval(interval: str):
        unit = interval[-1]
        quantity = int(interval[:-1])
        conversion = {"m": 1, "h": 60, "d": 1440}
        return conversion[unit] * quantity

    def ordered_market_data_dfs(self):
        market_data = {f"{candles.name}_{candles.interval}": candles.candles_df for candles in self.candles}
        return sorted(market_data.items(), key=lambda x: self.get_minutes_from_interval(x[0].split("_")[-1]))

    def get_dataframes_merged_by_min_resolution(self, add_indicators_func: Optional[Callable] = None):
        ordered_data = self.ordered_market_data_dfs()
        if add_indicators_func:
            processed_data = []
            for interval, df in ordered_data:
                processed_df = add_indicators_func(df)
                processed_data.append((interval, processed_df))
        else:
            processed_data = ordered_data
        interval_suffixes = {key: f'_{key.split("_")[-1]}' for key, _ in processed_data}
        merged_df = None
        for interval, df in processed_data:
            if merged_df is None:
                merged_df = df.copy()
            else:
                merged_df = pd.merge_asof(merged_df, df.add_suffix(interval_suffixes[interval]),
                                          left_on=f"timestamp", right_on=f"timestamp{interval_suffixes[interval]}",
                                          direction="backward")
        return merged_df

    def add_indicators(self, df):
        df.ta.supertrend(length=self.config.length, multiplier=self.config.multiplier, append=True)
        return df

    def get_processed_data(self) -> pd.DataFrame:
        df = self.get_dataframes_merged_by_min_resolution(self.add_indicators)
        df["percentage_distance"] = abs(df["close"] - df[f"SUPERT_{self.config.length}_{self.config.multiplier}"]) / df["close"]

        columns_with_supertrend = [col for col in df.columns if "SUPERTd" in col]

        # Conditions for long and short signals
        long_condition = df[columns_with_supertrend].apply(lambda x: all(item == 1 for item in x), axis=1)
        short_condition = df[columns_with_supertrend].apply(lambda x: all(item == -1 for item in x), axis=1)

        # Choose side
        df['signal'] = 0
        df.loc[long_condition, 'signal'] = 1
        df.loc[short_condition, 'signal'] = -1
        return df
