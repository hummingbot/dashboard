import os
import sqlite3
from datetime import datetime

import ccxt
import numpy as np

import pandas as pd
import streamlit as st

from utils.data_manipulation import BotData
from utils.graphs import CandlesGraph

st.set_page_config(
    page_title="Hummingbot Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("🚀 Strategy Performance")

intervals = {
    "1m": 60,
    "3m": 60 * 3,
    "30m": 60 * 30,
    "1h": 60 * 60,
    "6h": 60 * 60 * 6,
    "1d": 60 * 60 * 24,

}


@st.cache_resource
def get_data(db_name: str):
    path = os.path.join("data", db_name)
    conn = sqlite3.connect(path)
    order_df = pd.read_sql_query("SELECT * FROM 'Order'", conn)
    order_status_df = pd.read_sql_query("SELECT * FROM OrderStatus", conn)
    trade_fill_df = pd.read_sql_query("SELECT * FROM TradeFill", conn)
    order_df['creation_timestamp'] = pd.to_datetime(order_df['creation_timestamp'], unit="ms")
    order_df['last_update_timestamp'] = pd.to_datetime(order_df['last_update_timestamp'], unit="ms")
    trade_fill_df["timestamp"] = pd.to_datetime(trade_fill_df["timestamp"], unit="ms")
    # TODO: GitHub issue #8
    trade_fill_df["price"] = trade_fill_df["price"] / 1000000
    trade_fill_df["amount"] = trade_fill_df["amount"] / 1000000
    conn.close()
    return BotData(order_df, order_status_df, trade_fill_df)


@st.cache_data(ttl=60)
def get_ohlc(trading_pair: str, exchange: str, interval: str, start_timestamp: int, end_timestamp: int):
    exchange = eval("ccxt." + exchange + "()")
    limit = (end_timestamp - start_timestamp) / intervals[interval]
    bars = exchange.fetch_ohlcv(trading_pair, timeframe=interval, since=start_timestamp * 1000, limit=int(limit))
    df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


col11, col12 = st.columns(2)
with col11:
    db_names = [db_name for db_name in os.listdir("data") if db_name.endswith(".sqlite")]
    selected_db_name = st.selectbox("Select a database to use:", db_names)
    all_bots_data = get_data(selected_db_name)
with col12:
    selected_config_file = st.selectbox("Select a config file to analyze:",
                                        all_bots_data.trade_fill["config_file_path"].unique())
    if selected_config_file is not None:
        strategy_data = all_bots_data.get_strategy_data(
            selected_config_file)

exchange_name = strategy_data.market
trading_pair = strategy_data.symbol.replace("-", "")

c1, c2 = st.columns([1, 5])
with c1:
    interval = st.selectbox("Candles Interval:", intervals.keys(), index=3)

date_array = pd.date_range(start=strategy_data.start_time, end=strategy_data.end_time, periods=60)
ohlc_extra_time = 60
with st.spinner("Loading candles..."):
    candles_df = get_ohlc(trading_pair, exchange_name, interval, int(strategy_data.start_time.timestamp() - ohlc_extra_time),
                          int(strategy_data.end_time.timestamp() + ohlc_extra_time))
start_time, end_time = st.select_slider("Select a time range to analyze", options=date_array.tolist(), value=(date_array[0], date_array[-1]))
candles_df_filtered = candles_df[(candles_df["timestamp"] >= int(start_time.timestamp() * 1000)) & (candles_df["timestamp"] <= int(end_time.timestamp() * 1000))]
strategy_data_filtered = strategy_data.get_filtered_strategy_data(start_time, end_time)

row = st.container()
col11, col12, col13 = st.columns([1, 2, 3])
with row:
    with col11:
        st.header(f"🏦 Market")
        st.metric(label="Exchange", value=strategy_data_filtered.market.capitalize())
        st.metric(label="Trading pair", value=strategy_data_filtered.symbol)
    with col12:
        st.header("📋 General stats")
        col121, col122 = st.columns(2)
        with col121:
            st.metric(label='Start date', value=strategy_data_filtered.start_time.strftime("%Y-%m-%d %H:%M"))
            st.metric(label='End date', value=strategy_data_filtered.end_time.strftime("%Y-%m-%d %H:%M"))
            st.metric(label='Duration (Hours)', value=round(strategy_data_filtered.duration_seconds / 3600, 2))
        with col122:
            st.metric(label='Start Price', value=round(strategy_data_filtered.start_price, 4))
            st.metric(label='End Price', value=round(strategy_data_filtered.end_price, 4))
            st.metric(label='Price change', value=f"{round(strategy_data_filtered.price_change * 100, 2)} %")
    with col13:
        st.header("📈 Performance")
        col131, col132, col133 = st.columns(3)
        with col131:
            st.metric(label='Total Trades', value=strategy_data_filtered.total_orders)
            st.metric(label='Total Buy Trades', value=strategy_data_filtered.total_buy_trades)
            st.metric(label='Total Sell Trades', value=strategy_data_filtered.total_sell_trades)
        with col132:
            st.metric(label='Inventory change in Base asset', value=round(strategy_data_filtered.inventory_change_base_asset, 4))
            st.metric(label='Total Buy Trades Amount', value=strategy_data_filtered.total_buy_amount)
            st.metric(label='Total Sell Trades Amount', value=strategy_data_filtered.total_sell_amount)
        with col133:
            st.metric(label='Trade PNL USD', value=round(strategy_data_filtered.trade_pnl_usd, 2))
            st.metric(label='Average Buy Price', value=round(strategy_data_filtered.average_buy_price, 4))
            st.metric(label='Average Sell Price', value=round(strategy_data_filtered.average_sell_price, 4))

cg = CandlesGraph(candles_df_filtered, show_volume=True, extra_rows=2)
cg.add_buy_trades(strategy_data_filtered.buys)
cg.add_sell_trades(strategy_data_filtered.sells)
cg.add_base_inventory_change(strategy_data_filtered)
cg.add_trade_pnl(strategy_data_filtered)
fig = cg.figure()
st.plotly_chart(fig, use_container_width=True)

st.subheader("💵Trades")
st.write(strategy_data_filtered.trade_fill)

st.subheader("📩 Orders")
st.write(strategy_data_filtered.orders)

st.subheader("⌕ Order Status")
st.write(strategy_data_filtered.order_status)