import math
from typing import Any, Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from hummingbot.core.data_type.common import TradeType

from backend.services.backend_api_client import BackendAPIClient
from backend.utils.performance_data_source import PerformanceDataSource
from frontend.st_utils import download_csv_button
from frontend.visualization.backtesting import create_backtesting_figure
from frontend.visualization.backtesting_metrics import render_accuracy_metrics, render_backtesting_metrics, render_close_types
from frontend.visualization.performance_dca import display_dca_tab
from frontend.visualization.performance_time_evolution import create_combined_subplots, create_combined_subplots_by_controller

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


def display_performance_summary_table(executors, executors_with_orders: pd.DataFrame):
    if not executors_with_orders.empty:
        executors.sort_values("close_timestamp", inplace=True)
        executors["net_pnl_over_time"] = executors["net_pnl_quote"].cumsum()
        # Now perform the groupby operation, including the full series of net_pnl_over_time as a list for each group
        grouped_executors = executors.groupby(["controller_id", "controller_type", "exchange", "trading_pair"]).agg(
            net_pnl_quote=("net_pnl_quote", "sum"),
            id=("id", "count"),
            timestamp=("timestamp", "min"),
            close_timestamp=("close_timestamp", "max"),
            filled_amount_quote=("filled_amount_quote", "sum"),
            net_pnl_over_time=("net_pnl_over_time", lambda x: list(x))  # Store full series as a list
        ).reset_index()
        # Apply the function to the duration column
        grouped_executors["exchange"] = grouped_executors["exchange"].apply(lambda x: x.replace("_", " ").capitalize())
        grouped_executors["controller_type"] = grouped_executors["controller_type"].apply(
            lambda x: x.replace("_", " ").capitalize()
        )
        grouped_executors["duration"] = (grouped_executors["close_timestamp"] - grouped_executors["timestamp"]).apply(
            format_duration
        )
        grouped_executors["filled_amount_quote_sum"] = grouped_executors["filled_amount_quote"].apply(
            lambda x: f"$ {x:.2f}"
        )
        grouped_executors["net_pnl_quote"] = grouped_executors["net_pnl_quote"].apply(lambda x: f"$ {x:.2f}")
        grouped_executors.rename(columns={"datetime": "start_datetime_utc",
                                          "id": "total_executors"}, inplace=True)
        all_pnl_values = [value for sublist in grouped_executors["net_pnl_over_time"] for value in sublist]
        y_min = min(all_pnl_values) if all_pnl_values else -1e10
        y_max = max(all_pnl_values) if all_pnl_values else 1e10
        cols_to_show = ["exchange", "trading_pair", "net_pnl_quote", "net_pnl_over_time", "filled_amount_quote",
                        "controller_id", "controller_type", "total_executors", "duration"]

        st.dataframe(grouped_executors[cols_to_show],
                     use_container_width=True,
                     hide_index=True,
                     column_config={
                         "exchange": st.column_config.TextColumn("Exchange"),
                         "trading_pair": st.column_config.TextColumn("Trading Pair"),
                         "net_pnl_over_time": st.column_config.LineChartColumn(
                             "PnL Over Time", y_min=y_min, y_max=y_max
                         ),
                         "controller_id": st.column_config.TextColumn("Controller ID"),
                         "controller_type": st.column_config.TextColumn("Controller Type"),
                         "total_executors": st.column_config.NumberColumn("Total Executors"),
                         "filled_amount_quote": st.column_config.NumberColumn("Total Volume", format="$ %.2f"),
                         "net_pnl_quote": st.column_config.NumberColumn("Net PnL", format="$ %.2f"),
                         "duration": st.column_config.TextColumn("Duration")
                     })


def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{int(days)}d {int(hours)}h {int(minutes)}m"


