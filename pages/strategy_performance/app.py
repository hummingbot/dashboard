import os
import pandas as pd
import streamlit as st
import math
from utils.os_utils import get_databases
from utils.database_manager import DatabaseManager
from utils.graphs import CandlesGraph, PerformanceGraphs
from utils.st_utils import initialize_st_page, download_csv_button, style_metric_cards


def db_error_message(db: DatabaseManager, error_message: str):
    container = st.container()
    with container:
        st.warning(error_message)
        with st.expander("DB Status"):
            status_df = pd.DataFrame([db.status]).transpose().reset_index()
            status_df.columns = ["Attribute", "Value"]
            st.table(status_df)
    return container


def candles_graph(candles: pd.DataFrame, strat_data, show_volume=False, extra_rows=2):
    cg = CandlesGraph(candles, show_volume=show_volume, extra_rows=extra_rows)
    cg.add_buy_trades(strat_data.buys)
    cg.add_sell_trades(strat_data.sells)
    cg.add_pnl(strat_data, row=2)
    cg.add_quote_inventory_change(strat_data, row=3)
    return cg.figure()


initialize_st_page(title="Strategy Performance", icon="🚀")
style_metric_cards()

UPLOAD_FOLDER = "data"

# Start content here
intervals = {
    "1m": 60,
    "3m": 60 * 3,
    "5m": 60 * 5,
    "15m": 60 * 15,
    "30m": 60 * 30,
    "1h": 60 * 60,
    "6h": 60 * 60 * 6,
    "1d": 60 * 60 * 24,
}


st.subheader("🔫 Data source")

# Upload database
with st.expander("⬆️ Upload"):
    uploaded_db = st.file_uploader("Select a Hummingbot SQLite Database", type=["sqlite", "db"])
    if uploaded_db is not None:
        file_contents = uploaded_db.read()
        with open(os.path.join(UPLOAD_FOLDER, uploaded_db.name), "wb") as f:
            f.write(file_contents)
        st.success("File uploaded and saved successfully!")
        selected_db = DatabaseManager(uploaded_db.name)

# Find and select existing databases
dbs = get_databases()
if dbs is not None:
    bot_source = st.selectbox("Choose your database source:", dbs.keys())
    db_names = [x for x in dbs[bot_source]]
    selected_db_name = st.selectbox("Select a database to start:", db_names)
    selected_db = DatabaseManager(db_name=dbs[bot_source][selected_db_name])
else:
    st.warning("Ups! No databases were founded. Start uploading one")
    selected_db = None
    st.stop()

# Load strategy data
strategy_data = selected_db.get_strategy_data()
main_performance_charts = PerformanceGraphs(strategy_data)

# Strategy summary section
st.divider()
st.subheader("📝 Strategy summary")
if not main_performance_charts.has_summary_table:
    db_error_message(db=selected_db,
                     error_message="Inaccesible summary table. Please try uploading a new database.")
    st.stop()
else:
    table_tab, chart_tab = st.tabs(["Table", "Chart"])
    with chart_tab:
        st.plotly_chart(main_performance_charts.summary_chart(), use_container_width=True)
    with table_tab:
        selection = main_performance_charts.strategy_summary_table()
        if selection is None:
            st.info("💡 Choose a trading pair and start analyzing!")
            st.stop()
        elif len(selection) > 1:
            st.warning("This version doesn't support multiple selections. Please try selecting only one.")
            st.stop()
        else:
            selected_exchange = selection["Exchange"].values[0]
            selected_trading_pair = selection["Trading Pair"].values[0]


# Explore Trading Pair section
st.divider()
st.subheader("🔍 Explore Trading Pair")

if any("Error" in status for status in [selected_db.status["trade_fill"], selected_db.status["orders"]]):
    db_error_message(db=selected_db,
                     error_message="Database error. Check the status of your database.")
    st.stop()

# Filter strategy data by time
date_array = pd.date_range(start=strategy_data.start_time, end=strategy_data.end_time, periods=60)
start_time, end_time = st.select_slider("Select a time range to analyze",
                                        options=date_array.tolist(),
                                        value=(date_array[0], date_array[-1]))
single_market_strategy_data = strategy_data.get_single_market_strategy_data(selected_exchange, selected_trading_pair)
time_filtered_strategy_data = single_market_strategy_data.get_filtered_strategy_data(start_time, end_time)
time_filtered_performance_charts = PerformanceGraphs(time_filtered_strategy_data)

# Header metrics
col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
with col1:
    st.metric(label=f'Net PNL {time_filtered_strategy_data.quote_asset}',
              value=round(time_filtered_strategy_data.net_pnl_quote, 2))
with col2:
    st.metric(label='Total Trades', value=time_filtered_strategy_data.total_orders)
with col3:
    st.metric(label='Accuracy',
              value=f"{100 * time_filtered_strategy_data.accuracy:.2f} %")
with col4:
    st.metric(label="Profit Factor",
              value=round(time_filtered_strategy_data.profit_factor, 2))
with col5:
    st.metric(label='Duration (Days)',
              value=round(time_filtered_strategy_data.duration_seconds / (60 * 60 * 24), 2))
with col6:
    st.metric(label='Price change',
              value=f"{round(time_filtered_strategy_data.price_change * 100, 2)} %")
with col7:
    buy_trades_amount = round(time_filtered_strategy_data.total_buy_amount, 2)
    avg_buy_price = round(time_filtered_strategy_data.average_buy_price, 4)
    st.metric(label="Total Buy Volume",
              value=round(buy_trades_amount * avg_buy_price, 2))
