import pandas_ta as ta # noqa
import streamlit as st

from quants_lab.strategy.trend_follower.macd_cum_diff import MACDCumDiff
from quants_lab.utils import data_management

st.set_page_config(
    page_title="Hummingbot Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("⚙️ Backtesting")

candles_df = data_management.get_dataframe(
    exchange='binance_perpetual',
    trading_pair="ETH-USDT",
    interval='5m',
)


strategy = MACDCumDiff(
        exchange="binance_perpetual",
        trading_pair="ETH-USDT",
        interval="5m",
        delta_macd_thold=0.0006,
        macdh_thold=0.0,
        target_thold=0.0045,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
    )

run_backtesting = st.sidebar.button('Run optuna!')
if run_backtesting:
    strategy.optimize('macd_cum_diff', strategy.objective, n_trials=500)

dataframes = data_management.load_optuna_tables()

trial_user_attrs = dataframes['trial_user_attributes'].pivot_table(values='value_json', index='trial_id', columns='key').reset_index()
trial_params = dataframes['trial_params'].pivot_table(values='param_value', index='trial_id', columns='param_name').reset_index()
trial_values = dataframes['trial_values'].rename(columns={'value': 'net_profit_pct'})
df = dataframes['trials'].merge(dataframes['studies'], on='study_id').merge(trial_user_attrs, on='trial_id').merge(trial_params, on='trial_id').merge(trial_values[['trial_id', 'net_profit_pct']], on='trial_id')
st.dataframe(df)

