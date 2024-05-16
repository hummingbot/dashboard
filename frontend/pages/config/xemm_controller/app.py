import streamlit as st
import plotly.graph_objects as go
import yaml

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from backend.services.backend_api_client import BackendAPIClient
from frontend.st_utils import initialize_st_page

# Initialize the Streamlit page
initialize_st_page(title="XEMM Multiple Levels", icon="⚡️")

# Page content
st.text("This tool will let you create a config for XEMM Controller and upload it to the BackendAPI.")
st.write("---")
c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])

with c1:
    maker_connector = st.text_input("Maker Connector", value="kucoin")
    maker_trading_pair = st.text_input("Maker Trading Pair", value="LBR-USDT")
with c2:
    taker_connector = st.text_input("Taker Connector", value="okx")
    taker_trading_pair = st.text_input("Taker Trading Pair", value="LBR-USDT")
with c3:
    min_profitability = st.number_input("Min Profitability (%)", value=0.2, step=0.01) / 100
    max_profitability = st.number_input("Max Profitability (%)", value=1.0, step=0.01) / 100
with c4:
    buy_maker_levels = st.number_input("Buy Maker Levels", value=1, step=1)
    buy_targets_amounts = []
    c41, c42 = st.columns([1, 1])
    for i in range(buy_maker_levels):
        with c41:
            target_profitability = st.number_input(f"Target Profitability {i+1} B% ", value=0.3, step=0.01)
        with c42:
            amount = st.number_input(f"Amount {i+1}B Quote", value=10, step=1)
        buy_targets_amounts.append([target_profitability / 100, amount])
with c5:
    sell_maker_levels = st.number_input("Sell Maker Levels", value=1, step=1)
    sell_targets_amounts = []
    c51, c52 = st.columns([1, 1])
    for i in range(sell_maker_levels):
        with c51:
            target_profitability = st.number_input(f"Target Profitability {i+1}S %", value=0.3, step=0.001)
        with c52:
            amount = st.number_input(f"Amount {i+1} S Quote", value=10, step=1)
        sell_targets_amounts.append([target_profitability / 100, amount])


def create_order_graph(order_type, targets, min_profit, max_profit):
    # Create a figure
    fig = go.Figure()

    # Convert profit targets to percentage for x-axis and prepare data for bar chart
    x_values = [t[0] * 100 for t in targets]  # Convert to percentage
    y_values = [t[1] for t in targets]
    x_labels = [f"{x:.2f}%" for x in x_values]  # Format x labels as strings with percentage sign

    # Add bar plot for visualization of targets
    fig.add_trace(go.Bar(
        x=x_labels,
        y=y_values,
        width=0.01,
        name=f'{order_type.capitalize()} Targets',
        marker=dict(color='gold')
    ))

    # Convert min and max profitability to percentages for reference lines
    min_profit_percent = min_profit * 100
    max_profit_percent = max_profit * 100

    # Add vertical lines for min and max profitability
    fig.add_shape(type="line",
                  x0=min_profit_percent, y0=0, x1=min_profit_percent, y1=max(y_values, default=10),
                  line=dict(color="red", width=2),
                  name='Min Profitability')
    fig.add_shape(type="line",
                  x0=max_profit_percent, y0=0, x1=max_profit_percent, y1=max(y_values, default=10),
                  line=dict(color="red", width=2),
                  name='Max Profitability')

    # Update layouts with x-axis starting at 0
    fig.update_layout(
        title=f"{order_type.capitalize()} Order Distribution with Profitability Targets",
        xaxis=dict(
            title="Profitability (%)",
            range=[0, max(max(x_values + [min_profit_percent, max_profit_percent]) + 0.1, 1)]  # Adjust range to include a buffer
        ),
        yaxis=dict(
            title="Order Amount"
        ),
        height=400,
        width=600
    )

    return fig

# Use the function for both buy and sell orders
buy_order_fig = create_order_graph('buy', buy_targets_amounts, min_profitability, max_profitability)
sell_order_fig = create_order_graph('sell', sell_targets_amounts, min_profitability, max_profitability)

# Display the Plotly graphs in Streamlit
st.plotly_chart(buy_order_fig, use_container_width=True)
st.plotly_chart(sell_order_fig, use_container_width=True)

# Display in Streamlit
c1, c2, c3 = st.columns([2, 2, 1])
with c1:
    config_base = st.text_input("Config Base", value=f"xemm_{maker_connector}_{taker_connector}-{maker_trading_pair.split('-')[0]}")
with c2:
    config_tag = st.text_input("Config Tag", value="1.1")

id = f"{config_base}-{config_tag}"
config = {
        "id": id.lower(),
        "controller_name": "xemm_multiple_levels",
        "controller_type": "generic",
        "maker_connector": maker_connector,
        "maker_trading_pair": maker_trading_pair,
        "taker_connector": taker_connector,
        "taker_trading_pair": taker_trading_pair,
        "min_profitability": min_profitability,
        "max_profitability": max_profitability,
        "buy_levels_targets_amount": buy_targets_amounts,
        "sell_levels_targets_amount": sell_targets_amounts
}
yaml_config = yaml.dump(config, default_flow_style=False)

with c3:
    download_config = st.download_button(
        label="Download YAML",
        data=yaml_config,
        file_name=f'{id.lower()}.yml',
        mime='text/yaml'
    )
    upload_config_to_backend = st.button("Upload Config to BackendAPI")


if upload_config_to_backend:
    backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)
    backend_api_client.add_controller_config(config)
    st.success("Config uploaded successfully!")