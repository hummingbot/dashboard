import streamlit as st
from hummingbot.connector.connector_base import OrderType

def user_inputs():
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1:
        connector = st.text_input("Connector", value="binance_perpetual")
    with c2:
        trading_pair = st.text_input("Trading Pair", value="WLD-USDT")
    with c3:
        total_amount_quote = st.number_input("Total amount of quote", value=1000)
    with c4:
        leverage = st.number_input("Leverage", value=20)
        position_mode = st.selectbox("Position Mode", ("HEDGE", "ONEWAY"), index=0)
    with c5:
        executor_refresh_time = st.number_input("Refresh Time (minutes)", value=3)
        cooldown_time = st.number_input("Cooldown Time (minutes)", value=3)
    with c6:
        sl = st.number_input("Stop Loss (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.1)
        tp = st.number_input("Take Profit (%)", min_value=0.0, max_value=100.0, value=3.0, step=0.1)
        take_profit_order_type = st.selectbox("Take Profit Order Type", (OrderType.LIMIT, OrderType.MARKET))
    with c7:
        ts_ap = st.number_input("Trailing Stop Activation Price (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1)
        ts_delta = st.number_input("Trailing Stop Delta (%)", min_value=0.0, max_value=100.0, value=0.3, step=0.1)
        time_limit = st.number_input("Time Limit (minutes)", min_value=0, value=60 * 6)

    buy_order_levels = st.number_input("Number of Buy Order Levels", min_value=1, value=2)
    sell_order_levels = st.number_input("Number of Sell Order Levels", min_value=1, value=2)

    inputs = {
        "connector": connector,
        "trading_pair": trading_pair,
        "total_amount_quote": total_amount_quote,
        "leverage": leverage,
        "position_mode": position_mode,
        "executor_refresh_time": executor_refresh_time,
        "cooldown_time": cooldown_time,
        "sl": sl,
        "tp": tp,
        "take_profit_order_type": take_profit_order_type,
        "ts_ap": ts_ap,
        "ts_delta": ts_delta,
        "time_limit": time_limit,
        "buy_order_levels": buy_order_levels,
        "sell_order_levels": sell_order_levels
    }
    return inputs
