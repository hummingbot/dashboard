import asyncio
import math
import streamlit as st
import plotly.graph_objects as go
import json
import pandas as pd
import numpy as np

from hummingbot.data_feed.candles_feed.candles_factory import CandlesFactory
from hummingbot.data_feed.candles_feed.data_types import HistoricalCandlesConfig, CandlesConfig
import os

from frontend.visualization.performance import ChartsBase
from frontend.visualization.performance_candles import PerformanceCandles
from frontend.st_utils import initialize_st_page, download_csv_button
from backend.utils.hummingbot_database import HummingbotDatabase
from backend.utils.etl_performance import ETLPerformance
from backend.utils.databases_aggregator import DatabasesAggregator
from backend.services.backend_api_client import BackendAPIClient


candles_factory = CandlesFactory()


async def get_historical_candles(config: HistoricalCandlesConfig):
    try:
        candles_config = CandlesConfig(
            connector=config.connector_name,
            trading_pair=config.trading_pair,
            interval=config.interval
        )
        candles = candles_factory.get_candle(candles_config)
        all_candles = []
        current_start_time = config.start_time

        while current_start_time <= config.end_time:
            fetched_candles = await candles.fetch_candles(start_time=current_start_time)
            if fetched_candles.size < 1:
                break

            all_candles.append(fetched_candles)
            last_timestamp = fetched_candles[-1][0]  # Assuming the first column is the timestamp
            current_start_time = int(last_timestamp)

        final_candles = np.concatenate(all_candles, axis=0) if all_candles else np.array([])
        candles_df = pd.DataFrame(final_candles, columns=candles.columns)
        candles_df.drop_duplicates(subset=["timestamp"], inplace=True)
        candles_df["timestamp"] = candles_df["timestamp"] // 1e3
        return candles_df
    except Exception as e:
        return {"error": str(e)}


def concatenate_values(row):
    tsl = row[row['close_type'] == 'TRAILING_STOP']['count'].values
    tp = row[row['close_type'] == 'TAKE_PROFIT']['count'].values
    sl = row[row['close_type'] == 'STOP_LOSS']['count'].values
    tl = row[row['close_type'] == 'TIME_LIMIT']['count'].values
    es = row[row['close_type'] == 'EARLY_STOP']['count'].values

    tsl_count = tsl[0] if len(tsl) > 0 else 0
    tp_count = tp[0] if len(tp) > 0 else 0
    sl_count = sl[0] if len(sl) > 0 else 0
    tl_count = tl[0] if len(tl) > 0 else 0
    es_count = es[0] if len(es) > 0 else 0

    return f"{tsl_count}\t | \t{tp_count}\t | \t{sl_count}\t | \t{tl_count}\t | \t{es_count}"


def get_tp_sl_tsl_es_tl(executors_df: pd.DataFrame, grouped_executors_df: pd.DataFrame):
    df = executors_df.groupby(["instance", "controller_id", "exchange", "trading_pair", "db_name", "close_type"])[
        "close_type"].count().reset_index(name="count")
    result = df.groupby(["instance", "controller_id", "exchange", "trading_pair", "db_name"]).apply(concatenate_values).reset_index(name='tsl_tp_sl_tl_es')
    return grouped_executors_df.merge(result, on=["instance", "controller_id", "exchange", "trading_pair", "db_name"], how="left")


def get_total_and_exit_levels(executors_with_orders_df: pd.DataFrame, executors_df: pd.DataFrame):
    exit_level = executors_with_orders_df[executors_with_orders_df["position"] == "OPEN"].groupby("executor_id")["position"].count()
    executors_df["exit_level"] = executors_df["id"].map(exit_level).fillna(0.0).astype(int)
    executors_df["total_levels"] = executors_df["config"].apply(lambda x: len(json.loads(x)["prices"]))
    return executors_df


def get_executors_with_orders(executors_df: pd.DataFrame, orders_df: pd.DataFrame):
    df = pd.DataFrame(executors_df['custom_info'].tolist(), index=executors_df['id'],
                      columns=["custom_info"]).reset_index()
    df["custom_info"] = df["custom_info"].apply(lambda x: json.loads(x))
    df["orders"] = df["custom_info"].apply(lambda x: x["order_ids"])
    df.rename(columns={"id": "executor_id"}, inplace=True)
    exploded_df = df.explode("orders").rename(columns={"orders": "order_id"})
    exec_with_orders = exploded_df.merge(orders_df, left_on="order_id", right_on="client_order_id", how="inner")
    exec_with_orders = exec_with_orders[exec_with_orders["last_status"].isin(["SellOrderCompleted", "BuyOrderCompleted"])]
    return exec_with_orders[["executor_id", "order_id", "last_status", "last_update_timestamp", "price", "amount", "position"]]


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

