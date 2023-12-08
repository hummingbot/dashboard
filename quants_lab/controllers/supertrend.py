import time

import pandas as pd
from pydantic import Field

from hummingbot.smart_components.executors.position_executor.position_executor import PositionExecutor
from hummingbot.smart_components.strategy_frameworks.data_types import OrderLevel
from hummingbot.smart_components.strategy_frameworks.directional_trading.directional_trading_controller_base import (
    DirectionalTradingControllerBase,
    DirectionalTradingControllerConfigBase,
)


class SuperTrendConfig(DirectionalTradingControllerConfigBase):
    strategy_name: str = "supertrend"
    length: int = Field(default=20, ge=5, le=200)
    multiplier: float = Field(default=4.0, ge=2.0, le=7.0)
    percentage_threshold: float = Field(default=0.01, ge=0.005, le=0.05)


class SuperTrend(DirectionalTradingControllerBase):
    def __init__(self, config: SuperTrendConfig):
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

    def get_processed_data(self) -> pd.DataFrame:
        df = self.candles[0].candles_df
        df.ta.supertrend(length=self.config.length, multiplier=self.config.multiplier, append=True)
        df["percentage_distance"] = abs(df["close"] - df[f"SUPERT_{self.config.length}_{self.config.multiplier}"]) / df["close"]

        # Generate long and short conditions
        long_condition = (df[f"SUPERTd_{self.config.length}_{self.config.multiplier}"] == 1) & (df["percentage_distance"] < self.config.percentage_threshold)
        short_condition = (df[f"SUPERTd_{self.config.length}_{self.config.multiplier}"] == -1) & (df["percentage_distance"] < self.config.percentage_threshold)

        # Choose side
        df['signal'] = 0
        df.loc[long_condition, 'signal'] = 1
        df.loc[short_condition, 'signal'] = -1
        return df
