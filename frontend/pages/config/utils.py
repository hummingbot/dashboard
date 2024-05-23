import datetime

import streamlit as st
import pandas as pd

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from backend.services.backend_api_client import BackendAPIClient


def get_max_records(days_to_download: int, interval: str) -> int:
    conversion = {"s": 1 / 60, "m": 1, "h": 60, "d": 1440}
    unit = interval[-1]
    quantity = int(interval[:-1])
    return int(days_to_download * 24 * 60 / (quantity * conversion[unit]))


@st.cache_data
def get_candles(connector_name="binance", trading_pair="BTC-USDT", interval="1m", days=7):
    backend_client = BackendAPIClient(BACKEND_API_HOST, BACKEND_API_PORT)
    end_time = datetime.datetime.now() - datetime.timedelta(minutes=15)
    start_time = end_time - datetime.timedelta(days=days)

    df = pd.DataFrame(backend_client.get_historical_candles(connector_name, trading_pair, interval,
                                                            start_time=int(start_time.timestamp() * 1000),
                                                            end_time=int(end_time.timestamp() * 1000)))
    df.index = pd.to_datetime(df.timestamp, unit='ms')
    return df

