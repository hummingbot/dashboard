import pandas as pd
import pandas_ta as ta
from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase

from quants_lab.utils import data_management


class StatArb(DirectionalStrategyBase):
    def __init__(self,
                 exchange="binance_perpetual",
                 trading_pair="DOGE-USDT",
                 target_trading_pair="BTC-USDT",
                 interval="1h",
                 periods=100,
                 deviation_threshold=1.1):
        self.exchange = exchange
        self.trading_pair = trading_pair
        self.interval = interval
        self.target_trading_pair = target_trading_pair
        self.periods = periods
        self.deviation_threshold = deviation_threshold

    def get_raw_data(self):
        df = data_management.get_dataframe(
            exchange=self.exchange,
            trading_pair=self.trading_pair,
            interval=self.interval,
        )
        df_target = data_management.get_dataframe(
            exchange=self.exchange,
            trading_pair=self.target_trading_pair,
            interval=self.interval,
        )
        df = pd.merge(df, df_target, on="timestamp", how='inner', suffixes=('', '_target'))
        return df

    def add_indicators(self, df):
        df["pct_change_original"] = df["close"].pct_change()
        df["pct_change_target"] = df["close_target"].pct_change()
        df["spread"] = df["pct_change_target"] - df["pct_change_original"]
        df["cum_spread"] = df["spread"].rolling(self.periods).sum()
        df["z_score"] = ta.zscore(df["cum_spread"], length=self.periods)
        return df

    def add_signals(self, df):
        df["side"] = 0
        short_condition = df["z_score"] < - self.deviation_threshold
        long_condition = df["z_score"] > self.deviation_threshold
        df.loc[long_condition, "side"] = 1
        df.loc[short_condition, "side"] = -1
        return df
