import streamlit as st


def get_market_making_general_inputs():
    with st.expander("General Settings", expanded=True):
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1:
            connector_name = st.text_input("Connector", value="binance_perpetual",
                                           help="Enter the name of the exchange to trade on (e.g., binance_perpetual).")
        with c2:
            trading_pair = st.text_input("Trading Pair", value="WLD-USDT",
                                         help="Enter the trading pair to trade on (e.g., WLD-USDT).")
        with c3:
            leverage = st.number_input("Leverage", value=20,
                                       help="Set the leverage to use for trading (e.g., 20 for 20x leverage). Set it to 1 for spot trading.")
        with c4:
            total_amount_quote = st.number_input("Total amount of quote", value=1000,
                                                 help="Enter the total amount in quote asset to use for trading (e.g., 1000).")
        with c5:
            position_mode = st.selectbox("Position Mode", ("HEDGE", "ONEWAY"), index=0,
                                         help="Enter the position mode (HEDGE/ONEWAY).")
        with c6:
            cooldown_time = st.number_input("Cooldown Time (minutes)", value=60,
                                            help="Specify the cooldown time in minutes (e.g., 60).") * 60
        with c7:
            executor_refresh_time = st.number_input("Executor Refresh Time (minutes)", value=60,
                                                    help="Enter the refresh time in minutes for executors (e.g., 60).") * 60
    return connector_name, trading_pair, leverage, total_amount_quote, position_mode, cooldown_time, executor_refresh_time
