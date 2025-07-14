import streamlit as st

from frontend.components.config_loader import get_controller_config


def get_market_making_general_inputs(custom_candles=False, controller_name: str = None):
    with st.expander("General Settings", expanded=True):
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        if controller_name:
            default_config = get_controller_config(controller_name)
        else:
            # Fallback for backward compatibility
            default_config = st.session_state.get("default_config", {})
        connector_name = default_config.get("connector_name", "kucoin")
        trading_pair = default_config.get("trading_pair", "WLD-USDT")
        leverage = default_config.get("leverage", 20)
        total_amount_quote = default_config.get("total_amount_quote", 1000)
        position_mode = 0 if default_config.get("position_mode", "HEDGE") == "HEDGE" else 1
        cooldown_time = default_config.get("cooldown_time", 60 * 60) / 60
        executor_refresh_time = default_config.get("executor_refresh_time", 60 * 60) / 60
        candles_connector = None
        candles_trading_pair = None
        interval = None
        with c1:
            connector_name = st.text_input("Connector", value=connector_name,
                                           help="Enter the name of the exchange to trade on (e.g., binance_perpetual).")
        with c2:
            trading_pair = st.text_input("Trading Pair", value=trading_pair,
                                         help="Enter the trading pair to trade on (e.g., WLD-USDT).")
        with c3:
            leverage = st.number_input("Leverage", value=leverage,
                                       help="Set the leverage to use for trading (e.g., 20 for 20x leverage). "
                                            "Set it to 1 for spot trading.")
        with c4:
            total_amount_quote = st.number_input("Total amount of quote", value=total_amount_quote,
                                                 help="Enter the total amount in quote asset to use for "
                                                      "trading (e.g., 1000).")
        with c5:
            position_mode = st.selectbox("Position Mode", ("HEDGE", "ONEWAY"), index=position_mode,
                                         help="Enter the position mode (HEDGE/ONEWAY).")
        with c6:
            cooldown_time = st.number_input("Stop Loss Cooldown Time (minutes)", value=cooldown_time,
                                            help="Specify the cooldown time in minutes after having a "
                                                 "stop loss (e.g., 60).") * 60
        with c7:
            executor_refresh_time = st.number_input("Executor Refresh Time (minutes)", value=executor_refresh_time,
                                                    help="Enter the refresh time in minutes for executors (e.g., 60).") * 60
        if custom_candles:
            candles_connector = default_config.get("candles_connector", "kucoin")
            candles_trading_pair = default_config.get("candles_trading_pair", "WLD-USDT")
            interval = default_config.get("interval", "3m")
            intervals = ["1m", "3m", "5m", "15m", "1h", "4h", "1d"]
            interval_index = intervals.index(interval)
            with c1:
                candles_connector = st.text_input("Candles Connector", value=candles_connector,
                                                  help="Enter the name of the exchange to get candles from"
                                                       "(e.g., binance_perpetual).")
            with c2:
                candles_trading_pair = st.text_input("Candles Trading Pair", value=candles_trading_pair,
                                                     help="Enter the trading pair to get candles for (e.g., WLD-USDT).")
            with c3:
                interval = st.selectbox("Candles Interval", intervals, index=interval_index,
                                        help="Enter the interval for candles (e.g., 1m).")
    return connector_name, trading_pair, leverage, total_amount_quote, position_mode, cooldown_time, \
        executor_refresh_time, candles_connector, candles_trading_pair, interval
