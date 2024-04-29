import math
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv
import logging
from psycopg2 import OperationalError
import os

from data_viz.candles import PerformanceCandles
from data_viz.charts import ChartsBase
from utils.st_utils import initialize_st_page, download_csv_button
from utils.etl_performance import ETLPerformance
from data_viz.tracers import PerformancePlotlyTracer

load_dotenv()


def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{int(days)}d {int(hours)}h {int(minutes)}m"


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


def custom_sort(row):
    if row['type'] == 'buy':
        return 0, -row['number']
    else:
        return 1, row['number']


initialize_st_page(title="DCA Performance", icon="🚀")
st.subheader("🔫 Data source")

try:
    etl = ETLPerformance(host="dashboard-db-1",
                         port=5432,
                         database=os.environ.get("POSTGRES_DB"),
                         user=os.environ.get("POSTGRES_USER"),
                         password=os.environ.get("POSTGRES_PASSWORD"))
    etl.test_connection()
except Exception as e:
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        host = st.text_input("Host", "localhost")
    with col2:
        port = st.number_input("Port", value=5480, step=1)
    with col3:
        db_name = st.text_input("DB Name", os.environ.get("POSTGRES_DB"))
    with col4:
        db_user = st.text_input("DB User", os.environ.get("POSTGRES_USER"))
    with col5:
        db_password = st.text_input("DB Password", os.environ.get("POSTGRES_PASSWORD"), type="password")
    try:
        etl = ETLPerformance(host=host, port=port, database=db_name, user=db_user, password=db_password)
        st.success("Connected to PostgreSQL database successfully!")
    except OperationalError as e:
        # Log the error message to Streamlit interface
        st.error(f"Error connecting to PostgreSQL database: {e}")
        # Log the error to the console or log file
        logging.error(f"Error connecting to PostgreSQL database: {e}")
        st.stop()

executors = etl.read_executors()
market_data = etl.read_market_data()
charts = ChartsBase()
tracer = PerformancePlotlyTracer()

st.subheader("📊 Overview")
grouped_executors = executors.groupby(["instance", "controller_id", "exchange", "trading_pair", "db_name"]).agg(
    {"net_pnl_quote": "sum",
     "id": "count",
     "datetime": "min",
     "close_datetime": "max"}).reset_index()

# Apply the function to the duration column
grouped_executors["duration"] = (grouped_executors["close_datetime"] - grouped_executors["datetime"]).dt.total_seconds().apply(format_duration)
grouped_executors.rename(columns={"datetime": "start_datetime_utc",
                                  "close_datetime": "end_datetime_utc",
                                  "id": "total_executors"}, inplace=True)
st.dataframe(grouped_executors, use_container_width=True, hide_index=True)

st.subheader("🔍 Filters")
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
with col1:
    db_name = st.multiselect("Select db", executors["db_name"].unique())
with col2:
    instance_name = st.multiselect("Select instance", executors["instance"].unique())
with col3:
    controller_id = st.multiselect("Select controller", executors["controller_id"].unique())
with col4:
    exchange = st.multiselect("Select exchange", executors["exchange"].unique())
with col5:
    trading_pair = st.multiselect("Select trading_pair", executors["trading_pair"].unique())
with col6:
    start_datetime = st.date_input("Start date", value=executors["datetime"].min())
with col7:
    end_datetime = st.date_input("End date", value=executors["datetime"].max())

st.subheader("Performance Analysis")

filtered_executors_data = executors.copy()
if db_name:
    filtered_executors_data = filtered_executors_data[filtered_executors_data["db_name"].isin(db_name)]
if instance_name:
    filtered_executors_data = filtered_executors_data[filtered_executors_data["instance"].isin(instance_name)]
if controller_id:
    filtered_executors_data = filtered_executors_data[filtered_executors_data["controller_id"].isin(controller_id)]
if exchange:
    filtered_executors_data = filtered_executors_data[filtered_executors_data["exchange"].isin(exchange)]
if trading_pair:
    filtered_executors_data = filtered_executors_data[filtered_executors_data["trading_pair"].isin(trading_pair)]

