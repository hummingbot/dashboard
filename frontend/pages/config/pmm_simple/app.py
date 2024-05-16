import streamlit as st
from backend.services.backend_api_client import BackendAPIClient
from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT

# Import submodules
from frontend.pages.config.pmm_simple.user_inputs import user_inputs
from frontend.pages.config.pmm_simple import calculate_orders
from frontend.data_viz.visualization import visualize_orders
from frontend.pages.config.pmm_simple import handle_config
from frontend.components.backtesting import backtesting_section
from frontend.st_utils import initialize_st_page

# Initialize the Streamlit page
initialize_st_page(title="PMM Simple", icon="👨‍🏫")
backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)

# Page content
st.text("This tool will let you create a config for PMM Simple and upload it to the BackendAPI.")
st.write("---")

# Get user inputs
inputs = user_inputs()

# Calculate orders based on inputs
order_data = calculate_orders(inputs)

# Visualize orders
visualize_orders(order_data)

# Handle configuration
handle_config(inputs, order_data, backend_api_client)

st.write("---")
st.write("### Backtesting")
backtesting_section(inputs, backend_api_client)
