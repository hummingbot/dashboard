import pandas as pd
import pandas_ta as ta
import streamlit as st

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


df = data_management.get_dataframe(
    exchange='binance_perpetual',
    trading_pair='BTC-USDT',
    interval='1m',
)

df_to_show = data_management.get_dataframe(
    exchange='binance_perpetual',
    trading_pair='BTC-USDT',
    interval='1h',
)

def bbands_strategy(df):
    df.ta.bbands(length=100, std=3, append=True)
    df["side"] = 0
    long_condition = df["BBP_100_3.0"] < -0.2
    short_condition = df["BBP_100_3.0"] > 1.2
    df.loc[long_condition, "side"] = 1
    df.loc[short_condition, "side"] = -1
    return df

backtesting = Backtesting(candles_df=df)

backtesting_result = backtesting.run_backtesting(
    strategy=bbands_strategy,
    order_amount=50,
    leverage=20,
    initial_portfolio=100,
    take_profit_multiplier=1.5,
    stop_loss_multiplier=0.8,
    time_limit=60 * 60 * 24,
    std_span=None,
)


backtesting_analysis = BacktestingAnalysis(df_to_show, backtesting_result, extra_rows=1, show_volume=False)
backtesting_analysis.add_trade_pnl(row=2)

c1, c2 = st.columns([0.2, 0.8])
with c1:
    st.text(backtesting_analysis.text_report())
with c2:
    st.plotly_chart(backtesting_analysis.figure(), use_container_width=True)

