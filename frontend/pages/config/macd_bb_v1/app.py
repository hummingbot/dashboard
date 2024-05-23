import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yaml
from plotly.subplots import make_subplots

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from backend.services.backend_api_client import BackendAPIClient
from frontend.components.backtesting import backtesting_section
from frontend.components.save_config import render_save_config
from frontend.pages.config.macd_bb_v1.user_inputs import user_inputs
from frontend.pages.config.utils import get_candles, get_max_records
from frontend.st_utils import initialize_st_page
from frontend.visualization import theme
from frontend.visualization.backtesting import create_backtesting_figure
from frontend.visualization.backtesting_metrics import render_backtesting_metrics, render_accuracy_metrics, \
    render_close_types
from frontend.visualization.candles import get_candlestick_trace
from frontend.visualization.indicators import get_bbands_traces, get_volume_trace, get_macd_traces
from frontend.visualization.signals import get_macdbb_v1_signal_traces
from frontend.visualization.utils import add_traces_to_fig

# Initialize the Streamlit page
initialize_st_page(title="MACD_BB V1", icon="📊", initial_sidebar_state="expanded")
backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)


# User inputs
inputs = user_inputs()

st.write("### Visualizing MACD Bollinger Trading Signals")
days_to_visualize = st.number_input("Days to Visualize", min_value=1, max_value=365, value=3)
# Load candle data
candles = get_candles(connector_name=inputs["candles_connector"], trading_pair=inputs["candles_trading_pair"], interval=inputs["interval"], days=days_to_visualize)

# Create a subplot with 2 rows
fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    vertical_spacing=0.02, subplot_titles=('Candlestick with Bollinger Bands', 'Volume', "MACD"),
                    row_heights=[0.8, 0.2])
add_traces_to_fig(fig, [get_candlestick_trace(candles)], row=1, col=1)
add_traces_to_fig(fig, get_bbands_traces(candles, inputs["bb_length"], inputs["bb_std"]), row=1, col=1)
add_traces_to_fig(fig, get_macdbb_v1_signal_traces(df=candles, bb_length=inputs["bb_length"], bb_std=inputs["bb_std"],
                                                   bb_long_threshold=inputs["bb_long_threshold"], bb_short_threshold=inputs["bb_short_threshold"],
                                                   macd_fast=inputs["macd_fast"], macd_slow=inputs["macd_slow"], macd_signal=inputs["macd_signal"]), row=1, col=1)
add_traces_to_fig(fig, get_macd_traces(df=candles, macd_fast=inputs["macd_fast"], macd_slow=inputs["macd_slow"], macd_signal=inputs["macd_signal"]), row=2, col=1)

fig.update_layout(**theme.get_default_layout())
# Use Streamlit's functionality to display the plot
st.plotly_chart(fig, use_container_width=True)
bt_results = backtesting_section(inputs, backend_api_client)
if bt_results:
    fig = create_backtesting_figure(
        df=bt_results["processed_data"],
        executors=bt_results["executors"],
        config=inputs)
    c1, c2 = st.columns([0.9, 0.1])
    with c1:
        render_backtesting_metrics(bt_results["results"])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        render_accuracy_metrics(bt_results["results"])
        st.write("---")
        render_close_types(bt_results["results"])
st.write("---")
render_save_config("bollinger_v1", inputs)
