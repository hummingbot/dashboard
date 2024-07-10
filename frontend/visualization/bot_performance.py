import streamlit as st
import json
import pandas as pd
from hummingbot.strategy_v2.models.executors import CloseType

from backend.utils.etl_performance import ETLPerformance
from frontend.st_utils import download_csv_button


class BotPerformance:
    def __init__(self, executors, orders: pd.DataFrame = None):
        self.executors = executors
        self.orders = orders
        self.recalculate_pnl_and_volume()

    @property
    def composed_pnl(self):
        return self.executors['net_pnl_quote'].sum()

    @property
    def profit_per_executor(self):
        return self.composed_pnl / len(self.executors)

    @property
    def total_executors(self):
        return len(self.executors)

    @property
    def total_volume(self):
        return self.executors['filled_amount_quote'].sum()

    @property
    def trailing_stop(self):
        return len(self.executors[self.executors['close_type_name'] == 'TRAILING_STOP'])

    @property
    def trailing_stop_pnl(self):
        return self.executors[self.executors['close_type_name'] == 'TRAILING_STOP']['net_pnl_quote'].sum()

    @property
    def take_profit(self):
        return len(self.executors[self.executors['close_type_name'] == 'TAKE_PROFIT'])

    @property
    def take_profit_pnl(self):
        return self.executors[self.executors['close_type_name'] == 'TAKE_PROFIT']['net_pnl_quote'].sum()

    @property
    def stop_loss(self):
        return len(self.executors[self.executors['close_type_name'] == 'STOP_LOSS'])

    @property
    def stop_loss_pnl(self):
        return self.executors[self.executors['close_type_name'] == 'STOP_LOSS']['net_pnl_quote'].sum()

    @property
    def early_stop(self):
        return len(self.executors[self.executors['close_type_name'] == 'EARLY_STOP'])

    @property
    def early_stop_pnl(self):
        return self.executors[self.executors['close_type_name'] == 'EARLY_STOP']['net_pnl_quote'].sum()

    @property
    def time_limit(self):
        return len(self.executors[self.executors['close_type_name'] == 'TIME_LIMIT'])

    @property
    def time_limit_pnl(self):
        return self.executors[self.executors['close_type_name'] == 'TIME_LIMIT']['net_pnl_quote'].sum()

    @property
    def long_percentage(self):
        return 100 * len(self.executors[self.executors['side'] == '1']) / len(self.executors) if len(self.executors) > 0 else 0

    @property
    def long_pnl(self):
        return self.executors[self.executors['side'] == 1]['net_pnl_quote'].sum()

    @property
    def short_percentage(self):
        return 100 * len(self.executors[self.executors['side'] == '2']) / len(self.executors) if len(self.executors) > 0 else 0

    @property
    def short_pnl(self):
        return self.executors[self.executors['side'] == 2]['net_pnl_quote'].sum()

    @staticmethod
    def write_formatted_metric(name, value, delta: str = None):
        if delta is not None:
            color = "red" if "-" in delta else "green"
            st.write(f'<span style="color:white">{name}: {value} </span> <span style="color:{color}">{delta}</span>', unsafe_allow_html=True)
        else:
            color = "red" if "-" in value else "green"
            st.write(f'<span style="color:white">{name}:</span> <span style="color:{color}">{value}</span>', unsafe_allow_html=True)

    def display_performance_metrics_text(self):
        self.write_formatted_metric("Composed PnL", f"$ {self.composed_pnl:.2f}")
        self.write_formatted_metric("Profit per Executor", f"$ {self.profit_per_executor:.2f}")
        self.write_formatted_metric("Total Executors", f"{self.total_executors}")
        self.write_formatted_metric("Total Volume", f"{self.total_volume:.2f}")
        self.write_formatted_metric("# Trailing Stop", f"{self.trailing_stop}", f"($ {self.trailing_stop_pnl:.2f})")
        self.write_formatted_metric("# Take Profit", f"{self.take_profit}", f"($ {self.take_profit_pnl:.2f})")
        self.write_formatted_metric("# Stop Loss", f"{self.stop_loss}", f"($ {self.stop_loss_pnl:.2f})")
        self.write_formatted_metric("# Early Stop", f"{self.early_stop}", f"($ {self.early_stop_pnl:.2f})")
        self.write_formatted_metric("# Time Limit", f"{self.time_limit}", f"($ {self.time_limit_pnl:.2f})")
        self.write_formatted_metric("Long pct", f"{self.long_percentage:.0f} %", f"($ {self.long_pnl:.2f})")
        self.write_formatted_metric("Short pct", f"{self.short_percentage:.0f} %", f"($ {self.short_pnl:.2f})")

    def display_performance_metrics(self):
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
        with col1:
            st.metric("Composed PnL", f"$ {self.composed_pnl:.2f}")
            st.metric("Profit per Executor", f"$ {self.profit_per_executor:.2f}")
        with col2:
            st.metric("Total Executors", f"{self.total_executors}")
            st.metric("Total Volume", f"{self.total_volume:.2f}")
        with col3:
            st.metric("# Trailing Stop", f"{self.trailing_stop}",
                      delta=f"{self.trailing_stop_pnl:.2f}")
        with col4:
            st.metric("# Take Profit", f"{self.take_profit}",
                      delta=f"{self.take_profit_pnl:.2f}")
        with col5:
            st.metric("# Stop Loss", f"{self.stop_loss}",
                      delta=f"{self.stop_loss_pnl:.2f}")
        with col6:
            st.metric("# Early Stop", f"{self.early_stop}",
                      delta=f"{self.early_stop_pnl:.2f}")
        with col7:
            st.metric("# Time Limit", f"{self.time_limit}",
                      delta=f"{self.time_limit_pnl:.2f}")
        with col8:
            st.metric("Long %", f"{self.long_percentage:.0f} %",
                      delta=f"{self.long_pnl:.2f}")
        with col9:
            st.metric("Short %", f"{self.short_percentage:.0f} %",
                      delta=f"{self.short_pnl:.2f}")

    def recalculate_pnl_and_volume(self):
        self.executors.sort_values("close_datetime", inplace=True)
        self.executors["cum_net_pnl_quote"] = self.executors["net_pnl_quote"].cumsum()
        self.executors["cum_filled_amount_quote"] = self.executors["filled_amount_quote"].cumsum()


