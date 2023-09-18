from typing import Dict


def directional_trading_controller_template(strategy_cls_name: str) -> str:
    strategy_config_cls_name = f"{strategy_cls_name}Config"
    sma_config_text = "{self.config.sma_length}"
    return f"""import time
from typing import Optional

import pandas as pd
from pydantic import Field

from hummingbot.smart_components.executors.position_executor.position_executor import PositionExecutor
from hummingbot.smart_components.strategy_frameworks.data_types import OrderLevel
from hummingbot.smart_components.strategy_frameworks.directional_trading.directional_trading_controller_base import (
    DirectionalTradingControllerBase,
    DirectionalTradingControllerConfigBase,
)

class {strategy_config_cls_name}(DirectionalTradingControllerConfigBase):
    strategy_name: str = "{strategy_cls_name.lower()}"
    sma_length: int = Field(default=20, ge=10, le=200)
    # ... Add more fields here


class {strategy_cls_name}(DirectionalTradingControllerBase):

    def __init__(self, config: {strategy_config_cls_name}):
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
        df.ta.sma(length=self.config.sma_length, append=True)
        # ... Add more indicators here
        # ... Check https://github.com/twopirllc/pandas-ta#indicators-by-category for more indicators
        # ... Use help(ta.indicator_name) to get more info

        # Generate long and short conditions
        long_cond = (df['close'] > df[f'SMA_{sma_config_text}'])
        short_cond = (df['close'] < df[f'SMA_{sma_config_text}'])

        # Choose side
        df['signal'] = 0
        df.loc[long_cond, 'signal'] = 1
        df.loc[short_cond, 'signal'] = -1
        return df
"""


def get_optuna_suggest_str(field_name: str, properties: Dict):
    if field_name == "candles_config":
        return f"""{field_name}=[
                        CandlesConfig(connector=exchange, trading_pair=trading_pair, 
                                      interval="3m", max_records=1000000)  # Max number of candles for the real-time bot,
                    ]"""
    if field_name == "strategy_name":
        return f"{field_name}='{properties.get('default', '_')}'"
    if field_name in ["order_levels", "trading_pair", "exchange"]:
        return f"{field_name}={field_name}"
    if field_name == "position_mode":
        return f"{field_name}=PositionMode.HEDGE"
    if field_name == "leverage":
        return f"{field_name}=10"
    map_by_type = {
        "number": "trial.suggest_float",
        "integer": "trial.suggest_int",
        "string": "trial.suggest_categorical",
    }
    config_num = f"('{field_name}', {properties.get('minimum', '_')}, {properties.get('maximum', '_')}, step=0.01)"
    config_cat = f"('{field_name}', ['{properties.get('default', '_')}',])"
    optuna_trial_str = map_by_type[properties["type"]] + config_num if properties["type"] != "string" \
        else map_by_type[properties["type"]] + config_cat

    return f"{field_name}={optuna_trial_str}"


def strategy_optimization_template(strategy_info: dict):
    strategy_cls = strategy_info["class"]
    strategy_config = strategy_info["config"]
    strategy_module = strategy_info["module"]
    field_schema = strategy_config.schema()["properties"]
    fields_str = [get_optuna_suggest_str(field_name, properties) for field_name, properties in field_schema.items()]
    fields_str = "".join([f"                    {field_str},\n" for field_str in fields_str])
    return f"""import traceback
from decimal import Decimal

from hummingbot.core.data_type.common import PositionMode, TradeType, OrderType
from hummingbot.data_feed.candles_feed.candles_factory import CandlesConfig
from hummingbot.smart_components.strategy_frameworks.data_types import TripleBarrierConf, OrderLevel
from hummingbot.smart_components.strategy_frameworks.directional_trading import DirectionalTradingBacktestingEngine
from hummingbot.smart_components.utils import ConfigEncoderDecoder
from optuna import TrialPruned   

from quants_lab.controllers.{strategy_module} import {strategy_cls.__name__}, {strategy_config.__name__}


def objective(trial):
    try:
        # General configuration for the backtesting
        exchange = trial.suggest_categorical('exchange', ['binance_perpetual', ])
        trading_pair = trial.suggest_categorical('trading_pair', ['BTC-USDT', ])
        start = "2023-01-01"
        end = "2023-08-01"
        initial_portfolio_usd = 1000.0
        trade_cost = 0.0006
        
        # The definition of order levels is not so necessary for directional strategies now but let's you customize the
        # amounts for going long or short, the cooldown time between orders and the triple barrier configuration
        stop_loss = trial.suggest_float('stop_loss', 0.005, 0.02)
        take_profit = trial.suggest_float('take_profit', 0.005, 0.05)
        time_limit = trial.suggest_int('time_limit', 60 * 60 * 2, 60 * 60 * 24)

        triple_barrier_conf = TripleBarrierConf(
            stop_loss=Decimal(stop_loss), take_profit=Decimal(take_profit),
            time_limit=time_limit,
            trailing_stop_activation_price_delta=Decimal("0.008"),  # It's not working yet with the backtesting engine
            trailing_stop_trailing_delta=Decimal("0.004"),
        )
        
        order_levels = [
            OrderLevel(level=0, side=TradeType.BUY, order_amount_usd=Decimal(50),
                       cooldown_time=15, triple_barrier_conf=triple_barrier_conf),
            OrderLevel(level=0, side=TradeType.SELL, order_amount_usd=Decimal(50),
                       cooldown_time=15, triple_barrier_conf=triple_barrier_conf),
        ]
        config = {strategy_config.__name__}(
{fields_str}
        )
        controller = {strategy_cls.__name__}(config=config)
        engine = DirectionalTradingBacktestingEngine(controller=controller)
        engine.load_controller_data("./data/candles")
        backtesting_results = engine.run_backtesting(initial_portfolio_usd=initial_portfolio_usd, trade_cost=trade_cost, 
                                                     start=start, end=end)

        strategy_analysis = backtesting_results["results"]
        encoder_decoder = ConfigEncoderDecoder(TradeType, OrderType, PositionMode)

        trial.set_user_attr("net_pnl_quote", strategy_analysis["net_pnl_quote"])
        trial.set_user_attr("net_pnl_pct", strategy_analysis["net_pnl"])
        trial.set_user_attr("max_drawdown_usd", strategy_analysis["max_drawdown_usd"])
        trial.set_user_attr("max_drawdown_pct", strategy_analysis["max_drawdown_pct"])
        trial.set_user_attr("sharpe_ratio", strategy_analysis["sharpe_ratio"])
        trial.set_user_attr("accuracy", strategy_analysis["accuracy"])
        trial.set_user_attr("total_positions", strategy_analysis["total_positions"])
        trial.set_user_attr("profit_factor", strategy_analysis["profit_factor"])
        trial.set_user_attr("duration_in_hours", strategy_analysis["duration_minutes"] / 60)
        trial.set_user_attr("avg_trading_time_in_hours", strategy_analysis["avg_trading_time_minutes"] / 60)
        trial.set_user_attr("win_signals", strategy_analysis["win_signals"])
        trial.set_user_attr("loss_signals", strategy_analysis["loss_signals"])
        trial.set_user_attr("config", encoder_decoder.encode(config.dict()))
        return strategy_analysis["net_pnl"]
    except Exception as e:
        traceback.print_exc()
        raise TrialPruned()
    """
