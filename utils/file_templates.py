from typing import Dict


def directional_strategy_template(strategy_cls_name: str) -> str:
    strategy_config_cls_name = f"{strategy_cls_name}Config"
    sma_config_text = "{self.config.sma_length}"
    return f"""import pandas_ta as ta
from pydantic import BaseModel, Field

from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase


class {strategy_config_cls_name}(BaseModel):
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
    fields_str = [get_optuna_suggest_str(field_name, properties) for field_name, properties in field_schema.items()]
    fields_str = "".join([f"                    {field_str},\n" for field_str in fields_str])
    return f"""import traceback

from optuna import TrialPruned    

from quants_lab.strategy.experiments.{strategy_module} import {strategy_cls.__name__}, {strategy_config.__name__}
from quants_lab.strategy.strategy_analysis import StrategyAnalysis


def objective(trial):
    try:
        config = {strategy_config.__name__}(
{fields_str}
        )
        strategy = {strategy_cls.__name__}(config=config)
        market_data, positions = strategy.run_backtesting(
            start='2021-04-01',
            order_amount=50,
            leverage=20,
            initial_portfolio=100,
            take_profit_multiplier=trial.suggest_float("take_profit_multiplier", 1.0, 3.0),
            stop_loss_multiplier=trial.suggest_float("stop_loss_multiplier", 1.0, 3.0),
            time_limit=60 * 60 * trial.suggest_int("time_limit", 1, 24),
            std_span=None,
        )
        strategy_analysis = StrategyAnalysis(
            positions=positions,
        )
    
        trial.set_user_attr("net_profit_usd", strategy_analysis.net_profit_usd())
        trial.set_user_attr("net_profit_pct", strategy_analysis.net_profit_pct())
        trial.set_user_attr("max_drawdown_usd", strategy_analysis.max_drawdown_usd())
        trial.set_user_attr("max_drawdown_pct", strategy_analysis.max_drawdown_pct())
        trial.set_user_attr("sharpe_ratio", strategy_analysis.sharpe_ratio())
        trial.set_user_attr("accuracy", strategy_analysis.accuracy())
        trial.set_user_attr("total_positions", strategy_analysis.total_positions())
        trial.set_user_attr("win_signals", strategy_analysis.win_signals().shape[0])
        trial.set_user_attr("loss_signals", strategy_analysis.loss_signals().shape[0])
        trial.set_user_attr("profit_factor", strategy_analysis.profit_factor())
        trial.set_user_attr("duration_in_hours", strategy_analysis.duration_in_minutes() / 60)
        trial.set_user_attr("avg_trading_time_in_hours", strategy_analysis.avg_trading_time_in_minutes() / 60)
        return strategy_analysis.net_profit_pct()
    except Exception as e:
        traceback.print_exc()
        raise TrialPruned()
    """
