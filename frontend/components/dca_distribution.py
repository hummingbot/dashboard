import streamlit as st

from frontend.components.st_inputs import distribution_inputs, get_distribution, normalize


def get_dca_distribution_inputs():
    with st.expander("DCA Builder", expanded=True):
        default_config = st.session_state.get("default_config", {})
        dca_spreads = default_config.get("dca_spreads", [0.01, 0.02, 0.03])
        dca_amounts = default_config.get("dca_amounts", [0.2, 0.5, 0.3])
        tp = default_config.get("take_profit", 0.01) * 100
        sl = default_config.get("stop_loss", 0.02) * 100
        time_limit = default_config.get("time_limit", 60 * 6 * 60) // 60
        ts_ap = default_config.get("trailing_stop", {}).get("activation_price", 0.018) * 100
        ts_delta = default_config.get("trailing_stop", {}).get("trailing_delta", 0.002) * 100
        levels_def = len(dca_spreads)
        c1, c2 = st.columns([0.67, 0.33])
        with c1:
            st.header("DCA Distribution")
            buy_order_levels = st.number_input("Number of Order Levels", min_value=1, value=levels_def,
                                               help="Enter the number of order levels (e.g., 2).")

            if buy_order_levels > levels_def:
                dca_spreads += [0.01 + max(dca_spreads)] * (buy_order_levels - levels_def)
                dca_amounts += [0.2 + max(dca_amounts)] * (buy_order_levels - levels_def)
            elif buy_order_levels < levels_def:
                dca_spreads = dca_spreads[:buy_order_levels]
                dca_amounts = dca_amounts[:buy_order_levels]
            col_spreads, col_amounts = st.columns(2)
            with col_spreads:
                buy_spread_dist_type, buy_spread_start, buy_spread_base, buy_spread_scaling, buy_spread_step, \
                    buy_spread_ratio, buy_manual_spreads = distribution_inputs(col_spreads,
                                                                               "Spread", buy_order_levels, dca_spreads)
            with col_amounts:
                buy_amount_dist_type, buy_amount_start, buy_amount_base, buy_amount_scaling, buy_amount_step, \
                    buy_amount_ratio, buy_manual_amounts = distribution_inputs(col_amounts, "Amount",
                                                                               buy_order_levels, dca_amounts)

        # Generate distributions
        spread_distributions = get_distribution(buy_spread_dist_type, buy_order_levels, buy_spread_start,
                                                buy_spread_base, buy_spread_scaling, buy_spread_step, buy_spread_ratio,
                                                buy_manual_spreads)

        amount_distributions = get_distribution(buy_amount_dist_type, buy_order_levels, buy_amount_start,
                                                buy_amount_base, buy_amount_scaling,
                                                buy_amount_step, buy_amount_ratio, buy_manual_amounts)

        # Normalize and calculate order amounts
        orders_amount_normalized = normalize(amount_distributions)
        spreads_normalized = [spread - spread_distributions[0] for spread in spread_distributions]
        st.write("---")
        # c1, c2, c3, c4, c5 = st.columns(5)
        with c2:
            st.header("Risk Management")
            sl = st.number_input("Stop Loss (%)", min_value=0.0, max_value=100.0, value=sl, step=0.1,
                                 help="Enter the stop loss as a percentage (e.g., 2.0 for 2%).") / 100
            # with c2:
            tp = st.number_input("Take Profit (%)", min_value=0.0, max_value=100.0, value=tp, step=0.1,
                                 help="Enter the take profit as a percentage (e.g., 3.0 for 3%).") / 100
            # with c3:
            time_limit = st.number_input("Time Limit (minutes)", min_value=0, value=time_limit,
                                         help="Enter the time limit in minutes (e.g., 360 for 6 hours).") * 60
            # with c4:
            ts_ap = st.number_input("Trailing Stop Act. Price (%)", min_value=0.0, max_value=100.0, value=ts_ap,
                                    step=0.1,
                                    help="Enter the tr  ailing stop activation price as a percentage (e.g., 1.0 for 1%).") / 100
            # with c5:
            ts_delta = st.number_input("Trailing Stop Delta (%)", min_value=0.0, max_value=100.0, value=ts_delta,
                                       step=0.1,
                                       help="Enter the trailing stop delta as a percentage (e.g., 0.3 for 0.3%).") / 100

    return {
        "dca_spreads": [spread / 100 for spread in spreads_normalized],
        "dca_amounts": orders_amount_normalized,
        "stop_loss": sl,
        "take_profit": tp,
        "time_limit": time_limit,
        "trailing_stop": {
            "activation_price": ts_ap,
            "trailing_delta": ts_delta
        },
    }
