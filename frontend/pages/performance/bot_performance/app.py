import asyncio
import math
from datetime import datetime

import streamlit as st
import pandas as pd

from backend.services.backend_api_client import BackendAPIClient
from backend.utils.etl_performance import ETLPerformance
from frontend.visualization.backtesting import create_backtesting_figure
from frontend.st_utils import initialize_st_page, style_metric_cards
from frontend.visualization.backtesting_metrics import render_backtesting_metrics, render_accuracy_metrics, \
    render_close_types
from frontend.visualization.dca_builder import create_dca_graph
from frontend.visualization.bot_performance import BotPerformance, display_performance_summary_table, \
    display_tables_section
from frontend.visualization.etl import display_etl_section
from frontend.visualization.pnl import get_pnl_bar_fig

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
    backend_api = BackendAPIClient()

    checkpoint_data = display_etl_section(backend_api)
    etl_performance = ETLPerformance(checkpoint_data)

    # TODO: This should return a controller_id list
    executors_df = display_and_select_bots(etl_performance.executors,
                                           etl_performance.orders,
                                           etl_performance.executors_with_orders)

    display_global_results(executors_df, backend_api, etl_performance)

    display_execution_analysis(executors_df, etl_performance.orders, backend_api, etl_performance)

    display_tables_section(etl_performance)


def display_and_select_bots(executors, orders, executors_with_orders):
    # TODO: Replace botperformance class approach with current standard
    st.subheader("📊 Overview")

    selection, grouped_executors = display_performance_summary_table(executors, executors_with_orders)
    filtered_executors = filter_all_executors(executors, selection)

    selected_bots = BotPerformance(filtered_executors, orders)
    # selected_bots.display_performance_metrics()

    return filtered_executors


def display_global_results(executors, backend_api, etl):
    parsed_exec = etl.parse_executors(executors)
    execs = etl.dump_executors(parsed_exec)
    results = backend_api.get_performance_results(execs)
    render_backtesting_metrics(results, title="Global Results")
    pnl_bar_fig = get_pnl_bar_fig(executors)
    col1, col2 = st.columns([6, 1])
    with col1:
        st.plotly_chart(pnl_bar_fig, use_container_width=True)
    with col2:
        st.markdown("###")
        render_accuracy_metrics(results, mode="t")
        render_close_types(results, mode="t")


def display_execution_analysis(executors_df, orders, backend_api, etl):
    st.subheader("Execution Analysis")
    st.write("### Filters")
    executors = executors_df.copy()
    cola, colb, colc = st.columns([2, 1, 1])
    with cola:
        controller_id = st.selectbox("Controller ID", executors["controller_id"].unique())
    with colb:
        interval = st.selectbox("Select interval", list(intervals_to_secs.keys()), index=3)
    with colc:
        rows_per_page = st.number_input("Candles per Page", value=1500, min_value=1, max_value=5000)

    configs_dict = {config["id"]: config for config in backend_api.get_all_controllers_config() if config["id"] == controller_id}
    if bool(configs_dict):
        config = configs_dict[controller_id]
        trading_pair = config["trading_pair"]
        connector = config["connector_name"]
        config_type = get_config_type(config)
        config_executors = executors[executors["controller_id"] == config["id"]]
        bot = BotPerformance(config_executors, orders)

        performance_tab, backtesting_tab, comparison_tab, dca_tab, directional_tab = st.tabs(["Real Performance", "Backtesting", "Gap Analysis", "DCA Config", "Directional Config"])

        with performance_tab:
            with st.spinner(f"Loading market data from {connector}..."):
                params = {
                    "connector": connector,
                    "trading_pair": trading_pair,
                    "interval": interval,
                    "start_time": int(executors["timestamp"].min()),
                    "end_time": int(executors["close_timestamp"].max())
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
                start_time_page = paginated_data.index.min()
                end_time_page = paginated_data.index.max()

                page_filtered_executors = filter_executors(executors, connector, trading_pair, start_time_page,
                                                           end_time_page)
                parsed_exec = etl.parse_executors(page_filtered_executors)
                execs = etl.dump_executors(parsed_exec)
                performance_results = backend_api.get_performance_results_with_config(execs, config)
                fig = create_backtesting_figure(df=candles_df,
                                                executors=performance_results["executors"],
                                                config={"trading_pair": trading_pair},
                                                mode="candlestick")
            performance_section(performance_results, fig, "Real Performance")
        with backtesting_tab:
            if config is not None:

                cola, colb, colc, cold = st.columns(4)
                with cola:
                    start_time = st.date_input("Start Date", value=bot.executors.datetime.min())
                with colb:
                    end_time = st.date_input("End Date", value=bot.executors.close_datetime.max())
                with colc:
                    trade_cost = st.number_input("Trade Cost (%)", min_value=0.0, value=0.06, step=0.01, format="%.2f")
                with cold:
                    st.markdown("###")
                    run_backtesting = st.button("Run Backtesting")
            if run_backtesting or True:
                start_datetime = datetime.combine(start_time, datetime.min.time())
                end_datetime = datetime.combine(end_time, datetime.max.time())
                try:
                    bt_results = backend_api.run_backtesting(
                        start_time=int(executors["timestamp"].min()),
                        end_time=int(executors["close_timestamp"].max()),
                        backtesting_resolution=interval,
                        trade_cost=trade_cost / 100,
                        config=config,
                    )
                    bt_results["processed_data"]["timestamp_bt"] = pd.to_datetime(bt_results["processed_data"]["timestamp_bt"],
                                                                                  unit="s")
                    # TODO: Check why run_backtesting returns in thousand seconds
                    for executor in bt_results["executors"]:
                        executor.timestamp = executor.timestamp * 1000
                        executor.close_timestamp = executor.close_timestamp * 1000
                    fig = create_backtesting_figure(
                        df=bt_results["processed_data"].set_index("timestamp_bt"),
                        executors=bt_results["executors"],
                        config=config,
                        mode="candlestick")
                    performance_section(bt_results, fig, "Backtesting Metrics")

                except Exception as e:
                    st.error(e)
                    return None

        with comparison_tab:
            st.write("hi")
        if config_type == "dca":
            with dca_tab:
                col1, col2 = st.columns([0.75, 0.25])
                with col1:
                    # TODO: Add dca metrics here
                    display_dca_tab(config_type, config)
                with col2:
                    st.write("### Params")
                    st.json(config)
        if config_type == "directional":
            with directional_tab:
                display_directional_tab(config_type)


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


def filter_executors(filtered_executors, connector, trading_pair, start_time_page, end_time_page):
    return filtered_executors[
        (filtered_executors.datetime >= start_time_page) &
        (filtered_executors.close_datetime <= end_time_page) &
        (filtered_executors["exchange"] == connector) &
        (filtered_executors["trading_pair"] == trading_pair)
    ]


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
    render_backtesting_metrics(results["results"], title=title)
    col1, col2 = st.columns([1, 6])
    with col2:
        st.plotly_chart(fig, use_container_width=True)
    with col1:
        render_accuracy_metrics(results, mode="t")
        render_close_types(results, mode="t")

def get_dca_inputs(config: dict):
    dca_inputs = {
        "dca_spreads": config["dca_spreads"],
        "dca_amounts": config["dca_amounts"],
        "stop_loss": config["stop_loss"],
        "take_profit": config["take_profit"],
        "time_limit": config["time_limit"],
        "buy_amounts_pct": config["buy_amounts_pct"],
        "sell_amounts_pct": config["sell_amounts_pct"]
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
