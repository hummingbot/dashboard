import pandas as pd
import pandas_ta as ta
from pydantic import BaseModel, Field

from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase


class StatArbConfig(BaseModel):
    exchange: str = Field(default="binance_perpetual")
    trading_pair: str = Field(default="ETH-USDT")
    target_trading_pair: str = Field(default="BTC-USDT")
    interval: str = Field(default="1h")
    lookback: int = Field(default=100, ge=2, le=10000)
    z_score_long: float = Field(default=2, ge=0, le=5)
    z_score_short: float = Field(default=-2, ge=-5, le=0)


class StatArb(DirectionalStrategyBase):
    def __init__(self, config: StatArbConfig):
        super().__init__(config)
        self.exchange = config.exchange
        self.trading_pair = config.trading_pair
        self.target_trading_pair = config.target_trading_pair
        self.interval = config.interval
        self.lookback = config.lookback
        self.z_score_long = config.z_score_long
        self.z_score_short = config.z_score_short

    def get_raw_data(self):
        df = self.get_candles(
            exchange=self.exchange,
            trading_pair=self.trading_pair,
            interval=self.interval,
        )
        df_target = self.get_candles(
            exchange=self.exchange,
            trading_pair=self.target_trading_pair,
            interval=self.interval,
        )
        df = pd.merge(df, df_target, on="timestamp", how='inner', suffixes=('', '_target'))
        return df

    def preprocessing(self, df):
        df["pct_change_original"] = df["close"].pct_change()
        df["pct_change_target"] = df["close_target"].pct_change()
        df["spread"] = df["pct_change_target"] - df["pct_change_original"]
        df["cum_spread"] = df["spread"].rolling(self.lookback).sum()
        df["z_score"] = ta.zscore(df["cum_spread"], length=self.lookback)
        return df

    def predict(self, df):
        df["side"] = 0
        short_condition = df["z_score"] < - self.z_score_short
        long_condition = df["z_score"] > self.z_score_long
        df.loc[long_condition, "side"] = 1
        df.loc[short_condition, "side"] = -1
        return df
