import streamlit as st
from frontend.components.directional_trading_general_inputs import get_directional_trading_general_inputs
from frontend.components.risk_management import get_risk_management_inputs


def user_inputs():
    connector_name, trading_pair, leverage, total_amount_quote, max_executors_per_side, cooldown_time, position_mode, candles_connector_name, candles_trading_pair, interval = get_directional_trading_general_inputs()
    sl, tp, time_limit, ts_ap, ts_delta, take_profit_order_type = get_risk_management_inputs()
    with st.expander("MACD Bollinger Configuration", expanded=True):
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1:
            bb_length = st.number_input("Bollinger Bands Length", min_value=20, max_value=200, value=100)
        with c2:
            bb_std = st.number_input("Standard Deviation Multiplier", min_value=1.0, max_value=5.0, value=2.0)
        with c3:
            bb_long_threshold = st.number_input("Long Threshold", value=0.2)
        with c4:
            bb_short_threshold = st.number_input("Short Threshold", value=0.8)
        with c5:
            macd_fast = st.number_input("MACD Fast", min_value=1, value=21)
        with c6:
            macd_slow = st.number_input("MACD Slow", min_value=1, value=42)
        with c7:
            macd_signal = st.number_input("MACD Signal", min_value=1, value=9)

    return {
        "controller_name": "macd_bb_v1",
        "controller_type": "directional_trading",
        "connector_name": connector_name,
        "trading_pair": trading_pair,
        "leverage": leverage,
        "total_amount_quote": total_amount_quote,
        "max_executors_per_side": max_executors_per_side,
        "cooldown_time": cooldown_time,
        "position_mode": position_mode,
        "candles_connector": candles_connector_name,
        "candles_trading_pair": candles_trading_pair,
        "interval": interval,
        "bb_length": bb_length,
        "bb_std": bb_std,
        "bb_long_threshold": bb_long_threshold,
        "bb_short_threshold": bb_short_threshold,
        "macd_fast": macd_fast,
        "macd_slow": macd_slow,
        "macd_signal": macd_signal,
        "stop_loss": sl,
        "take_profit": tp,
        "time_limit": time_limit,
        "trailing_stop": {
            "activation_price": ts_ap,
            "trailing_delta": ts_delta
        },
        "take_profit_order_type": take_profit_order_type.value
    }
