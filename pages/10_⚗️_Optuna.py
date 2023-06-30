import pandas_ta as ta # noqa
import streamlit as st
import optuna
import optuna.visualization as viz
import sklearn
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
    strategy.optimize('macd_cum_diff', strategy.objective, n_trials=100)

# Generate global table from .db file
dataframes = data_management.load_optuna_tables()
trial_user_attrs = dataframes['trial_user_attributes'].pivot_table(values='value_json', index='trial_id', columns='key').reset_index()
trial_params = dataframes['trial_params'].pivot_table(values='param_value', index='trial_id', columns='param_name').reset_index()
trial_values = dataframes['trial_values'].rename(columns={'value': 'net_profit_pct'})
df = dataframes['trials'].merge(dataframes['studies'], on='study_id').merge(trial_user_attrs, on='trial_id').merge(trial_params, on='trial_id').merge(trial_values[['trial_id', 'net_profit_pct']], on='trial_id')
st.dataframe(df)

# Load study from database via load_study
study = optuna.study.load_study('macd_cum_diff', storage='sqlite:///backtesting_report.db')
col1, col2 = st.columns(2)
# with col1:
st.plotly_chart(viz.plot_edf(study))
st.plotly_chart(viz.plot_intermediate_values(study))
st.plotly_chart(viz.plot_optimization_history(study))
st.plotly_chart(viz.plot_parallel_coordinate(study))
# with col2:
st.plotly_chart(viz.plot_rank(study))
st.plotly_chart(viz.plot_slice(study))
st.plotly_chart(viz.plot_timeline(study))
# TODO: Fix plot_terminator_improvement.
# No module named 'botorch'.
# st.plotly_chart(viz.plot_terminator_improvement(study))
# TODO: Fix plot_pareto_front
# ValueError: `plot_pareto_front` function only supports 2 or 3 objective studies when using `targets` is `None`.
# Please use `targets` if your objective studies have more than 3 objectives.
# st.plotly_chart(viz.plot_pareto_front(study))
# TODO: No module named 'scikit-learn'
# st.plotly_chart(viz.plot_param_importances(study))