def display_global_results(backend_api: BackendAPIClient,
                           data_source: PerformanceDataSource):
    selected_controllers = st.multiselect("Select Controllers", data_source.controllers_dict.keys())
    selected_controllers_filter = {
        "controller_id": selected_controllers
    }
    executors_dict = data_source.get_executor_dict(selected_controllers_filter)
    results_response = backend_api.get_performance_results(executors=executors_dict)
    all_results = results_response.get("results", {})

    render_backtesting_metrics(summary_results=all_results,
                               title="Global Metrics")

    time_tab, detail_tab = st.tabs(["Time Evolution", "Detail View"])
    with time_tab:
        executors_df = data_source.get_executors_df(executors_filter=selected_controllers_filter,
                                                    apply_executor_data_types=True)
        by_controller = st.toggle("Global / By Controller", value=False)
        if not by_controller:
            st.plotly_chart(create_combined_subplots(executors_df), use_container_width=True)
        else:
            st.plotly_chart(create_combined_subplots_by_controller(executors_df), use_container_width=True)
    with detail_tab:
        long_col, short_col = st.columns(2)
        with long_col:
            with st.container(border=True):
                display_long_vs_short_analysis(backend_api, data_source, selected_controllers_filter, is_long=True)
        with short_col:
            with st.container(border=True):
                display_long_vs_short_analysis(backend_api, data_source, selected_controllers_filter, is_long=False)


def display_long_vs_short_analysis(backend_api: BackendAPIClient,
                                   data_source: PerformanceDataSource,
                                   current_filter: Dict[str, Any] = None,
                                   is_long: bool = True):
    side_filter = current_filter.copy()
    side_filter["side"] = [TradeType.BUY] if is_long else [TradeType.SELL]
    executors_dict = data_source.get_executor_dict(side_filter,
                                                   apply_executor_data_types=True,
                                                   remove_special_fields=True)
    results = backend_api.get_performance_results(executors=executors_dict).get("results", {})
    if results:
        executors_df = data_source.get_executors_df(executors_filter=side_filter,
                                                    apply_executor_data_types=True)
        side_str = "Long" if is_long else "Short"
        st.write(f"### {side_str} Positions")
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Net PnL (Quote)", value=f"{results['net_pnl_quote']:.2f}")
        col2.metric(label="Max Drawdown (USD)", value=f"{results['max_drawdown_usd']:.2f}")
        col3.metric(label="Total Volume (Quote)", value=f"{results['total_volume']:.2f}")
        col1.metric(label="Sharpe Ratio", value=f"{results['sharpe_ratio']:.2f}")
        col2.metric(label="Profit Factor", value=f"{results['profit_factor']:.2f}")
        col3.metric(label="Total Executors with Position", value=results['total_executors_with_position'])
        fig = go.Figure(data=[go.Pie(labels=list(results["close_types"].keys()),
                                     values=list(results["close_types"].values()), hole=.3)])
        fig.update_layout(title="Close Types")
        st.plotly_chart(fig, use_container_width=True)
        executors_by_close_type = executors_df.groupby("close_type_name")["net_pnl_quote"].sum().to_dict()
        keys_to_remove = ["EXPIRED", "INSUFFICIENT_BALANCE", "FAILED"]
        for key in keys_to_remove:
            if key in executors_by_close_type:
                del executors_by_close_type[key]
        columns = st.columns(len(executors_by_close_type))
        for i, (key, value) in enumerate(executors_by_close_type.items()):
            with columns[i]:
                st.metric(label=key, value=f"${value:.2f}")


def display_tables_section(data_source: PerformanceDataSource):
    with st.expander("💵 Trades"):
        trade_fill = data_source.load_trade_fill()
        st.write(trade_fill)
        download_csv_button(trade_fill, "trade_fill", "download-trades")
    with st.expander("📩 Orders"):
        orders = data_source.load_orders()
        st.write(orders)
        download_csv_button(orders, "orders", "download-orders")
    with st.expander("📈 Executors"):
        executors = data_source.get_executors_df()
        st.write(executors)
        download_csv_button(executors, "executors", "download-executors")


