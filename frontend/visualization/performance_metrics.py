import streamlit as st
import json
import pandas as pd
from hummingbot.strategy_v2.models.executors import CloseType


def render_performance_metrics(executors):
    df = executors.copy()
    df["close_type"] = df["close_type"].apply(lambda x: CloseType(x).name)
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
    with col1:
        st.metric("Composed PnL", f"$ {df['net_pnl_quote'].sum():.2f}")
        st.metric("Profit per Executor", f"$ {df['net_pnl_quote'].sum() / len(df):.2f}")
    with col2:
        st.metric("Total Executors", f"{len(df)}")
        st.metric("Total Volume", f"{df['filled_amount_quote'].sum():.2f}")
    with col3:
        st.metric("# Trailing Stop", f"{len(df[df['close_type'] == 'TRAILING_STOP'])}",
                  delta=f"{df[df['close_type'] == 'TRAILING_STOP']['net_pnl_quote'].sum():.2f}")
    with col4:
        st.metric("# Take Profit", f"{len(df[df['close_type'] == 'TAKE_PROFIT'])}",
                  delta=f"{df[df['close_type'] == 'TAKE_PROFIT']['net_pnl_quote'].sum():.2f}")
    with col5:
        st.metric("# Stop Loss", f"{len(df[df['close_type'] == 'STOP_LOSS'])}",
                  delta=f"{df[df['close_type'] == 'STOP_LOSS']['net_pnl_quote'].sum():.2f}")
    with col6:
        st.metric("# Early Stop", f"{len(df[df['close_type'] == 'EARLY_STOP'])}",
                  delta=f"{df[df['close_type'] == 'EARLY_STOP']['net_pnl_quote'].sum():.2f}")
    with col7:
        st.metric("# Time Limit", f"{len(df[df['close_type'] == 'TIME_LIMIT'])}",
                  delta=f"{df[df['close_type'] == 'TIME_LIMIT']['net_pnl_quote'].sum():.2f}")
    with col8:
        st.metric("Long %", f"{100 * len(df[df['side'] == '1']) / len(df):.0f} %",
                  delta=f"{df[df['side'] == 1]['net_pnl_quote'].sum():.2f}")
    with col9:
        st.metric("Short %", f"{100 * len(df[df['side'] == '2']) / len(df):.0f} %",
                  delta=f"{df[df['side'] == 2]['net_pnl_quote'].sum():.2f}")


def render_performance_summary_table(executors, orders):
    executors_with_orders = get_executors_with_orders(executors, orders)
    executors = get_total_and_exit_levels(executors_with_orders, executors)
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
    cols_to_show = ["filter", "controller_id", "exchange", "trading_pair", "total_executors", "filled_amount_quote", "net_pnl_quote", "duration", "tsl_tp_sl_tl_es"]
    selection = st.data_editor(grouped_executors[cols_to_show], use_container_width=True, hide_index=True, column_config={"filter": st.column_config.CheckboxColumn(required=True)})
    return selection, grouped_executors


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


def get_total_and_exit_levels(executors_with_orders_df: pd.DataFrame, executors_df: pd.DataFrame):
    exit_level = executors_with_orders_df[executors_with_orders_df["position"] == "OPEN"].groupby("executor_id")["position"].count()
    executors_df["exit_level"] = executors_df["id"].map(exit_level).fillna(0.0).astype(int)
    executors_df["total_levels"] = executors_df["config"].apply(lambda x: len(json.loads(x)["prices"]))
    return executors_df


def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{int(days)}d {int(hours)}h {int(minutes)}m"


def get_tp_sl_tsl_es_tl(executors_df: pd.DataFrame, grouped_executors_df: pd.DataFrame):
    df = executors_df.copy()
    df["close_type"] = df["close_type"].apply(lambda x: CloseType(x).name)
    df = df.groupby(["instance", "controller_id", "exchange", "trading_pair", "db_name", "close_type"])[
        "close_type"].count().reset_index(name="count")
    result = df.groupby(["instance", "controller_id", "exchange", "trading_pair", "db_name"]).apply(concatenate_values).reset_index(name='tsl_tp_sl_tl_es')
    return grouped_executors_df.merge(result, on=["instance", "controller_id", "exchange", "trading_pair", "db_name"], how="left")


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
