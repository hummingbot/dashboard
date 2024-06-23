import asyncio
import math
import streamlit as st
import pandas as pd
import os

from backend.services.backend_api_client import BackendAPIClient
from frontend.visualization.backtesting import create_backtesting_figure
from frontend.st_utils import initialize_st_page, download_csv_button
from backend.utils.etl_performance import ETLPerformance
from backend.utils.databases_aggregator import DatabasesAggregator
from frontend.visualization.performance_metrics import render_performance_metrics, render_performance_summary_table
from frontend.visualization.pnl import get_pnl_bar_fig


async def main():
    initialize_st_page(title="Bot Performance", icon="🚀")
    db_orchestrator = DatabasesAggregator()
    backend_api = BackendAPIClient()
    intervals_to_secs = {
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
    with st.expander("ETL Tool"):
        st.markdown("""In this tool, you can upload and merge different databases.
        
- Drag and drop or upload your databases
- Select those you want to analyze
- Merge databases
    - If you want to start a new analysis or discard previous results, clean tables before loading""")
        st.markdown("#### 1) Upload a new Hummingbot SQLite Database")
        uploaded_db = st.file_uploader("Upload a new Hummingbot SQLite Database", type=["sqlite", "db"],
                                       label_visibility="collapsed")
        if uploaded_db is not None:
            load_database(uploaded_db)
        if len(db_orchestrator.healthy_dbs) == 0:
            st.warning("Oops, there are no databases here. If you uploaded a file and it's not available, you can "
                       "check the status report.")
            if st.button("Status report"):
                if len(db_orchestrator.dbs) == 0:
                    st.write("Nothing here, check if there is any file in dashboard/data/uploaded path.")
                else:
                    st.dataframe(db_orchestrator.status_report, use_container_width=True)
        else:
            healthy_dbs = [db.db_path for db in db_orchestrator.healthy_dbs]
            st.markdown("#### 2) Select databases to merge")
            selected_dbs = st.multiselect("Select databases to merge", healthy_dbs, label_visibility="collapsed")
            if len(selected_dbs) == 0:
                st.warning("No databases selected. Please select at least one database.")
            else:
                st.markdown("#### 3) Merge databases")
                clean_tables_before = st.checkbox("Clean tables before loading", False)
                if st.button("Start"):
                    etl = ETLPerformance(db_path="data/hummingbot.sqlite")
                    tables_dict = db_orchestrator.get_tables(selected_dbs)
                    etl.create_tables()
                    if clean_tables_before:
                        etl.clean_tables()
                    etl.insert_data(tables_dict)
                    st.success("Data loaded successfully!")

    if not os.path.exists("data/hummingbot.sqlite"):
        st.warning("No database detected. Please upload and merge a database to continue.")
        st.stop()

    st.subheader("📊 Overview")
    etl = ETLPerformance(db_path="data/hummingbot.sqlite")
    executors = etl.read_executors()
    orders = etl.read_orders()
    selection, grouped_executors = render_performance_summary_table(executors, orders)
    
    st.subheader("Performance Analysis")
    with st.expander("🔍 Filters"):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            db_name = st.multiselect("Select db", executors["db_name"].unique(), default=grouped_executors.loc[selection["filter"], "db_name"].unique())
            current_close_types = executors["close_type_name"].unique()
            hidden_close_types = ["INSUFFICIENT_BALANCE", "FAILED", "EXPIRED"]
            close_type = st.multiselect("Select close type", current_close_types,
                                        default=[x for x in current_close_types if x not in hidden_close_types])
        with col2:
            instance_name = st.multiselect("Select instance", executors["instance"].unique(), default=grouped_executors.loc[selection["filter"], "instance"].unique())
        with col3:
            controller_id = st.multiselect("Select controller", executors["controller_id"].unique(), default=grouped_executors.loc[selection["filter"], "controller_id"].unique())
        with col4:
            exchange = st.multiselect("Select exchange", executors["exchange"].unique(), default=grouped_executors.loc[selection["filter"], "exchange"].unique())
        with col5:
            trading_pair = st.multiselect("Select trading_pair", executors["trading_pair"].unique(), default=grouped_executors.loc[selection["filter"], "trading_pair"].unique())

    filtered_executors = executors.copy()
    if db_name:
        filtered_executors = filtered_executors[filtered_executors["db_name"].isin(db_name)]
    if instance_name:
        filtered_executors = filtered_executors[filtered_executors["instance"].isin(instance_name)]
    if controller_id:
        filtered_executors = filtered_executors[filtered_executors["controller_id"].isin(controller_id)]
    if exchange:
        filtered_executors = filtered_executors[filtered_executors["exchange"].isin(exchange)]
    if trading_pair:
        filtered_executors = filtered_executors[filtered_executors["trading_pair"].isin(trading_pair)]
    if close_type:
        filtered_executors = filtered_executors[filtered_executors["close_type_name"].isin(close_type)]

    recalculate_pnl_and_volume(filtered_executors)
    render_performance_metrics(filtered_executors)
    pnl_bar_fig = get_pnl_bar_fig(filtered_executors)
    st.plotly_chart(pnl_bar_fig, use_container_width=True)

    # Market data
    st.subheader("Market Data")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        connector = st.selectbox("Connector", executors["exchange"].unique())
    with col2:
        trading_pair = st.selectbox("Select trading pair", filtered_executors["trading_pair"].unique())
    with col3:
        interval = st.selectbox("Select interval", list(intervals_to_secs.keys()), index=3)
    with col4:
        rows_per_page = st.number_input("Candles per Page", value=1500, min_value=1, max_value=5000)

    with st.spinner(f"Loading market data from {connector}..."):
        market_data = backend_api.get_historical_candles(connector=connector,
                                                         trading_pair=trading_pair,
                                                         interval=interval,
                                                         start_time=float(filtered_executors["timestamp"].min()),
                                                         end_time=float(filtered_executors["close_timestamp"].max()))
    filtered_executors = filtered_executors[filtered_executors["trading_pair"] == trading_pair]
    if len(market_data) == 0:
        st.warning("No market data available for this trading pair.")
        st.stop()
    else:
        filtered_market_data = pd.DataFrame(market_data)
        filtered_market_data["datetime"] = pd.to_datetime(filtered_market_data.timestamp, unit="s")
        filtered_market_data.index = filtered_market_data.datetime
        filtered_market_data = filtered_market_data[
            (filtered_market_data.timestamp >= filtered_executors["timestamp"].min()) &
            (filtered_market_data.timestamp <= filtered_executors["close_timestamp"].max())
        ]
        # Add pagination
        total_rows = len(filtered_market_data)
        total_pages = math.ceil(total_rows / rows_per_page)
        if total_pages > 1:
            selected_page = st.select_slider("Select page", list(range(total_pages)), total_pages - 1, key="page_slider")
        else:
            selected_page = 0
        start_idx = selected_page * rows_per_page
        end_idx = start_idx + rows_per_page
        candles_df = filtered_market_data.iloc[start_idx:end_idx]

        start_time_page = candles_df.datetime.min()
        end_time_page = candles_df.datetime.max()

        page_filtered_executors = filtered_executors[(filtered_executors.datetime >= start_time_page) &
                                                     (filtered_executors.close_datetime <= end_time_page) &
                                                     (filtered_executors["exchange"] == connector) &
                                                     (filtered_executors["trading_pair"] == trading_pair)]
        execs = etl._parse_executors(page_filtered_executors)
        fig = create_backtesting_figure(candles_df, execs, config={"trading_pair": trading_pair}, mode="candlestick")
        st.plotly_chart(fig, use_container_width=True)

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
    if not filtered_market_data.empty:
        with st.expander("💱 Market Data"):
            st.write(filtered_market_data)
            download_csv_button(filtered_market_data, "market_data", "download-market-data")
    with st.expander("📈 Executors"):
        st.write(executors)
        download_csv_button(executors, "executors", "download-executors")


def recalculate_pnl_and_volume(executors):
    executors.sort_values("close_datetime", inplace=True)
    executors["cum_net_pnl_quote"] = executors["net_pnl_quote"].cumsum()
    executors["cum_filled_amount_quote"] = executors["filled_amount_quote"].cumsum()


def load_database(uploaded_db, root_path: str = "data/uploaded"):
    file_contents = uploaded_db.read()
    with open(os.path.join(root_path, uploaded_db.name), "wb") as f:
        f.write(file_contents)
    st.success("File uploaded and saved successfully!")


if __name__ == "__main__":
    asyncio.run(main())
