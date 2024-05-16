import streamlit as st
from backend.services.backend_api_client import BackendAPIClient
from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT

# Import submodules
from frontend.pages.config.pmm_simple.user_inputs import user_inputs
from frontend.components.backtesting import backtesting_section
from frontend.st_utils import initialize_st_page
from frontend.visualization.backtesting import create_backtesting_figure
from frontend.visualization.executors_distribution import create_executors_distribution_traces

# Initialize the Streamlit page
initialize_st_page(title="PMM Simple", icon="👨‍🏫")
backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)

# Page content
st.text("This tool will let you create a config for PMM Simple, backtest and upload it to the Backend API.")
st.write("---")

# Get user inputs
inputs = user_inputs()
st.write(inputs)
fig = create_executors_distribution_traces(inputs)
st.plotly_chart(fig, use_container_width=True)

st.write("### Backtesting")
bt_results = backtesting_section(inputs, backend_api_client)
if bt_results:
    fig = create_backtesting_figure(
        df=bt_results["processed_data"],
        executors=bt_results["executors"],
        config=inputs)
    st.plotly_chart(fig, use_container_width=True)