import pandas as pd
import pandas_ta as ta
import streamlit as st

from quants_lab.strategy.mean_reversion.bollinger import Bollinger
from quants_lab.utils import data_management
from quants_lab.backtesting.backtesting import Backtesting
from quants_lab.backtesting.backtesting_analysis import BacktestingAnalysis

st.set_page_config(
    page_title="Hummingbot Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("⚙️ Backtesting")

df_to_show = data_management.get_dataframe(
    exchange='binance_perpetual',
    trading_pair='IOTA-USDT',
    interval='1h',
)

strategy = Bollinger(
    exchange="binance_perpetual",
    trading_pair="ETH-USDT",
    interval="1h",
    bb_length=24,
    bb_std=2.0,
)

backtesting = Backtesting(strategy=strategy)


backtesting_result = backtesting.run_backtesting(
    order_amount=50,
    leverage=20,
    initial_portfolio=100,
    take_profit_multiplier=3.5,
    stop_loss_multiplier=1.5,
    time_limit=60 * 60 * 12,
    std_span=None,
)


backtesting_analysis = BacktestingAnalysis(df_to_show, backtesting_result, extra_rows=1, show_volume=False)
backtesting_analysis.add_trade_pnl(row=2)
# backtesting_analysis.add_positions()

c1, c2 = st.columns([0.2, 0.8])
with c1:
    st.text(backtesting_analysis.text_report())
with c2:
    st.plotly_chart(backtesting_analysis.figure(), use_container_width=True)