# Apply datetime filters if start_datetime and end_datetime are not None
# if start_datetime:
#     filtered_executors_data = filtered_executors_data[filtered_executors_data["datetime"] >= pd.to_datetime(start_datetime)]
# if end_datetime:
#     filtered_executors_data = filtered_executors_data[filtered_executors_data["close_datetime"] <= pd.to_datetime(end_datetime)]

col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
with col1:
    st.metric("Composed PnL", f"$ {filtered_executors_data['net_pnl_quote'].sum():.2f}")
    st.metric("Profit per Executor", f"$ {filtered_executors_data['net_pnl_quote'].sum() / len(filtered_executors_data):.2f}")
with col2:
    st.metric("Total Executors", f"{len(filtered_executors_data)}")
    st.metric("Total Volume", f"{filtered_executors_data['filled_amount_quote'].sum():.2f}")
with col3:
    st.metric("# Trailing Stop", f"{len(filtered_executors_data[filtered_executors_data['close_type'] == 'TRAILING_STOP'])}",
              delta=f"{filtered_executors_data[filtered_executors_data['close_type'] == 'TRAILING_STOP']['net_pnl_quote'].sum():.2f}")
with col4:
    st.metric("# Take Profit", f"{len(filtered_executors_data[filtered_executors_data['close_type'] == 'TAKE_PROFIT'])}",
              delta=f"{filtered_executors_data[filtered_executors_data['close_type'] == 'TAKE_PROFIT']['net_pnl_quote'].sum():.2f}")
with col5:
    st.metric("# Stop Loss", f"{len(filtered_executors_data[filtered_executors_data['close_type'] == 'STOP_LOSS'])}",
              delta=f"{filtered_executors_data[filtered_executors_data['close_type'] == 'STOP_LOSS']['net_pnl_quote'].sum():.2f}")
with col6:
    st.metric("# Early Stop", f"{len(filtered_executors_data[filtered_executors_data['close_type'] == 'EARLY_STOP'])}",
              delta=f"{filtered_executors_data[filtered_executors_data['close_type'] == 'EARLY_STOP']['net_pnl_quote'].sum():.2f}")
with col7:
    st.metric("Long %", f"{100 * len(filtered_executors_data[filtered_executors_data['side'] == 1]) / len(filtered_executors_data):.2f} %",
              delta=f"{filtered_executors_data[filtered_executors_data['side'] == 1]['net_pnl_quote'].sum():.2f}")
with col8:
    st.metric("Short %", f"{100 * len(filtered_executors_data[filtered_executors_data['side'] == 2]) / len(filtered_executors_data):.2f} %",
              delta=f"{filtered_executors_data[filtered_executors_data['side'] == 2]['net_pnl_quote'].sum():.2f}")

# PnL Over Time
realized_pnl_data = filtered_executors_data[["close_datetime", "net_pnl_quote"]].sort_values("close_datetime")
realized_pnl_data["cum_pnl_over_time"] = realized_pnl_data["net_pnl_quote"].cumsum()
st.plotly_chart(charts.realized_pnl_over_time(data=realized_pnl_data,
                                              cum_realized_pnl_column="cum_pnl_over_time"),
                use_container_width=True)

# Close Types
col1, col2 = st.columns(2)
with col1:
    close_type_data = filtered_executors_data.groupby("close_type").agg({"id": "count"}).reset_index()
    st.plotly_chart(charts.close_types_pie_chart(data=close_type_data,
                                                 close_type_column="close_type",
                                                 values_column="id"), use_container_width=True)

# Level IDs
with col2:
    level_id_data = filtered_executors_data.groupby("level_id").agg({"id": "count"}).reset_index()
    st.plotly_chart(charts.level_id_pie_chart(level_id_data,
                                              level_id_column="level_id",
                                              values_column="id"),
                    use_container_width=True)

# Apply custom sorting function to create a new column 'sorting_order'
level_id_data[['type', 'number']] = level_id_data['level_id'].str.split('_', expand=True)
level_id_data["number"] = level_id_data["number"].astype(int)
level_id_data['sorting_order'] = level_id_data.apply(custom_sort, axis=1)
level_id_data = level_id_data.sort_values(by='sorting_order')
level_id_data.drop(columns=['type', 'number', 'sorting_order'], inplace=True)
st.plotly_chart(charts.level_id_histogram(level_id_data,
                                          level_id_column="level_id",
                                          values_column="id"),
                use_container_width=True)

