import streamlit as st
from frontend.components.st_inputs import get_distribution, normalize, distribution_inputs


def get_executors_distribution_inputs():
    with st.expander("Executors Configuration", expanded=True):
        col_buy, col_sell = st.columns(2)
        with col_buy:
            st.header("Buy Order Settings")
            buy_order_levels = st.number_input("Number of Buy Order Levels", min_value=1, value=2,
                                               help="Enter the number of buy order levels (e.g., 2).")
        with col_sell:
            st.header("Sell Order Settings")
            sell_order_levels = st.number_input("Number of Sell Order Levels", min_value=1, value=2,
                                                help="Enter the number of sell order levels (e.g., 2).")
        col_buy_spreads, col_buy_amounts, col_sell_spreads, col_sell_amounts = st.columns(4)
        with col_buy_spreads:
            buy_spread_dist_type, buy_spread_start, buy_spread_base, buy_spread_scaling, buy_spread_step, buy_spread_ratio, buy_manual_spreads = distribution_inputs(
                col_buy_spreads, "Spread", buy_order_levels)
        with col_buy_amounts:
            buy_amount_dist_type, buy_amount_start, buy_amount_base, buy_amount_scaling, buy_amount_step, buy_amount_ratio, buy_manual_amounts = distribution_inputs(
                col_buy_amounts, "Amount", buy_order_levels)
        with col_sell_spreads:
            sell_spread_dist_type, sell_spread_start, sell_spread_base, sell_spread_scaling, sell_spread_step, sell_spread_ratio, sell_manual_spreads = distribution_inputs(
                col_sell_spreads, "Spread", sell_order_levels)
        with col_sell_amounts:
            sell_amount_dist_type, sell_amount_start, sell_amount_base, sell_amount_scaling, sell_amount_step, sell_amount_ratio, sell_manual_amounts = distribution_inputs(
                col_sell_amounts, "Amount", sell_order_levels)

    # Generate distributions
    buy_spread_distributions = get_distribution(buy_spread_dist_type, buy_order_levels, buy_spread_start,
                                                buy_spread_base, buy_spread_scaling, buy_spread_step, buy_spread_ratio,
                                                buy_manual_spreads)
    sell_spread_distributions = get_distribution(sell_spread_dist_type, sell_order_levels, sell_spread_start,
                                                 sell_spread_base, sell_spread_scaling, sell_spread_step,
                                                 sell_spread_ratio, sell_manual_spreads)

    buy_amount_distributions = get_distribution(buy_amount_dist_type, buy_order_levels, buy_amount_start, buy_amount_base, buy_amount_scaling,
                         buy_amount_step, buy_amount_ratio, buy_manual_amounts)
    sell_amount_distributions = get_distribution(sell_amount_dist_type, sell_order_levels, sell_amount_start, sell_amount_base,
                         sell_amount_scaling, sell_amount_step, sell_amount_ratio, sell_manual_amounts)

    # Normalize and calculate order amounts
    all_orders_amount_normalized = normalize(buy_amount_distributions + sell_amount_distributions)
    buy_order_amounts_pct = [amount for amount in all_orders_amount_normalized[:buy_order_levels]]
    sell_order_amounts_pct = [amount for amount in all_orders_amount_normalized[buy_order_levels:]]
    buy_spread_distributions = [spread / 100 for spread in buy_spread_distributions]
    sell_spread_distributions = [spread / 100 for spread in sell_spread_distributions]
    return buy_spread_distributions, sell_spread_distributions, buy_order_amounts_pct, sell_order_amounts_pct