with col8:
    sell_trades_amount = round(time_filtered_strategy_data.total_sell_amount, 2)
    avg_sell_price = round(time_filtered_strategy_data.average_sell_price, 4)
    st.metric(label="Total Sell Volume",
              value=round(sell_trades_amount * avg_sell_price, 2))

# Cummulative pnl chart
st.plotly_chart(time_filtered_performance_charts.pnl_over_time(), use_container_width=True)

# Market activity section
st.subheader("💱 Market activity")
if "Error" in selected_db.status["market_data"] or time_filtered_strategy_data.market_data.empty:
    st.warning("Market data is not available so the candles graph is not going to be rendered."
               "Make sure that you are using the latest version of Hummingbot and market data recorder activated.")
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        interval = st.selectbox("Candles Interval:", intervals.keys(), index=2)
    with col2:
        rows_per_page = st.number_input("Candles per Page", value=1500, min_value=1, max_value=5000)
    with col3:
        st.markdown("##")
        show_panel_metrics = st.checkbox("Show panel metrics", value=True)
    with col4:
        total_rows = len(time_filtered_strategy_data.get_market_data_resampled(interval=f"{intervals[interval]}S"))
        total_pages = math.ceil(total_rows / rows_per_page)
        if total_pages > 1:
            selected_page = st.select_slider("Select page", list(range(total_pages)), total_pages - 1,
                                             key="page_slider")
        else:
            selected_page = 0
        start_idx = selected_page * rows_per_page
        end_idx = start_idx + rows_per_page
        candles_df = time_filtered_strategy_data.get_market_data_resampled(interval=f"{intervals[interval]}S").iloc[start_idx:end_idx]
        start_time_page = candles_df.index.min()
        end_time_page = candles_df.index.max()

    # Filter strategy data by page
    page_filtered_strategy_data = single_market_strategy_data.get_filtered_strategy_data(start_time_page, end_time_page)
    page_performance_charts = PerformanceGraphs(page_filtered_strategy_data)

    # Panel Metrics
    if show_panel_metrics:
        col1, col2 = st.columns([2, 1])
        with col1:
            candles_chart = candles_graph(candles_df, page_filtered_strategy_data)
            st.plotly_chart(candles_chart, use_container_width=True)
        with col2:
            chart_tab, table_tab = st.tabs(["Chart", "Table"])
            with chart_tab:
                st.plotly_chart(page_performance_charts.intraday_performance(), use_container_width=True)
                st.plotly_chart(page_performance_charts.returns_histogram(), use_container_width=True)
            with table_tab:
                st.dataframe(page_filtered_strategy_data.trade_fill[["timestamp", "gross_pnl", "trade_fee", "realized_pnl"]].dropna(subset="realized_pnl"),
                             use_container_width=True,
                             hide_index=True,
                             height=(min(len(page_filtered_strategy_data.trade_fill) * 39, candles_chart.layout.height - 180)))
    else:
        st.plotly_chart(candles_graph(candles_df, page_filtered_strategy_data), use_container_width=True)

# Position executor section
st.divider()
st.subheader("🤖 Position executor")
if "Error" in selected_db.status["position_executor"] or strategy_data.position_executor.empty:
    st.warning("Position executor data is not available so position executor graphs are not going to be rendered."
               "Make sure that you are using the latest version of Hummingbot.")
else:
    st.dataframe(strategy_data.position_executor, use_container_width=True)

# Community metrics section
st.divider()
st.subheader("👥 Community Metrics")
with st.container():
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label=f'Trade PNL {time_filtered_strategy_data.quote_asset}',
                  value=round(time_filtered_strategy_data.trade_pnl_quote, 2))
        st.metric(label=f'Fees {time_filtered_strategy_data.quote_asset}',
                  value=round(time_filtered_strategy_data.cum_fees_in_quote, 2))
    with col2:
        st.metric(label='Total Buy Trades', value=time_filtered_strategy_data.total_buy_trades)
        st.metric(label='Total Sell Trades', value=time_filtered_strategy_data.total_sell_trades)
    with col3:
        st.metric(label='Total Buy Trades Amount',
                  value=round(time_filtered_strategy_data.total_buy_amount, 2))
        st.metric(label='Total Sell Trades Amount',
                  value=round(time_filtered_strategy_data.total_sell_amount, 2))
    with col4:
        st.metric(label='Average Buy Price', value=round(time_filtered_strategy_data.average_buy_price, 4))
        st.metric(label='Average Sell Price', value=round(time_filtered_strategy_data.average_sell_price, 4))
    with col5:
        st.metric(label='Inventory change in Base asset',
                  value=round(time_filtered_strategy_data.inventory_change_base_asset, 4))

# Tables section
st.divider()
st.subheader("Tables")
with st.expander("💵 Trades"):
    st.write(strategy_data.trade_fill)
    download_csv_button(strategy_data.trade_fill, "trade_fill", "download-trades")
with st.expander("📩 Orders"):
    st.write(strategy_data.orders)
    download_csv_button(strategy_data.orders, "orders", "download-orders")
with st.expander("⌕ Order Status"):
    st.write(strategy_data.order_status)
    download_csv_button(strategy_data.order_status, "order_status", "download-order-status")
if not strategy_data.market_data.empty:
    with st.expander("💱 Market Data"):
        st.write(strategy_data.market_data)
        download_csv_button(strategy_data.market_data, "market_data", "download-market-data")
