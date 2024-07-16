import streamlit as st

from frontend.components.directional_trading_general_inputs import get_directional_trading_general_inputs
from frontend.components.risk_management import get_risk_management_inputs


def user_inputs():
    default_config = st.session_state.get("default_config", {})
    length = default_config.get("length", 20)
    multiplier = default_config.get("multiplier", 3.0)
    percentage_threshold = default_config.get("percentage_threshold", 0.5)
    connector_name, trading_pair, leverage, total_amount_quote, max_executors_per_side, cooldown_time, position_mode, \
        candles_connector_name, candles_trading_pair, interval = get_directional_trading_general_inputs()
    sl, tp, time_limit, ts_ap, ts_delta, take_profit_order_type = get_risk_management_inputs()

    with st.expander("SuperTrend Configuration", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            length = st.number_input("Supertrend Length", min_value=1, max_value=200, value=length)
        with c2:
            multiplier = st.number_input("Supertrend Multiplier", min_value=1.0, max_value=5.0, value=multiplier)
        with c3:
            percentage_threshold = st.number_input("Percentage Threshold (%)", value=percentage_threshold) / 100
    return {
        "controller_name": "supertrend_v1",
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
        "length": length,
        "multiplier": multiplier,
        "percentage_threshold": percentage_threshold,
        "stop_loss": sl,
        "take_profit": tp,
        "time_limit": time_limit,
        "trailing_stop": {
            "activation_price": ts_ap,
            "trailing_delta": ts_delta
        },
        "take_profit_order_type": take_profit_order_type.value
    }
