import datetime

import pandas as pd
import streamlit as st

from frontend.st_utils import get_backend_api_client


def get_max_records(days_to_download: int, interval: str) -> int:
    conversion = {"s": 1 / 60, "m": 1, "h": 60, "d": 1440}
    unit = interval[-1]
    quantity = int(interval[:-1])
    return int(days_to_download * 24 * 60 / (quantity * conversion[unit]))


@st.cache_data
def get_candles(connector_name="binance", trading_pair="BTC-USDT", interval="1m", days=7):
    backend_client = get_backend_api_client()
    
    # Use the market_data.get_candles_last_days method
    candles = backend_client.market_data.get_candles_last_days(
        connector_name=connector_name,
        trading_pair=trading_pair,
        days=days,
        interval=interval
    )
    
    # Convert the response to DataFrame (response is a list of candles)
    df = pd.DataFrame(candles)
    if not df.empty and 'timestamp' in df.columns:
        df.index = pd.to_datetime(df.timestamp, unit='s')
    return df