def display_execution_analysis(backend_api: BackendAPIClient,
                               data_source: PerformanceDataSource):
    st.write("### Filters")
    cola, colb, colc = st.columns([2, 1, 1])
    with cola:
        controller_id = st.selectbox("Controller ID", data_source.controllers_dict.keys())
    with colb:
        interval = st.selectbox("Select interval", list(intervals_to_secs.keys()), index=3)
    with colc:
        rows_per_page = st.number_input("Candles per Page", value=1500, min_value=1, max_value=5000)

    if bool(data_source.controllers_dict):
        config = data_source.controllers_dict[controller_id]
        executors_filter = {
            "controller_id": [controller_id],
        }
        executors_df = data_source.get_executors_df(executors_filter=executors_filter,
                                                    apply_executor_data_types=True)
        trading_pair = config["trading_pair"]
        connector = config["connector_name"]
        config_type = get_config_type(config)

        performance_tab, dca_tab = st.tabs(["Real Performance", "DCA Config"])

        with performance_tab:
            with st.spinner(f"Loading market data from {connector}..."):
                start_time = int(executors_df["timestamp"].min()) - 60 * intervals_to_secs[interval]
                end_time = int(executors_df["close_timestamp"].max()) + 60 * intervals_to_secs[interval]
                params = {
                    "connector": connector,
                    "trading_pair": trading_pair,
                    "interval": interval,
                    "start_time": start_time,
                    "end_time": end_time
                }
                executors_filter = {
                    "controller_id": [controller_id],
                    "exchange": [connector],
                    "trading_pair": [trading_pair],
                    "close_type_name": [
                        "TAKE_PROFIT",
                        "TRAILING_STOP",
                        "STOP_LOSS",
                        "TIME_LIMIT",
                        "EARLY_STOP",
                    ]
                }
                executors: List[Dict[str, Any]] = data_source.get_executor_dict(executors_filter)
                market_data, performance_results = fetch_market_data_with_execution(backend_api, params, executors)

            if len(market_data) == 0:
                st.warning("No market data available for this trading pair.")
                return pd.DataFrame()

            candles_df = pd.DataFrame(market_data)
            candles_df["datetime"] = pd.to_datetime(candles_df.timestamp, unit="s")
            candles_df.set_index("datetime", inplace=True)
            paginated_data, selected_page = paginate_data(candles_df, rows_per_page)

            if selected_page is not None:
                start_time_page = paginated_data.timestamp.min()
                end_time_page = paginated_data.timestamp.max()
                page_candles_df = candles_df.loc[(candles_df.timestamp >= start_time_page) &
                                                 (candles_df.timestamp <= end_time_page)]
                executors_filter["start_time"] = start_time_page
                executors_filter["end_time"] = end_time_page
                page_executors = data_source.get_executor_info_list(executors_filter)
                fig = create_backtesting_figure(df=page_candles_df,
                                                executors=page_executors,
                                                config={"trading_pair": trading_pair})
            performance_section(performance_results, fig, "Real Performance")

        if config_type == "dca":
            with dca_tab:
                col1, col2 = st.columns([0.75, 0.25])
                with col1:
                    display_dca_tab(config_type, config)
                with col2:
                    st.write("### Params")
                    st.json(config)


@st.cache_data(show_spinner=False)
def fetch_market_data_with_execution(_backend_api, params, _executors):
    candles_df = _backend_api.get_historical_candles(**params)
    results = _backend_api.get_performance_results(executors=_executors)
    return candles_df, results


def get_config_type(selected_config):
    if len([param.startswith("dca") for param in selected_config.keys()]) > 0:
        return "dca"


def paginate_data(filtered_market_data, rows_per_page):
    total_rows = len(filtered_market_data)
    total_pages = math.ceil(total_rows / rows_per_page)
    if total_pages > 1:
        selected_page = st.select_slider("Select page", list(range(total_pages)), total_pages - 1, key="page_slider")
    else:
        selected_page = 0
    start_idx = selected_page * rows_per_page
    end_idx = start_idx + rows_per_page
    paginated_data = filtered_market_data.iloc[start_idx:end_idx]
    return paginated_data, selected_page


def performance_section(results: dict, fig=None, title: str = "Backtesting Metrics"):
    render_backtesting_metrics(results["results"], title="Controller Performance")
    col1, col2 = st.columns([6, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        render_accuracy_metrics(results)
        render_close_types(results)
