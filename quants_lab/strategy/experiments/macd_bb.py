import pandas_ta as ta
from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase

from quants_lab.utils import data_management


class MACDBB(DirectionalStrategyBase):
    def __init__(self,
                 exchange="binance_perpetual",
                 trading_pair="ETH-USDT",
                 interval="1h",
                 bb_length=24,
                 bb_std=2.0,
                 bb_long_threshold=0.05,
                 bb_short_threshold=0.95,
                 fast_macd=21,
                 slow_macd=42,
                 signal_macd=9):
        self.exchange = exchange
        self.trading_pair = trading_pair
        self.interval = interval
        self.bb_length = bb_length
        self.bb_std = bb_std
        self.bb_long_threshold = bb_long_threshold
        self.bb_short_threshold = bb_short_threshold
        self.fast_macd = fast_macd
        self.slow_macd = slow_macd
        self.signal_macd = signal_macd

    def get_raw_data(self):
        df = data_management.get_dataframe(
            exchange=self.exchange,
            trading_pair=self.trading_pair,
            interval=self.interval,
        )
        return df

    def preprocessing(self, df):
        df.ta.bbands(length=self.bb_length, std=self.bb_std, append=True)
        df.ta.macd(fast=self.fast_macd, slow=self.slow_macd, signal=self.signal_macd, append=True)
        return df

    def predict(self, df):
        bbp = df[f"BBP_{self.bb_length}_{self.bb_std}"]
        macdh = df[f"MACDh_{self.fast_macd}_{self.slow_macd}_{self.signal_macd}"]
        macd = df[f"MACD_{self.fast_macd}_{self.slow_macd}_{self.signal_macd}"]

        long_condition = (bbp < self.bb_long_threshold) & (macdh > 0) & (macd < 0)
        short_condition = (bbp > self.bb_short_threshold) & (macdh < 0) & (macd > 0)

        df["side"] = 0
        df.loc[long_condition, "side"] = 1
        df.loc[short_condition, "side"] = -1
        return df
