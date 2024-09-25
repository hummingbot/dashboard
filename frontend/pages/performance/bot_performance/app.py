import asyncio
import math
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from backend.services.backend_api_client import BackendAPIClient
from backend.utils.performance_data_source import PerformanceDataSource
from frontend.st_utils import initialize_st_page
from frontend.visualization.backtesting import create_backtesting_figure
from frontend.visualization.backtesting_metrics import render_accuracy_metrics, render_backtesting_metrics, render_close_types
from frontend.visualization.bot_performance import display_performance_summary_table, display_tables_section
from frontend.visualization.dca_builder import create_dca_graph
from frontend.visualization.etl_section import display_etl_section
from frontend.visualization.time_evolution import create_combined_subplots

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


async def main():
    initialize_st_page(title="Bot Performance", icon="🚀", initial_sidebar_state="collapsed")
    st.session_state["default_config"] = {}
    backend_api = BackendAPIClient("localhost")
    checkpoint_data = display_etl_section(backend_api)
    data_source = PerformanceDataSource(checkpoint_data)
    st.divider()

    st.subheader("📊 OVERVIEW")
    display_performance_summary_table(data_source.get_executors_df(), data_source.executors_with_orders)
    st.divider()

    # EXPLODE IN CONTROLLER!
    global_tab, execution_tab = st.tabs(["Global Results", "Execution Analysis"])
    with global_tab:
        st.subheader("🌎 GLOBAL RESULTS")
        display_global_results(backend_api, data_source)
        st.divider()
    with execution_tab:
        st.subheader("🧨 EXECUTION")
        display_execution_analysis(backend_api, data_source)
        st.divider()

    st.subheader("💾 EXPORT")
    display_tables_section(data_source)


def display_global_results(backend_api: BackendAPIClient,
                           data_source: PerformanceDataSource):
    all_results = {}
    selected_controllers = st.multiselect("Select Controllers", data_source.controllers_dict.keys())
    selected_controllers_filter = {
        "controller_id": selected_controllers
    }
    executors_by_controller_type_dict = data_source.get_executors_by_controller_type(selected_controllers_filter)

    for controller_type in ["market_making", "directional_trading"]:
        selected_controller_types = selected_controllers_filter.copy()
        executors_df = executors_by_controller_type_dict.get(controller_type)
        if executors_df is None:
            continue

        selected_controller_types["controller_type"] = [controller_type]
        executors_dict = data_source.get_executor_dict(selected_controller_types)
        results_response = backend_api.get_performance_results(executors=executors_dict,
                                                               controller_type=controller_type)
        all_results[controller_type] = results_response.get("results", {})

    global_results_df = calculate_global_results_table(all_results)

    render_backtesting_metrics(summary_results=global_results_df["global_results"].to_dict(),
                               title="Performance Metrics")

    time_tab, detail_tab = st.tabs(["Time Evolution", "Detail View"])
    with time_tab:
        executors_df = data_source.get_executors_df(executors_filter=selected_controllers_filter,
                                                    apply_executor_data_types=True)
        st.plotly_chart(create_combined_subplots(executors_df), use_container_width=True)
    with detail_tab:
        st.dataframe(global_results_df, use_container_width=True)


