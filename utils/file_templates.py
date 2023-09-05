from typing import Dict


def directional_strategy_template(strategy_cls_name: str) -> str:
    strategy_config_cls_name = f"{strategy_cls_name}Config"
    sma_config_text = "{self.config.sma_length}"
    return f"""import pandas_ta as ta
from pydantic import BaseModel, Field

from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase


class {strategy_config_cls_name}(BaseModel):
    name: str = "{strategy_cls_name.lower()}"
    exchange: str = Field(default="binance_perpetual")
    trading_pair: str = Field(default="ETH-USDT")
    interval: str = Field(default="1h")
    sma_length: int = Field(default=20, ge=10, le=200)
    # ... Add more fields here


class {strategy_cls_name}(DirectionalStrategyBase[{strategy_config_cls_name}]):

    def get_raw_data(self):
        # The method get candles will search for the data in the folder data/candles
        # If the data is not there, you can use the candles downloader to get the data
        df = self.get_candles(
            exchange=self.config.exchange,
            trading_pair=self.config.trading_pair,
            interval=self.config.interval,
        )
        return df

    def preprocessing(self, df):
        df.ta.sma(length=self.config.sma_length, append=True)
        # ... Add more indicators here
        # ... Check https://github.com/twopirllc/pandas-ta#indicators-by-category for more indicators
        # ... Use help(ta.indicator_name) to get more info
        return df

    def predict(self, df):
        # Generate long and short conditions
        long_cond = (df['close'] > df[f'SMA_{sma_config_text}'])
        short_cond = (df['close'] < df[f'SMA_{sma_config_text}'])

        # Choose side
        df['side'] = 0
        df.loc[long_cond, 'side'] = 1
        df.loc[short_cond, 'side'] = -1
        return df
"""


def get_optuna_suggest_str(field_name: str, properties: Dict):
    if field_name == "candles_config":
        return f"""{field_name}=[
                        CandlesConfig(connector=exchange, trading_pair=trading_pair, 
                                      interval="3m", max_records=1000000)  # Max number of candles for the real-time bot,
                    ]"""
    if field_name == "order_levels":
        return f"{field_name}=order_levels"
    if field_name == "trading_pair":
        return f"{field_name}=trading_pair"
    if field_name == "exchange":
        return f"{field_name}=exchange"
    if field_name == "position_mode":
        return f"{field_name}=PositionMode.HEDGE"
    if field_name == "leverage":
        return f"{field_name}=10"
    map_by_type = {
        "number": "trial.suggest_float",
        "integer": "trial.suggest_int",
        "string": "trial.suggest_categorical",
    }
    config_num = f"('{field_name}', {properties.get('minimum', '_')}, {properties.get('maximum', '_')})"
    config_cat = f"('{field_name}', ['{properties.get('default', '_')}',])"
    optuna_trial_str = map_by_type[properties["type"]] + config_num if properties["type"] != "string" \
        else map_by_type[properties["type"]] + config_cat

    return f"{field_name}={optuna_trial_str}"


def strategy_optimization_template(strategy_info: dict):
    strategy_cls = strategy_info["class"]
    strategy_config = strategy_info["config"]
    strategy_module = strategy_info["module"]
    field_schema = strategy_config.schema()["properties"]
    config_to_save_str = "{config: value for config, value in config.dict().items() if config not in ['position_mode', 'order_levels']}"
    fields_str = [get_optuna_suggest_str(field_name, properties) for field_name, properties in field_schema.items()]
    fields_str = "".join([f"                    {field_str},\n" for field_str in fields_str])
    return f"""import traceback
from decimal import Decimal

from hummingbot.core.data_type.common import OrderType
from hummingbot.core.data_type.common import TradeType, PositionMode
from hummingbot.data_feed.candles_feed.candles_factory import CandlesConfig
from hummingbot.smart_components.strategy_frameworks.data_types import TripleBarrierConf, OrderLevel
from hummingbot.smart_components.strategy_frameworks.directional_trading import DirectionalTradingBacktestingEngine
from optuna import TrialPruned   

from quants_lab.strategy.controllers.{strategy_module} import {strategy_cls.__name__}, {strategy_config.__name__}


def objective(trial):
    try:
        exchange = trial.suggest_categorical('exchange', ['binance_perpetual', ])
        trading_pair = trial.suggest_categorical('trading_pair', ['BTC-USDT', ])
        stop_loss = trial.suggest_float('stop_loss', 0.001, 0.01)
        take_profit = trial.suggest_float('take_profit', 0.01, 0.05)
        time_limit = trial.suggest_int('time_limit', 60 * 60 * 2, 60 * 60 * 24)

        triple_barrier_conf = TripleBarrierConf(
            stop_loss=Decimal(stop_loss), take_profit=Decimal(take_profit),
            time_limit=time_limit,
            trailing_stop_activation_price_delta=Decimal("0.008"),
            trailing_stop_trailing_delta=Decimal("0.004"),
        )
        order_levels = [
            OrderLevel(level=0, side=TradeType.BUY, order_amount_usd=Decimal(15),
                       cooldown_time=15, triple_barrier_conf=triple_barrier_conf),
            OrderLevel(level=0, side=TradeType.SELL, order_amount_usd=Decimal(15),
                       cooldown_time=15, triple_barrier_conf=triple_barrier_conf),
        ]
        config = {strategy_config.__name__}(
{fields_str}
        )
        controller = {strategy_cls.__name__}(config=config)
        engine = DirectionalTradingBacktestingEngine(controller=controller)
        engine.load_controller_data("./data/candles")
        backtesting_results = engine.run_backtesting()

        strategy_analysis = backtesting_results["results"]
        config_to_save = {config_to_save_str}

        config_to_save["order_levels"] = [order_level.to_dict() for order_level in config.order_levels]
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
        trial.set_user_attr("config", config_to_save)
        return strategy_analysis["net_pnl"]
    except Exception as e:
        traceback.print_exc()
        raise TrialPruned()
    """
