import streamlit as st

from frontend.components.executors_distribution import get_executors_distribution_inputs
from frontend.components.market_making_general_inputs import get_market_making_general_inputs


def user_inputs():
    connector_name, trading_pair, leverage, total_amount_quote, position_mode, cooldown_time, executor_refresh_time, _, _, _ = get_market_making_general_inputs()
    buy_spread_distributions, sell_spread_distributions, buy_order_amounts_pct, sell_order_amounts_pct = get_executors_distribution_inputs()
    with st.expander("Custom D-Man Maker V2 Settings"):
        c1, c2 = st.columns(2)
        with c1:
            top_executor_refresh_time = st.number_input("Top Refresh Time (minutes)", value=60) * 60
        with c2:
            executor_activation_bounds = st.number_input("Activation Bounds (%)", value=0.1) / 100
    # Create the config
    config = {
        "controller_name": "dman_maker_v2",
        "controller_type": "market_making",
        "manual_kill_switch": None,
        "candles_config": [],
        "connector_name": connector_name,
        "trading_pair": trading_pair,
        "total_amount_quote": total_amount_quote,
        "buy_spreads": buy_spread_distributions,
        "sell_spreads": sell_spread_distributions,
        "buy_amounts_pct": buy_order_amounts_pct,
        "sell_amounts_pct": sell_order_amounts_pct,
        "executor_refresh_time": executor_refresh_time,
        "cooldown_time": cooldown_time,
        "leverage": leverage,
        "position_mode": position_mode,
        "top_executor_refresh_time": top_executor_refresh_time,
        "executor_activation_bounds": [executor_activation_bounds]
    }

    return config
