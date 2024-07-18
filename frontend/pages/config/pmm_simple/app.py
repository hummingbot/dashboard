import streamlit as st

from frontend.components.backtesting import backtesting_section
from frontend.components.config_loader import get_default_config_loader
from frontend.components.save_config import render_save_config

# Import submodules
from frontend.pages.config.pmm_simple.user_inputs import user_inputs
from frontend.st_utils import get_backend_api_client, initialize_st_page
from frontend.visualization.backtesting import create_backtesting_figure
from frontend.visualization.backtesting_metrics import render_accuracy_metrics, render_backtesting_metrics, render_close_types
from frontend.visualization.executors_distribution import create_executors_distribution_traces

# Initialize the Streamlit page
initialize_st_page(title="PMM Simple", icon="👨‍🏫")
backend_api_client = get_backend_api_client()

# Page content
st.text("This tool will let you create a config for PMM Simple, backtest and upload it to the Backend API.")
get_default_config_loader("pmm_simple")

inputs = user_inputs()

st.session_state["default_config"].update(inputs)
with st.expander("Executor Distribution:", expanded=True):
    fig = create_executors_distribution_traces(inputs["buy_spreads"], inputs["sell_spreads"], inputs["buy_amounts_pct"],
                                               inputs["sell_amounts_pct"], inputs["total_amount_quote"])
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
