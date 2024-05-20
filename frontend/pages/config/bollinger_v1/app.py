from datetime import datetime

import streamlit as st
import pandas as pd
import yaml
import pandas_ta as ta  # noqa: F401

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from backend.services.backend_api_client import BackendAPIClient
from frontend.pages.config.utils import get_max_records
from frontend.st_utils import initialize_st_page
from frontend.pages.config.bollinger_v1.user_inputs import user_inputs
from plotly.subplots import make_subplots

from frontend.visualization.candles import get_candlestick_trace
from frontend.visualization.indicators import get_bbands_traces
from frontend.visualization.utils import add_traces_to_fig

# Initialize the Streamlit page
initialize_st_page(title="Bollinger V1", icon="📈", initial_sidebar_state="expanded")


@st.cache_data
def get_candles(connector_name="binance", trading_pair="BTC-USDT", interval="1m", max_records=5000):
    backend_client = BackendAPIClient(BACKEND_API_HOST, BACKEND_API_PORT)
    return pd.DataFrame(backend_client.get_real_time_candles(connector_name, trading_pair, interval, max_records))



st.text("This tool will let you create a config for Bollinger V1 and visualize the strategy.")
st.write("---")

inputs = user_inputs()

st.write("### Visualizing Bollinger Bands and Trading Signals")
days_to_visualize = st.number_input("Days to Visualize", min_value=1, max_value=365, value=7)
max_records = get_max_records(days_to_visualize, inputs["interval"])
# Load candle data
candles = get_candles(connector_name=inputs["candles_connector"], trading_pair=inputs["candles_trading_pair"], interval=inputs["interval"], max_records=max_records)

# Create a subplot with 2 rows
fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    vertical_spacing=0.02, subplot_titles=('Candlestick with Bollinger Bands', 'Trading Signals'),
                    row_heights=[0.7, 0.3])

fig.add_trace(get_candlestick_trace(candles), row=1, col=1)
add_traces_to_fig(fig, get_bbands_traces(candles, inputs["bb_length"], inputs["bb_std"]), row=1, col=1)


# Use Streamlit's functionality to display the plot
st.plotly_chart(fig, use_container_width=True)
