import streamlit as st

from frontend.components.executors_distribution import get_executors_distribution_inputs
from frontend.components.market_making_general_inputs import get_market_making_general_inputs
from frontend.components.risk_management import get_risk_management_inputs


def user_inputs():
    default_config = st.session_state.get("default_config", {})
    position_rebalance_threshold_pct = default_config.get("position_rebalance_threshold_pct", 0.05)
    skip_rebalance = default_config.get("skip_rebalance", False)
    
    connector_name, trading_pair, leverage, total_amount_quote, position_mode, cooldown_time, \
        executor_refresh_time, _, _, _ = get_market_making_general_inputs()
    buy_spread_distributions, sell_spread_distributions, buy_order_amounts_pct, \
        sell_order_amounts_pct = get_executors_distribution_inputs()
    sl, tp, time_limit, ts_ap, ts_delta, take_profit_order_type = get_risk_management_inputs()
    
    with st.expander("Position Rebalancing", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            position_rebalance_threshold_pct = st.number_input(
                "Position Rebalance Threshold (%)", 
                min_value=0.0, 
                max_value=100.0, 
                value=position_rebalance_threshold_pct * 100,
                step=0.1,
                help="Threshold percentage for position rebalancing"
            ) / 100
        with c2:
            skip_rebalance = st.checkbox(
                "Skip Rebalance", 
                value=skip_rebalance,
                help="Skip position rebalancing"
            )
    # Create the config
    config = {
        "controller_name": "pmm_simple",
        "controller_type": "market_making",
        "manual_kill_switch": False,
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
        "stop_loss": sl,
        "take_profit": tp,
        "time_limit": time_limit,
        "take_profit_order_type": take_profit_order_type.value,
        "trailing_stop": {
            "activation_price": ts_ap,
            "trailing_delta": ts_delta
        },
        "position_rebalance_threshold_pct": position_rebalance_threshold_pct,
        "skip_rebalance": skip_rebalance
    }
    return config
