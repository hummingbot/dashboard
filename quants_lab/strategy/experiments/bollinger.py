import pandas_ta as ta
from pydantic import BaseModel, Field

from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase


class BollingerConf(BaseModel):
    exchange: str = Field(default="binance_perpetual")
    trading_pair: str = Field(default="ETH-USDT")
    interval: str = Field(default="1h")
    bb_length: int = Field(default=100, ge=2, le=1000)
    bb_std: float = Field(default=2.0, ge=0.5, le=4.0)
    bb_long_threshold: float = Field(default=0.0, ge=-3.0, le=0.5)
    bb_short_threshold: float = Field(default=1.0, ge=0.5, le=3.0)


class Bollinger(DirectionalStrategyBase[BollingerConf]):
    def get_raw_data(self):
        df = self.get_candles(
            exchange=self.config.exchange,
            trading_pair=self.config.trading_pair,
            interval=self.config.interval,
        )
        return df

    def preprocessing(self, df):
        df.ta.bbands(length=self.config.bb_length, std=self.config.bb_std, append=True)
        return df

    def predict(self, df):
        df["side"] = 0
        long_condition = df[f"BBP_{self.config.bb_length}_{self.config.bb_std}"] < self.config.bb_long_threshold
        short_condition = df[f"BBP_{self.config.bb_length}_{self.config.bb_std}"] > self.config.bb_short_threshold
        df.loc[long_condition, "side"] = 1
        df.loc[short_condition, "side"] = -1
        return df