def display_performance_summary_table(executors, executors_with_orders: pd.DataFrame):
    if not executors_with_orders.empty:
        exit_level = executors_with_orders[executors_with_orders["position"] == "OPEN"].groupby("executor_id")[
            "position"].count()
        executors["exit_level"] = executors["id"].map(exit_level).fillna(0.0).astype(int)
        executors["total_levels"] = executors["config"].apply(lambda x: len(json.loads(x)["prices"]))
        grouped_executors = executors.groupby(["controller_id", "exchange", "trading_pair"]).agg(
            dict(net_pnl_quote="sum",
                 id="count",
                 timestamp="min",
                 close_timestamp="max",
                 filled_amount_quote="sum")).reset_index()

        # Apply the function to the duration column
        grouped_executors["duration"] = (grouped_executors["close_timestamp"] - grouped_executors["timestamp"]).apply(format_duration)
        grouped_executors["filled_amount_quote"] = grouped_executors["filled_amount_quote"].apply(lambda x: f"$ {x:.2f}")
        grouped_executors["net_pnl_quote"] = grouped_executors["net_pnl_quote"].apply(lambda x: f"$ {x:.2f}")
        grouped_executors["filter"] = False
        grouped_executors.rename(columns={"datetime": "start_datetime_utc",
                                          "id": "total_executors"}, inplace=True)
        cols_to_show = ["filter", "controller_id", "exchange", "trading_pair", "total_executors", "filled_amount_quote", "net_pnl_quote", "duration"]
        selection = st.data_editor(grouped_executors[cols_to_show], use_container_width=True, hide_index=True, column_config={"filter": st.column_config.CheckboxColumn(required=True)})
        return selection, grouped_executors


def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{int(days)}d {int(hours)}h {int(minutes)}m"


def display_tables_section(etl: ETLPerformance):
    st.divider()
    st.subheader("Tables")
    with st.expander("💵 Trades"):
        trade_fill = etl.load_trade_fill()
        st.write(trade_fill)
        download_csv_button(trade_fill, "trade_fill", "download-trades")
    with st.expander("📩 Orders"):
        orders = etl.load_orders()
        st.write(orders)
        download_csv_button(orders, "orders", "download-orders")
    with st.expander("📈 Executors"):
        executors = etl.load_executors()
        st.write(executors)
        download_csv_button(executors, "executors", "download-executors")
