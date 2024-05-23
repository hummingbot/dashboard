import streamlit as st

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from backend.services.backend_api_client import BackendAPIClient
from frontend.components.backtesting import backtesting_section
from frontend.components.dca_distribution import get_dca_distribution_inputs
from frontend.components.save_config import render_save_config
from frontend.pages.config.dman_maker_v2.user_inputs import user_inputs
from frontend.st_utils import initialize_st_page
from frontend.visualization.backtesting import create_backtesting_figure
from frontend.visualization.backtesting_metrics import render_backtesting_metrics, render_accuracy_metrics, \
    render_close_types
from frontend.visualization.dca_builder import create_dca_graph
from frontend.visualization.executors_distribution import create_executors_distribution_traces

# Initialize the Streamlit page
initialize_st_page(title="D-Man Maker V2", icon="🧙‍♂️")
backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)


# Page content
st.text("This tool will let you create a config for D-Man Maker V2 and upload it to the BackendAPI.")
st.write("---")

inputs = user_inputs()
with st.expander("Executor Distribution:", expanded=True):
    fig = create_executors_distribution_traces(inputs["buy_spreads"], inputs["sell_spreads"], inputs["buy_amounts_pct"], inputs["sell_amounts_pct"], inputs["total_amount_quote"])
    st.plotly_chart(fig, use_container_width=True)

dca_inputs = get_dca_distribution_inputs()

st.write("### Visualizing DCA Distribution for specific Executor Level")
st.write("---")
buy_order_levels = len(inputs["buy_spreads"])
sell_order_levels = len(inputs["sell_spreads"])

buy_executor_levels = [f"BUY_{i}" for i in range(buy_order_levels)]
sell_executor_levels = [f"SELL_{i}" for i in range(sell_order_levels)]
c1, c2 = st.columns(2)
with c1:
    executor_level = st.selectbox("Executor Level", buy_executor_levels + sell_executor_levels)
    side, level = executor_level.split("_")
    if side == "BUY":
        dca_amount = inputs["buy_amounts_pct"][int(level)] * inputs["total_amount_quote"]
    else:
        dca_amount = inputs["sell_amounts_pct"][int(level)] * inputs["total_amount_quote"]
with c2:
    st.metric(label="DCA Amount", value=f"{dca_amount:.2f}")
fig = create_dca_graph(dca_inputs, dca_amount)
st.plotly_chart(fig, use_container_width=True)

# Combine inputs and dca_inputs into final config
config = {**inputs, **dca_inputs}
bt_results = backtesting_section(config, backend_api_client)
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
render_save_config("dman_maker_v2", config)