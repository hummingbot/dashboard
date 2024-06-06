import streamlit as st
from plotly.subplots import make_subplots

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from backend.services.backend_api_client import BackendAPIClient
from frontend.components.backtesting import backtesting_section
from frontend.components.config_loader import get_default_config_loader
from frontend.components.save_config import render_save_config
from frontend.pages.config.supertrend_v1.user_inputs import user_inputs
from frontend.pages.config.utils import get_candles, get_max_records
from frontend.st_utils import initialize_st_page, get_backend_api_client
from frontend.visualization import theme
from frontend.visualization.backtesting import create_backtesting_figure
from frontend.visualization.backtesting_metrics import render_backtesting_metrics, render_accuracy_metrics, \
    render_close_types
from frontend.visualization.candles import get_candlestick_trace
from frontend.visualization.indicators import get_volume_trace, get_supertrend_traces
from frontend.visualization.signals import get_supertrend_v1_signal_traces
from frontend.visualization.utils import add_traces_to_fig

# Initialize the Streamlit page
initialize_st_page(title="SuperTrend V1", icon="📊", initial_sidebar_state="expanded")
backend_api_client = get_backend_api_client()

get_default_config_loader("supertrend_v1")
# User inputs
inputs = user_inputs()
st.session_state["default_config"].update(inputs)

st.write("### Visualizing Supertrend Trading Signals")
days_to_visualize = st.number_input("Days to Visualize", min_value=1, max_value=365, value=3)
# Load candle data
candles = get_candles(connector_name=inputs["candles_connector"], trading_pair=inputs["candles_trading_pair"], interval=inputs["interval"], days=days_to_visualize)

# Create a subplot with 2 rows
fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    vertical_spacing=0.02, subplot_titles=('Candlestick with Bollinger Bands', 'Volume', "MACD"),
                    row_heights=[0.8, 0.2])
add_traces_to_fig(fig, [get_candlestick_trace(candles)], row=1, col=1)
add_traces_to_fig(fig, get_supertrend_traces(candles, inputs["length"], inputs["multiplier"]), row=1, col=1)
add_traces_to_fig(fig, get_supertrend_v1_signal_traces(candles, inputs["length"], inputs["multiplier"], inputs["percentage_threshold"]), row=1, col=1)
add_traces_to_fig(fig, [get_volume_trace(candles)], row=2, col=1)

layout_settings = theme.get_default_layout()
layout_settings["showlegend"] = False
fig.update_layout(**layout_settings)
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
render_save_config(st.session_state["default_config"]["id"], st.session_state["default_config"])