async def main():
    initialize_st_page(title="Bot Performance", icon="🚀")
    backend_api = BackendAPIClient()
    db_orchestrator = DatabasesAggregator()

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
    etl = ETLPerformance(db_path="data/hummingbot.sqlite")
    executors = etl.read_executors()
    orders = etl.read_orders()
    executors_with_orders = get_executors_with_orders(executors, orders)
    executors = get_total_and_exit_levels(executors_with_orders, executors)
    charts = ChartsBase()

    st.divider()
    st.subheader("📊 Overview")
    grouped_executors = executors.groupby(["instance", "controller_id", "exchange", "trading_pair", "db_name"]).agg(
        {"net_pnl_quote": "sum",
         "id": "count",
         "datetime": "min",
         "close_datetime": "max",
         "filled_amount_quote": "sum"}).reset_index()

    # Apply the function to the duration column
    grouped_executors["duration"] = (grouped_executors["close_datetime"] - grouped_executors["datetime"]).dt.total_seconds().apply(format_duration)
    grouped_executors["filled_amount_quote"] = grouped_executors["filled_amount_quote"].apply(lambda x: f"$ {x:.2f}")
    grouped_executors["net_pnl_quote"] = grouped_executors["net_pnl_quote"].apply(lambda x: f"$ {x:.2f}")
    grouped_executors["filter"] = False
    grouped_executors = get_tp_sl_tsl_es_tl(executors, grouped_executors)
    grouped_executors.rename(columns={"datetime": "start_datetime_utc",
                                      "id": "total_executors"}, inplace=True)
    cols_to_show = ["filter", "controller_id", "exchange", "trading_pair", "db_name", "total_executors", "filled_amount_quote", "net_pnl_quote", "duration", "tsl_tp_sl_tl_es"]
    selection = st.data_editor(grouped_executors[cols_to_show], use_container_width=True, hide_index=True, column_config={"filter": st.column_config.CheckboxColumn(required=True)})
    with st.expander("🔍 Filters"):
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        with col1:
            db_name = st.multiselect("Select db", executors["db_name"].unique(), default=grouped_executors.loc[selection["filter"], "db_name"].unique())
        with col2:
            instance_name = st.multiselect("Select instance", executors["instance"].unique(), default=grouped_executors.loc[selection["filter"], "instance"].unique())
        with col3:
            controller_id = st.multiselect("Select controller", executors["controller_id"].unique(), default=grouped_executors.loc[selection["filter"], "controller_id"].unique())
        with col4:
            exchange = st.multiselect("Select exchange", executors["exchange"].unique(), default=grouped_executors.loc[selection["filter"], "exchange"].unique())
        with col5:
            trading_pair = st.multiselect("Select trading_pair", executors["trading_pair"].unique(), default=grouped_executors.loc[selection["filter"], "trading_pair"].unique())
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

    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
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
        st.metric("# Time Limit", f"{len(filtered_executors_data[filtered_executors_data['close_type'] == 'TIME_LIMIT'])}",
                  delta=f"{filtered_executors_data[filtered_executors_data['close_type'] == 'TIME_LIMIT']['net_pnl_quote'].sum():.2f}")
    with col8:
        st.metric("Long %", f"{100 * len(filtered_executors_data[filtered_executors_data['side'] == 1]) / len(filtered_executors_data):.2f} %",
                  delta=f"{filtered_executors_data[filtered_executors_data['side'] == 1]['net_pnl_quote'].sum():.2f}")
    with col9:
        st.metric("Short %", f"{100 * len(filtered_executors_data[filtered_executors_data['side'] == 2]) / len(filtered_executors_data):.2f} %",
                  delta=f"{filtered_executors_data[filtered_executors_data['side'] == 2]['net_pnl_quote'].sum():.2f}")

    # PnL Over Time
    realized_pnl_data = filtered_executors_data[["close_datetime", "net_pnl_quote"]].sort_values("close_datetime")
    realized_pnl_data["cum_pnl_over_time"] = realized_pnl_data["net_pnl_quote"].cumsum()
    st.plotly_chart(charts.realized_pnl_over_time(data=realized_pnl_data,
                                                  cum_realized_pnl_column="cum_pnl_over_time"),
                    use_container_width=True)

    # Close Types
    col1, col2, col3 = st.columns(3)
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

    with (col3):
        intra_level_id_data = filtered_executors_data.groupby(['exit_level', 'close_type']).size().reset_index(name='count')
        fig = go.Figure()
        fig.add_trace(go.Pie(labels=intra_level_id_data.loc[intra_level_id_data["exit_level"] != 0, 'exit_level'],
                             values=intra_level_id_data.loc[intra_level_id_data["exit_level"] != 0, 'count'],
                             hole=0.4))
        fig.update_layout(title='Count of Close Types by Exit Level')
        st.plotly_chart(fig, use_container_width=True)

    # Intra level Analysis
    intra_level_id_pnl_data = filtered_executors_data.groupby(['exit_level'])['net_pnl_quote'].sum().reset_index(name='pnl')

    fig = go.Figure()

    for close_type in intra_level_id_data['close_type'].unique():
        temp_data = intra_level_id_data[intra_level_id_data['close_type'] == close_type]
        fig.add_trace(go.Bar(
            x=temp_data['exit_level'],
            y=temp_data['count'],
            name=close_type,
            yaxis='y'
        ))

    fig.add_trace(go.Scatter(x=intra_level_id_pnl_data['exit_level'],
                             y=intra_level_id_pnl_data['pnl'],
                             mode='lines+markers',
                             name='PnL',
                             text=intra_level_id_pnl_data['pnl'].apply(lambda x: f"$ {x:.2f}"),
                             textposition='top center',
                             yaxis='y2'))

    # Determine the maximum absolute value of count and pnl for setting the y-axis range
    max_count = max(abs(intra_level_id_data['count'].min()), abs(intra_level_id_data['count'].max()))
    max_pnl = max(abs(intra_level_id_pnl_data['pnl'].min()), abs(intra_level_id_pnl_data['pnl'].max()))

    # Update layout
    fig.update_layout(
        title='Count of Close Types by Exit Level and PnL by Exit Level',
        xaxis=dict(title='Exit Level'),
        yaxis=dict(title='Count', side='left', range=[-max_count, max_count]),
        yaxis2=dict(title='PnL', overlaying='y', side='right', range=[-max_pnl, max_pnl]),
        barmode='group'
    )

    st.plotly_chart(fig, use_container_width=True)

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
    connector = st.selectbox("Connector", executors["exchange"].unique())
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        trading_pair = st.selectbox("Select trading pair", filtered_executors_data["trading_pair"].unique())
    with col2:
        interval = st.selectbox("Select interval", list(intervals.keys()), index=3)
    with col3:
        rows_per_page = st.number_input("Candles per Page", value=1500, min_value=1, max_value=5000)

    start_datetime_in_secs = int(filtered_executors_data["datetime"].min().timestamp())
    end_datetime_in_secs = int(filtered_executors_data["close_datetime"].max().timestamp())

    historical_candles_config = HistoricalCandlesConfig(connector_name=connector,
                                                        trading_pair=trading_pair,
                                                        interval=interval,
                                                        start_time=start_datetime_in_secs * 1000,
                                                        end_time=end_datetime_in_secs * 1000)
    market_data = await get_historical_candles(historical_candles_config)
    filtered_market_data = pd.DataFrame(market_data)
    filtered_market_data["timestamp"] = filtered_market_data["timestamp"]
    filtered_market_data["datetime"] = pd.to_datetime(filtered_market_data.timestamp, unit="s")
    filtered_market_data.index = pd.to_datetime(filtered_market_data.timestamp)
    # Add pagination
    total_rows = len(filtered_market_data)
    total_pages = math.ceil(total_rows / rows_per_page)
    if total_pages > 1:
        selected_page = st.select_slider("Select page", list(range(total_pages)), total_pages - 1, key="page_slider")
    else:
        selected_page = 0
    start_idx = selected_page * rows_per_page
    end_idx = start_idx + rows_per_page
    candles_df = filtered_market_data[start_idx:end_idx]

    start_time_page = candles_df.datetime.min()
    end_time_page = candles_df.datetime.max()
    filtered_executors_data.sort_values("close_datetime", inplace=True)
    filtered_executors_data["cum_net_pnl_quote"] = filtered_executors_data["net_pnl_quote"].cumsum()
    filtered_executors_data["cum_filled_amount_quote"] = filtered_executors_data["filled_amount_quote"].cumsum()
    page_filtered_executors_data = filtered_executors_data[(filtered_executors_data.datetime >= start_time_page) &
                                                           (filtered_executors_data.close_datetime <= end_time_page) &
                                                           (filtered_executors_data["exchange"] == connector) &
                                                           (filtered_executors_data["trading_pair"] == trading_pair)]
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
    if not filtered_market_data.empty:
        with st.expander("💱 Market Data"):
            st.write(filtered_market_data)
            download_csv_button(filtered_market_data, "market_data", "download-market-data")
    with st.expander("📈 Executors"):
        st.write(executors)
        download_csv_button(executors, "executors", "download-executors")


def load_database(uploaded_db, root_path: str = "data/uploaded"):
    file_contents = uploaded_db.read()
    with open(os.path.join(root_path, uploaded_db.name), "wb") as f:
        f.write(file_contents)
    st.success("File uploaded and saved successfully!")


if __name__ == "__main__":
    asyncio.run(main())