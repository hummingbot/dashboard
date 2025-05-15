import streamlit as st

from frontend.components.market_making_general_inputs import get_market_making_general_inputs
from frontend.components.risk_management import get_risk_management_inputs


def user_inputs():
    default_config = st.session_state.get("default_config", {})
    macd_fast = default_config.get("macd_fast", 21)
    macd_slow = default_config.get("macd_slow", 42)
    macd_signal = default_config.get("macd_signal", 9)
    natr_length = default_config.get("natr_length", 14)
    connector_name, trading_pair, leverage, total_amount_quote, position_mode, cooldown_time, executor_refresh_time, \
        candles_connector, candles_trading_pair, interval = get_market_making_general_inputs(custom_candles=True)
    sl, tp, time_limit, ts_ap, ts_delta, take_profit_order_type = get_risk_management_inputs()
    with st.expander("PMM Dynamic Configuration", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            macd_fast = st.number_input("MACD Fast Period", min_value=1, max_value=200, value=macd_fast)
        with c2:
            macd_slow = st.number_input("MACD Slow Period", min_value=1, max_value=200, value=macd_slow)
        with c3:
            macd_signal = st.number_input("MACD Signal Period", min_value=1, max_value=200, value=macd_signal)
        with c4:
            natr_length = st.number_input("NATR Length", min_value=1, max_value=200, value=natr_length)

    # Create the config
    config = {
        "controller_name": "pmm_dynamic",
        "controller_type": "market_making",
        "manual_kill_switch": False,
        "candles_config": [],
        "connector_name": connector_name,
        "trading_pair": trading_pair,
        "total_amount_quote": total_amount_quote,
        "executor_refresh_time": executor_refresh_time,
        "cooldown_time": cooldown_time,
        "leverage": leverage,
        "position_mode": position_mode,
        "candles_connector": candles_connector,
        "candles_trading_pair": candles_trading_pair,
        "interval": interval,
        "macd_fast": macd_fast,
        "macd_slow": macd_slow,
        "macd_signal": macd_signal,
        "natr_length": natr_length,
        "stop_loss": sl,
        "take_profit": tp,
        "time_limit": time_limit,
        "take_profit_order_type": take_profit_order_type.value,
        "trailing_stop": {
            "activation_price": ts_ap,
            "trailing_delta": ts_delta
        }
    }

    return config
