from decimal import Decimal
import pandas as pd
import pandas_ta as ta

from hummingbot.data_feed.candles_feed.candles_factory import CandlesFactory
from hummingbot.strategy.directional_strategy_base import DirectionalStrategyBase


class StatArb(DirectionalStrategyBase):
    directional_strategy_name: str = "STAT_ARB"
    # Define the trading pair and exchange that we want to use and the csv where we are going to store the entries
    trading_pair: str = "ETH-USDT"
    exchange: str = "binance_perpetual"
    order_amount_usd = Decimal("15")
    leverage = 10

    # Configure the parameters for the position
    stop_loss: float = 0.025
    take_profit: float = 0.02
    time_limit: int = 60 * 60 * 12
    trailing_stop_activation_delta = 0.01
    trailing_stop_trailing_delta = 0.005
    cooldown_after_execution = 10
    max_executors = 1

    candles = [CandlesFactory.get_candle(connector="binance_perpetual",
                                         trading_pair=trading_pair,
                                         interval="1h", max_records=150),
               CandlesFactory.get_candle(connector="binance_perpetual",
                                         trading_pair="BTC-USDT",
                                         interval="1h", max_records=150)
               ]
    periods = 24
    markets = {exchange: {trading_pair}}

    def get_signal(self):
        """
        Generates the trading signal based on the RSI indicator.
        Returns:
            int: The trading signal (-1 for sell, 0 for hold, 1 for buy).
        """
        candles_df = self.get_processed_df()
        z_score = candles_df["z_score"].iloc[-1]
        if z_score > 1.1:
            return 1
        elif z_score < -1.1:
            return -1
        else:
            return 0

    def get_processed_df(self):
        """
        Retrieves the processed dataframe with RSI values.
        Returns:
            pd.DataFrame: The processed dataframe with RSI values.
        """
        candles_df_eth = self.candles[0].candles_df
        candles_df_btc = self.candles[1].candles_df
        df = pd.merge(candles_df_eth, candles_df_btc, on="timestamp", how='inner', suffixes=('', '_target'))
        df["pct_change_original"] = df["close"].pct_change()
        df["pct_change_target"] = df["close_target"].pct_change()
        df["spread"] = df["pct_change_target"] - df["pct_change_original"]
        df["cum_spread"] = df["spread"].rolling(self.periods).sum()
        df["z_score"] = ta.zscore(df["cum_spread"], length=self.periods)
        return df

    def market_data_extra_info(self):
        """
        Provides additional information about the market data to the format status.
        Returns:
            List[str]: A list of formatted strings containing market data information.
        """
        lines = []
        columns_to_show = ["timestamp", "open", "low", "high", "close", "volume", "z_score", "cum_spread", "close_target"]
        candles_df = self.get_processed_df()
        lines.extend([f"Candles: {self.candles[0].name} | Interval: {self.candles[0].interval}\n"])
        lines.extend(self.candles_formatted_list(candles_df, columns_to_show))
        return lines
