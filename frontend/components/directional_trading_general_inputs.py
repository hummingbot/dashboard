import streamlit as st


def get_directional_trading_general_inputs():
    with st.expander("General Settings", expanded=True):
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1:
            connector_name = st.text_input("Connector", value="binance",
                                           help="Enter the name of the exchange to trade on (e.g., binance_perpetual).")
            candles_connector_name = st.text_input("Candles Connector", value="binance",
                                                   help="Enter the name of the exchange to get candles from (e.g., binance_perpetual).")
        with c2:
            trading_pair = st.text_input("Trading Pair", value="WLD-USDT",
                                         help="Enter the trading pair to trade on (e.g., WLD-USDT).")
            candles_trading_pair = st.text_input("Candles Trading Pair", value="WLD-USDT",
                                                 help="Enter the trading pair to get candles for (e.g., WLD-USDT).")
        with c3:
            leverage = st.number_input("Leverage", value=20,
                                       help="Set the leverage to use for trading (e.g., 20 for 20x leverage). Set it to 1 for spot trading.")
            interval = st.selectbox("Candles Interval", ("1m", "3m", "5m", "15m", "1h", "4h", "1d"), index=1,
                                    help="Enter the interval for candles (e.g., 1m).")
        with c4:
            total_amount_quote = st.number_input("Total amount of quote", value=1000,
                                                 help="Enter the total amount in quote asset to use for trading (e.g., 1000).")
        with c5:
            max_executors_per_side = st.number_input("Max Executors Per Side", value=5,
                                                        help="Enter the maximum number of executors per side (e.g., 5).")
        with c6:
            cooldown_time = st.number_input("Cooldown Time (minutes)", value=10,
                                            help="Time between accepting a new signal in minutes (e.g., 60).") * 60
        with c7:
            position_mode = st.selectbox("Position Mode", ("HEDGE", "ONEWAY"), index=0,
                                         help="Enter the position mode (HEDGE/ONEWAY).")
    return connector_name, trading_pair, leverage, total_amount_quote, max_executors_per_side, cooldown_time, position_mode, candles_connector_name, candles_trading_pair, interval
