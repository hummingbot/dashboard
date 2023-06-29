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
    trading_pair="ETH-USDT",
    interval='1h',
)


strategy = Bollinger(
        exchange="binance_perpetual",
        trading_pair="ETH-USDT",
        interval="3m",
        bb_length=66,
        bb_std=2.8,
        bb_long_threshold=0.17,
        bb_short_threshold=1.23,
    )

backtesting = Backtesting(strategy=strategy)

positions = backtesting.run_backtesting(
    start='2021-04-01',
    # end='2023-06-02',
    order_amount=50,
    leverage=20,
    initial_portfolio=100,
    take_profit_multiplier=4.3,
    stop_loss_multiplier=3.0,
    time_limit=60 * 60 * 24,
    std_span=None,
)
backtesting_analysis = BacktestingAnalysis(positions=positions, candles_df=df_to_show)
backtesting_analysis.create_base_figure(volume=False, positions=True, extra_rows=1)
backtesting_analysis.add_trade_pnl(row=2)

c1, c2 = st.columns([0.2, 0.8])
with c1:
    st.text(backtesting_analysis.text_report())
with c2:
    st.plotly_chart(backtesting_analysis.figure(), use_container_width=True)

