import streamlit as st
from backend.services.backend_api_client import BackendAPIClient
from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from frontend.components.save_config import render_save_config

# Import submodules
from frontend.pages.config.pmm_simple.user_inputs import user_inputs
from frontend.components.backtesting import backtesting_section
from frontend.st_utils import initialize_st_page
from frontend.visualization.backtesting import create_backtesting_figure
from frontend.visualization.executors_distribution import create_executors_distribution_traces
from frontend.visualization.backtesting_metrics import render_backtesting_metrics, render_close_types, \
    render_accuracy_metrics

# Initialize the Streamlit page
initialize_st_page(title="PMM Simple", icon="👨‍🏫")
backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)

# Page content
st.text("This tool will let you create a config for PMM Simple, backtest and upload it to the Backend API.")
# Get user inputs
inputs = user_inputs()
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
