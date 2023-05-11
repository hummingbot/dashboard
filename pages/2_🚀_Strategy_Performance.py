import os
import sqlite3

import ccxt

import pandas as pd
import streamlit as st

from utils.database_manager import DatabaseManager
from utils.graphs import CandlesGraph

st.set_page_config(
    page_title="Hummingbot Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("🚀 Strategy Performance")

intervals = {
    # "1m": 60,
    "3m": 60 * 3,
    "30m": 60 * 30,
    "1h": 60 * 60,
    "6h": 60 * 60 * 6,
    "1d": 60 * 60 * 24,
}

@st.cache_resource
def get_database(db_name: str):
    db_manager = DatabaseManager(db_name)
    return db_manager


@st.cache_data(ttl=60)
def get_ohlc(trading_pair: str, exchange: str, interval: str, start_timestamp: int, end_timestamp: int):
    # TODO: Remove hardcoded exchange by using the new data collected by the bot.
    connector = getattr(ccxt, "binance")()
    limit = max(int((end_timestamp - start_timestamp) / intervals[interval]), 10)
    bars = connector.fetch_ohlcv(trading_pair.replace("-", ""), timeframe=interval, since=start_timestamp * 1000, limit=limit)
    df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


with st.container():
    col1, col2 = st.columns(2)
    with col1:
        db_names = [db_name for db_name in os.listdir("data") if db_name.endswith(".sqlite")]
        selected_db_name = st.selectbox("Select a database to use:",
                                        db_names if len(db_names) > 0 else ["No databases found"])
    if selected_db_name == "No databases found":
        st.warning("No databases available to analyze. Please run a backtesting first.")
    else:
        db_manager = get_database(selected_db_name)
        with col2:
            selected_config_file = st.selectbox("Select a config file to analyze:", db_manager.get_config_files())
            if selected_config_file is not None:
                exchanges_trading_pairs = db_manager.get_exchanges_trading_pairs_by_config_file(selected_config_file)
                strategy_data = db_manager.get_strategy_data(selected_config_file)

        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_exchange = st.selectbox("Select an exchange:", list(exchanges_trading_pairs.keys()))
            with col2:
                selected_trading_pair = st.selectbox("Select a trading pair:", exchanges_trading_pairs[selected_exchange])
            with col3:
                interval = st.selectbox("Candles Interval:", intervals.keys(), index=0)

        if selected_exchange and selected_trading_pair:
            single_market_strategy_data = strategy_data.get_single_market_strategy_data(selected_exchange, selected_trading_pair)
            date_array = pd.date_range(start=strategy_data.start_time, end=strategy_data.end_time, periods=60)
            ohlc_extra_time = 60
            with st.spinner("Loading candles..."):
                candles_df = get_ohlc(single_market_strategy_data.trading_pair, single_market_strategy_data.exchange, interval,
                                      int(strategy_data.start_time.timestamp() - ohlc_extra_time),
                                      int(strategy_data.end_time.timestamp() + ohlc_extra_time))
            start_time, end_time = st.select_slider("Select a time range to analyze", options=date_array.tolist(),
                                                    value=(date_array[0], date_array[-1]))
            candles_df_filtered = candles_df[(candles_df["timestamp"] >= int(start_time.timestamp() * 1000)) & (
                        candles_df["timestamp"] <= int(end_time.timestamp() * 1000))]
            strategy_data_filtered = single_market_strategy_data.get_filtered_strategy_data(start_time, end_time)

            row = st.container()
            col11, col12, col13 = st.columns([1, 2, 3])
            with row:
                with col11:
                    st.header(f"🏦 Market")
                    st.metric(label="Exchange", value=strategy_data_filtered.exchange.capitalize())
                    st.metric(label="Trading pair", value=strategy_data_filtered.trading_pair.upper())
                with col12:
                    st.header("📋 General stats")
                    col121, col122 = st.columns(2)
                    with col121:
                        st.metric(label='Duration (Hours)', value=round(strategy_data_filtered.duration_seconds / 3600, 2))
                        st.metric(label='Start date', value=strategy_data_filtered.start_time.strftime("%Y-%m-%d %H:%M"))
                        st.metric(label='End date', value=strategy_data_filtered.end_time.strftime("%Y-%m-%d %H:%M"))
                    with col122:
                        st.metric(label='Price change', value=f"{round(strategy_data_filtered.price_change * 100, 2)} %")
                with col13:
                    st.header("📈 Performance")
                    col131, col132, col133, col134 = st.columns(4)
                    with col131:
                        st.metric(label=f'Net PNL {strategy_data_filtered.quote_asset}', value=round(strategy_data_filtered.net_pnl_quote, 2))
                        st.metric(label=f'Trade PNL {strategy_data_filtered.quote_asset}', value=round(strategy_data_filtered.trade_pnl_quote, 2))
                        st.metric(label=f'Fees {strategy_data_filtered.quote_asset}', value=round(strategy_data_filtered.cum_fees_in_quote, 2))
                    with col132:
                        st.metric(label='Total Trades', value=strategy_data_filtered.total_orders)
                        st.metric(label='Total Buy Trades', value=strategy_data_filtered.total_buy_trades)
                        st.metric(label='Total Sell Trades', value=strategy_data_filtered.total_sell_trades)
                    with col133:
                        st.metric(label='Inventory change in Base asset',
                                  value=round(strategy_data_filtered.inventory_change_base_asset, 4))
                        st.metric(label='Total Buy Trades Amount', value=round(strategy_data_filtered.total_buy_amount, 2))
                        st.metric(label='Total Sell Trades Amount', value=round(strategy_data_filtered.total_sell_amount, 2))
                    with col134:
                        st.metric(label='End Price', value=round(strategy_data_filtered.end_price, 4))
                        st.metric(label='Average Buy Price', value=round(strategy_data_filtered.average_buy_price, 4))
                        st.metric(label='Average Sell Price', value=round(strategy_data_filtered.average_sell_price, 4))

            cg = CandlesGraph(candles_df_filtered, show_volume=True, extra_rows=4)
            cg.add_buy_trades(strategy_data_filtered.buys)
            cg.add_sell_trades(strategy_data_filtered.sells)
            cg.add_base_inventory_change(strategy_data_filtered)
            cg.add_net_pnl(strategy_data_filtered)
            cg.add_trade_pnl(strategy_data_filtered)
            cg.add_trade_fee(strategy_data_filtered)
            fig = cg.figure()
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("💵Trades")
            st.write(strategy_data_filtered.trade_fill)

            st.subheader("📩 Orders")
            st.write(strategy_data_filtered.orders)

            st.subheader("⌕ Order Status")
            st.write(strategy_data_filtered.order_status)
