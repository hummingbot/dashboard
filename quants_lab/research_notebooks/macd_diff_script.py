import pandas_ta as ta
import pandas as pd
import numpy as np

from quants_lab.utils import data_management
from quants_lab.backtesting.backtesting import Backtesting
from quants_lab.backtesting.backtesting_analysis import BacktestingAnalysis

df = pd.read_csv('quants_lab/research_notebooks/candles_DOGE-BUSD_5m.csv') #.tail(2016)


def macd_diff_custom(candles_df):
    delta_macd_thold = 0.0006
    macdh_thold = 0.0
    target_thold = 0.0045
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    candles_df['timestamp'] = pd.to_datetime(candles_df['timestamp'], unit='ms')
    candles_df.ta.macd(fast=macd_fast, slow=macd_slow, signal=macd_signal, append=True)

    macdh = f'MACDh_{macd_fast}_{macd_slow}_{macd_signal}'
    macdh_norm = f'MACDh_{macd_fast}_{macd_slow}_{macd_signal}_norm'
    candles_df[macdh_norm] = candles_df[macdh] / candles_df['close']

    candles_df['diff'] = candles_df[macdh_norm].diff()
    candles_df['start'] = np.sign(candles_df['diff']) != np.sign(candles_df['diff'].shift())
    candles_df['id'] = candles_df['start'].cumsum()
    candles_df['macd_cum_diff'] = candles_df.groupby('id')['diff'].cumsum()

    candles_df['target'] = candles_df['close'].rolling(100).std() / candles_df['close']

    macd_long_cond = (candles_df['macd_cum_diff'] > delta_macd_thold) & (candles_df[macdh_norm] > macdh_thold) & (candles_df['target'] > target_thold)
    macd_short_cond = (candles_df['macd_cum_diff'] < - delta_macd_thold) & (candles_df[macdh_norm] < - macdh_thold) & (candles_df['target'] > target_thold)

    candles_df['side'] = 0
    candles_df.loc[macd_long_cond, 'side'] = 1
    candles_df.loc[macd_short_cond, 'side'] = -1
    return candles_df


backtesting = Backtesting(candles_df=df)

positions = backtesting.run_backtesting(
    strategy=macd_diff_custom,
    order_amount=20,
    leverage=20,
    initial_portfolio=148,
    take_profit_multiplier=0.3,
    stop_loss_multiplier=0.3,
    time_limit=60 * 55 * 1,
    std_span=None,
)
backtesting_report = BacktestingAnalysis(df, positions, extra_rows=1, show_volume=False)

print(backtesting_report.text_report())

# Set the backend to Plotly
pd.options.plotting.backend = "plotly"

# positions["ret_usd"].cumsum().plot()
