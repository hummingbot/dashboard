import streamlit as st
from datetime import datetime, timedelta


def backtesting_section(inputs, backend_api_client):
    st.write("### Backtesting")
    c1, c2, c3, c4, c5 = st.columns(5)
    default_end_time = datetime.now().date() - timedelta(days=1)
    default_start_time = default_end_time - timedelta(days=2)
    with c1:
        start_date = st.date_input("Start Date", default_start_time)
    with c2:
        end_date = st.date_input("End Date", default_end_time,
                                 help="End date is inclusive, make sure that you are not including the current date.")
    with c3:
        backtesting_resolution = st.selectbox("Backtesting Resolution", options=["1m", "3m", "5m", "15m", "30m", "1h", "1s"], index=0)
    with c4:
        trade_cost = st.number_input("Trade Cost (%)", min_value=0.0, value=0.06, step=0.01, format="%.2f")
    with c5:
        run_backtesting = st.button("Run Backtesting")

    if run_backtesting:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        backtesting_results = backend_api_client.run_backtesting(
            start_time=int(start_datetime.timestamp()) * 1000,
            end_time=int(end_datetime.timestamp()) * 1000,
            backtesting_resolution=backtesting_resolution,
            trade_cost=trade_cost / 100,
            config=inputs,
        )
        if len(backtesting_results["processed_data"]) == 0:
            st.error("No trades were executed during the backtesting period.")
            return None
        if len(backtesting_results["executors"]) == 0:
            st.error("No executors were found during the backtesting period.")
            return None
        return backtesting_results
