def directional_strategy_template(strategy_name: str,
                                  exchange: str,
                                  trading_pair: str,
                                  interval: str) -> str:
    return f"""import pandas_ta as ta
import pandas as pd
import numpy as np

from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase
from quants_lab.utils import data_management



class {strategy_name}(DirectionalStrategyBase):
    # Define the attributes of the strategy
    def __init__(self,
                 exchange="{exchange}",
                 trading_pair="{trading_pair}",
                 interval="{interval}"):
        self.exchange = exchange
        self.trading_pair = trading_pair
        self.interval = interval

    def get_raw_data(self):
        # The method get candles will search for the data in the folder data/candles
        # If the data is not there, you can use the candles downloader to get the data
        df = self.get_candles(
            exchange=self.exchange,
            trading_pair=self.trading_pair,
            interval=self.interval,
        )
        return df

    def add_indicators(self, df):
        df.ta.sma(length=20, append=True)
        # ... Add more indicators here
        # ... Check https://github.com/twopirllc/pandas-ta#indicators-by-category for more indicators
        # ... Use help(ta.indicator_name) to get more info
        return df

    def add_signals(self, df):
        # ... Do your own logic
        random_series = pd.Series(np.random.randint(low=0, high=101, size=100))
        random_series_2 = pd.Series(np.random.randint(low=0, high=101, size=100))
        random_thold = np.random.randint(low=45, high=65)
        random_thold_2 = np.random.randint(low=45, high=65)

        # Generate long and short conditions
        macd_long_cond = (random_series > random_thold) & (random_series_2 > random_thold_2)
        macd_short_cond = (random_series < random_thold) & (random_series_2 > random_thold_2)

        # Choose side
        df['side'] = 0
        df.loc[macd_long_cond, 'side'] = 1
        df.loc[macd_short_cond, 'side'] = -1
        return df
"""