# Market data
st.subheader("Market Data")
col1, col2, col3, col4 = st.columns(4)
with col1:
    trading_pair = st.selectbox("Select trading pair", market_data["trading_pair"].unique())
with col2:
    interval = st.selectbox("Select interval", list(intervals.keys()), index=3)
with col3:
    rows_per_page = st.number_input("Candles per Page", value=400, min_value=1, max_value=5000)
filtered_market_data = market_data[market_data["trading_pair"] == trading_pair]
filtered_market_data.set_index("timestamp", inplace=True)
market_data_resampled = filtered_market_data.resample(f"{intervals[interval]}S").agg({
    "mid_price": "ohlc",
    "best_bid": "last",
    "best_ask": "last",
})
market_data_resampled.columns = market_data_resampled.columns.droplevel(0)

# Add pagination
total_rows = len(market_data_resampled)
total_pages = math.ceil(total_rows / rows_per_page)
if total_pages > 1:
    selected_page = st.select_slider("Select page", list(range(total_pages)), total_pages - 1, key="page_slider")
else:
    selected_page = 0
start_idx = selected_page * rows_per_page
end_idx = start_idx + rows_per_page
candles_df = market_data_resampled[start_idx:end_idx]
start_time_page = candles_df.index.min()
end_time_page = candles_df.index.max()
filtered_executors_data.sort_values("close_datetime", inplace=True)
filtered_executors_data["cum_net_pnl_quote"] = filtered_executors_data["net_pnl_quote"].cumsum()
filtered_executors_data["cum_filled_amount_quote"] = filtered_executors_data["filled_amount_quote"].cumsum()
page_filtered_executors_data = filtered_executors_data[(filtered_executors_data["datetime"] >= start_time_page) &
                                                       (filtered_executors_data["close_datetime"] <= end_time_page)]
performance_candles = PerformanceCandles(strategy_version="v2",
                                         rows=3,
                                         row_heights=[0.6, 0.2, 0.2],
                                         indicators_config=None,
                                         candles_df=candles_df,
                                         executors_df=page_filtered_executors_data,
                                         show_positions=True,
                                         show_buys=False,
                                         show_sells=False,
                                         show_pnl=False,
                                         show_quote_inventory_change=False,
                                         show_indicators=False,
                                         main_height=False,
                                         show_annotations=True)
candles_figure = performance_candles.figure()

candles_figure.add_trace(go.Scatter(x=page_filtered_executors_data["close_datetime"],
                                    y=page_filtered_executors_data["cum_net_pnl_quote"],
                                    mode="lines",
                                    fill="tozeroy",
                                    name="Cum Realized PnL (Quote)"), row=2, col=1)
candles_figure.add_trace(go.Scatter(x=page_filtered_executors_data["close_datetime"],
                                    y=page_filtered_executors_data["cum_filled_amount_quote"],
                                    mode="lines",
                                    fill="tozeroy",
                                    name="Cum Volume (Quote)"), row=3, col=1)
candles_figure.update_yaxes(title_text="Realized PnL ($)", row=2, col=1)
candles_figure.update_yaxes(title_text="Volume ($)", row=3, col=1)
st.plotly_chart(candles_figure, use_container_width=True)


# Tables section
st.divider()
st.subheader("Tables")
with st.expander("💵 Trades"):
    trade_fill = etl.read_trade_fill()
    st.write(trade_fill)
    download_csv_button(trade_fill, "trade_fill", "download-trades")
with st.expander("📩 Orders"):
    orders = etl.read_orders()
    st.write(orders)
    download_csv_button(orders, "orders", "download-orders")
if not market_data.empty:
    with st.expander("💱 Market Data"):
        st.write(market_data)
        download_csv_button(market_data, "market_data", "download-market-data")
with st.expander("📈 Executors"):
    st.write(executors)
    download_csv_button(executors, "executors", "download-executors")
