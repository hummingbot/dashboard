import pandas_ta as ta
from pydantic import BaseModel, Field

from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase


class MACDBBConfig(BaseModel):
    exchange: str = Field(default="binance_perpetual")
    trading_pair: str = Field(default="ETH-USDT")
    interval: str = Field(default="1h")
    bb_length: int = Field(default=24, ge=2, le=1000)
    bb_std: float = Field(default=2.0, ge=0.5, le=4.0)
    bb_long_threshold: float = Field(default=0.0, ge=-3.0, le=0.5)
    bb_short_threshold: float = Field(default=1.0, ge=0.5, le=3.0)
    fast_macd: int = Field(default=21, ge=2, le=100)
    slow_macd: int = Field(default=42, ge=30, le=1000)
    signal_macd: int = Field(default=9, ge=2, le=100)


class MacdBollinger(DirectionalStrategyBase[MACDBBConfig]):
    def get_raw_data(self):
        df = self.get_candles(
            exchange=self.config.exchange,
            trading_pair=self.config.trading_pair,
            interval=self.config.interval,
        )
        return df

    def preprocessing(self, df):
        df.ta.bbands(length=self.config.bb_length, std=self.config.bb_std, append=True)
        df.ta.macd(fast=self.config.fast_macd, slow=self.config.slow_macd, signal=self.config.signal_macd, append=True)
        return df

    def predict(self, df):
        bbp = df[f"BBP_{self.config.bb_length}_{self.config.bb_std}"]
        macdh = df[f"MACDh_{self.config.fast_macd}_{self.config.slow_macd}_{self.config.signal_macd}"]
        macd = df[f"MACD_{self.config.fast_macd}_{self.config.slow_macd}_{self.config.signal_macd}"]

        long_condition = (bbp < self.config.bb_long_threshold) & (macdh > 0) & (macd < 0)
        short_condition = (bbp > self.config.bb_short_threshold) & (macdh < 0) & (macd > 0)

        df["side"] = 0
        df.loc[long_condition, "side"] = 1
        df.loc[short_condition, "side"] = -1
        return df