def calculate_global_results_table(global_results):
    global_results_df = pd.DataFrame(global_results)

    # Define indices for each calculation type
    sum_index = ["net_pnl", "net_pnl_quote", "total_executors", "total_executors_with_position", "total_volume",
                 "total_long", "total_short", "total_positions", "win_signals", "loss_signals"]
    min_index = ["max_drawdown_usd", "max_drawdown_pct"]
    mean_index = ["accuracy_long", "accuracy_short", "accuracy"]
    dict_index = ["close_types"]

    # Initialize a dictionary to store the global results
    global_dict = {}

    # Sum calculations
    for index in sum_index:
        global_dict[index] = global_results_df.loc[index].sum()

    # Minimum calculations
    for index in min_index:
        global_dict[index] = global_results_df.loc[index].min()

    # Mean calculations
    for index in mean_index:
        global_dict[index] = global_results_df.loc[index].mean()

    # Special variables
    for index in ["sharpe_ratio", "profit_factor"]:
        global_dict[index] = 0

    # Dictionary aggregation
    for index in dict_index:
        result_dict = {}
        for column in global_results_df.columns:
            current_dict = global_results_df.loc[index, column]
            for key, value in current_dict.items():
                if key in result_dict:
                    result_dict[key] += value
                else:
                    result_dict[key] = value
        global_dict[index] = result_dict

    # Convert the global results dictionary to a DataFrame and add it as a new column
    global_results_df['global_results'] = pd.Series(global_dict)
    return global_results_df


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
                start_time = int(executors_df["timestamp"].min())
                end_time = int(executors_df["close_timestamp"].max())
                params = {
                    "connector": connector,
                    "trading_pair": trading_pair,
                    "interval": interval,
                    "start_time": start_time,
                    "end_time": end_time
                }
                market_data = backend_api.get_historical_candles(**params)

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
                executors_filter = {
                    "controller_id": [controller_id],
                    "exchange": [connector],
                    "trading_pair": [trading_pair],
                    "start_time": start_time_page,
                    "end_time": end_time_page
                }
                page_filtered_executors = data_source.get_executors_df(executors_filter)
                controller_type = page_filtered_executors["controller_type"].iloc[0]
                executors: List[Dict[str, Any]] = data_source.get_executor_dict(executors_filter)
                performance_results = backend_api.get_performance_results(executors=executors,
                                                                          controller_type=controller_type)
                fig = create_backtesting_figure(df=candles_df,
                                                executors=performance_results["executors"],
                                                config={"trading_pair": trading_pair})
            performance_section(performance_results, fig, "Real Performance")

        if config_type == "dca" and False:
            with dca_tab:
                col1, col2 = st.columns([0.75, 0.25])
                with col1:
                    display_dca_tab(config_type, config)
                with col2:
                    st.write("### Params")
                    st.json(config)


def filter_all_executors(executors, selection):
    current_close_types = executors["close_type_name"].unique()
    default_close_types = [x for x in current_close_types if x not in ["INSUFFICIENT_BALANCE", "FAILED", "EXPIRED"]]

    close_type = st.multiselect("Close type", current_close_types, default=default_close_types)

    filter_condition = executors["close_type_name"].isin(close_type)
    if selection["filter"].sum() != 0:
        filter_condition &= executors["controller_id"].isin(
            selection.loc[selection["filter"], "controller_id"].unique())

    return executors[filter_condition]


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


def get_config_type(selected_config):
    if len([param.startswith("dca") for param in selected_config.keys()]) > 0:
        return "dca"


def display_dca_tab(config_type, config):
    if config_type != "dca":
        st.info("No DCA configuration available for this controller.")
    else:
        dca_inputs, dca_amount = get_dca_inputs(config)
        fig = create_dca_graph(dca_inputs, dca_amount)
        st.plotly_chart(fig, use_container_width=True)


def performance_section(results: dict, fig=None, title: str = "Backtesting Metrics"):
    # c1, c2 = st.columns([0.9, 0.1])
    # with c1:
    #     render_backtesting_metrics(results["results"], title=title)
    #     st.plotly_chart(fig, use_container_width=True)
    # with c2:
    #     render_accuracy_metrics(results["results"])
    #     st.write("---")
    #     render_close_types(results["results"])
    render_backtesting_metrics(results["results"])
    col1, col2 = st.columns([1, 6])
    with col2:
        st.plotly_chart(fig, use_container_width=True)
    with col1:
        render_accuracy_metrics(results)
        render_close_types(results)


def get_dca_inputs(config: dict):
    dca_inputs = {
        "dca_spreads": config.get("dca_spreads", []),
        "dca_amounts": config.get("dca_amounts", []),
        "stop_loss": config.get("stop_loss", 0.0),
        "take_profit": config.get("take_profit", 0.0),
        "time_limit": config.get("time_limit", 0.0),
        "buy_amounts_pct": config.get("buy_amounts_pct", []),
        "sell_amounts_pct": config.get("sell_amounts_pct", [])
    }
    dca_amount = config["total_amount_quote"]
    return dca_inputs, dca_amount


def display_directional_tab(config_type):
    if config_type != "directional":
        st.info("No Directional configuration available for this controller.")
    else:
        st.info("Directional configuration available.")


if __name__ == "__main__":
    asyncio.run(main())
