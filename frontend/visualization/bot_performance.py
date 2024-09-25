import pandas as pd
import streamlit as st

from backend.utils.performance_data_source import PerformanceDataSource
from frontend.st_utils import download_csv_button


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
