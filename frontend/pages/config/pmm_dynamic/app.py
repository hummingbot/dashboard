import streamlit as st
from plotly.subplots import make_subplots

from backend.services.backend_api_client import BackendAPIClient
from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from frontend.components.save_config import render_save_config

# Import submodules
from frontend.components.backtesting import backtesting_section
from frontend.pages.config.pmm_dynamic.user_inputs import user_inputs
from frontend.pages.config.utils import get_max_records, get_candles
from frontend.st_utils import initialize_st_page
from frontend.visualization.backtesting import create_backtesting_figure
from frontend.visualization.candles import get_candlestick_trace
from frontend.visualization.executors_distribution import create_executors_distribution_traces
from frontend.visualization.backtesting_metrics import render_backtesting_metrics, render_close_types, \
    render_accuracy_metrics
from frontend.visualization.indicators import get_macd_traces
from frontend.visualization.utils import add_traces_to_fig

# Initialize the Streamlit page
initialize_st_page(title="PMM Dynamic", icon="👩‍🏫")
backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)

# Page content
st.text("This tool will let you create a config for PMM Dynamic, backtest and upload it to the Backend API.")
# Get user inputs
inputs = user_inputs()
st.write("### Visualizing MACD and NATR indicators for PMM Dynamic")
st.text("The MACD is used to shift the mid price and the NATR to make the spreads dynamic. "
        "In the order distributions graph, we are going to see the values of the orders affected by the average NATR")
days_to_visualize = st.number_input("Days to Visualize", min_value=1, max_value=365, value=7)
max_records = get_max_records(days_to_visualize, inputs["interval"])
# Load candle data
candles = get_candles(connector_name=inputs["candles_connector"], trading_pair=inputs["candles_trading_pair"], interval=inputs["interval"], max_records=max_records)
# Create a subplot with 2 rows
fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                    vertical_spacing=0.02, subplot_titles=('Candlestick with Bollinger Bands', 'Volume', "MACD"),
                    row_heights=[0.8, 0.2, 0.2, 0.2])
add_traces_to_fig(fig, [get_candlestick_trace(candles)], row=1, col=1)
add_traces_to_fig(fig, get_macd_traces(df=candles, macd_fast=inputs["macd_fast"], macd_slow=inputs["macd_slow"], macd_signal=inputs["macd_signal"]), row=2, col=1)



fig = create_executors_distribution_traces(inputs)
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
render_save_config("pmm_simple", inputs)
