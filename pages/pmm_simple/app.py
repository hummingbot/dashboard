import pandas as pd
import streamlit as st
from hummingbot.connector.connector_base import OrderType
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from decimal import Decimal
import yaml

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from utils.backend_api_client import BackendAPIClient
from utils.st_utils import initialize_st_page
from ui_components.st_inputs import normalize, distribution_inputs, get_distribution

# Initialize the Streamlit page
initialize_st_page(title="PMM Simple", icon="👨‍🏫", initial_sidebar_state="collapsed")

# Page content
st.text("This tool will let you create a config for PMM Simple and upload it to the BackendAPI.")
st.write("---")

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

with c1:
    connector = st.text_input("Connector", value="binance_perpetual")
with c2:
    trading_pair = st.text_input("Trading Pair", value="WLD-USDT")
with c3:
    total_amount_quote = st.number_input("Total amount of quote", value=1000)
with c4:
    leverage = st.number_input("Leverage", value=20)
    position_mode = st.selectbox("Position Mode", ("HEDGE", "ONEWAY"), index=0)
with c5:
    executor_refresh_time = st.number_input("Refresh Time (minutes)", value=3)
    cooldown_time = st.number_input("Cooldown Time (minutes)", value=3)
with c6:
    sl = st.number_input("Stop Loss (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.1)
    tp = st.number_input("Take Profit (%)", min_value=0.0, max_value=100.0, value=3.0, step=0.1)
    take_profit_order_type = st.selectbox("Take Profit Order Type", (OrderType.LIMIT, OrderType.MARKET))
with c7:
    ts_ap = st.number_input("Trailing Stop Activation Price (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1)
    ts_delta = st.number_input("Trailing Stop Delta (%)", min_value=0.0, max_value=100.0, value=0.3, step=0.1)
    time_limit = st.number_input("Time Limit (minutes)", min_value=0, value=60 * 6)




# Executors configuration
col_buy, col_sell = st.columns(2)
with col_buy:
    st.header("Buy Order Settings")
    buy_order_levels = st.number_input("Number of Buy Order Levels", min_value=1, value=2)
with col_sell:
    st.header("Sell Order Settings")
    sell_order_levels = st.number_input("Number of Sell Order Levels", min_value=1, value=2)

col_buy_spreads, col_buy_amounts, col_sell_spreads, col_sell_amounts = st.columns(4)

# Inputs for buy orders
with col_buy_spreads:
    buy_spread_dist_type, buy_spread_start, buy_spread_base, buy_spread_scaling, buy_spread_step, buy_spread_ratio, buy_manual_spreads = distribution_inputs(
        col_buy_spreads, "Spread", buy_order_levels)
with col_buy_amounts:
    buy_amount_dist_type, buy_amount_start, buy_amount_base, buy_amount_scaling, buy_amount_step, buy_amount_ratio, buy_manual_amounts = distribution_inputs(
        col_buy_amounts, "Amount", buy_order_levels)
with col_sell_spreads:
    sell_spread_dist_type, sell_spread_start, sell_spread_base, sell_spread_scaling, sell_spread_step, sell_spread_ratio, sell_manual_spreads = distribution_inputs(
        col_sell_spreads, "Spread", sell_order_levels)
with col_sell_amounts:
    sell_amount_dist_type, sell_amount_start, sell_amount_base, sell_amount_scaling, sell_amount_step, sell_amount_ratio, sell_manual_amounts = distribution_inputs(
        col_sell_amounts, "Amount", sell_order_levels)

buy_spread_distributions = get_distribution(buy_spread_dist_type, buy_order_levels, buy_spread_start, buy_spread_base,
                                            buy_spread_scaling, buy_spread_step, buy_spread_ratio, buy_manual_spreads)
sell_spread_distributions = get_distribution(sell_spread_dist_type, sell_order_levels, sell_spread_start,
                                             sell_spread_base, sell_spread_scaling, sell_spread_step, sell_spread_ratio,
                                             sell_manual_spreads)
buy_amount_distributions = normalize(
    get_distribution(buy_amount_dist_type, buy_order_levels, buy_amount_start, buy_amount_base, buy_amount_scaling,
                     buy_amount_step, buy_amount_ratio, buy_manual_amounts))
sell_amount_distributions = normalize(
    get_distribution(sell_amount_dist_type, sell_order_levels, sell_amount_start, sell_amount_base, sell_amount_scaling,
                     sell_amount_step, sell_amount_ratio, sell_manual_amounts))

all_orders_amount_normalized = normalize(buy_amount_distributions + sell_amount_distributions)
buy_order_amounts_quote = [amount * total_amount_quote for amount in
                           all_orders_amount_normalized[:buy_order_levels]]
sell_order_amounts_quote = [amount * total_amount_quote for amount in
                            all_orders_amount_normalized[buy_order_levels:]]

# Initialize your figure with a dark theme
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.update_layout(
    template="plotly_dark",
    plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent background
    paper_bgcolor='rgba(0, 0, 0, 0.1)',  # Lighter shade for the paper
    title="Market Maker Order Distribution",
    xaxis_title="Spread (%)",
    yaxis_title="Amount (Quote)",
    legend_title="Order Type",
    font=dict(color='white', size=12)  # Consistent font color and size
)

# Define colors for buy and sell orders
colors = {
    'buy': '#32CD32',  # Green for buy orders
    'sell': '#FF6347'  # Tomato red for sell orders
}

# Add traces for buy and sell orders
# Buy orders on the negative side of x-axis
fig.add_trace(go.Bar(
    x=[-dist for dist in buy_spread_distributions],
    y=buy_order_amounts_quote,
    name='Buy Orders',
    marker_color=colors['buy'],
    width=[0.2] * buy_order_levels  # Adjust the width of the bars as needed
), secondary_y=False)

# Sell orders on the positive side of x-axis
fig.add_trace(go.Bar(
    x=sell_spread_distributions,
    y=sell_order_amounts_quote,
    name='Sell Orders',
    marker_color=colors['sell'],
    width=[0.2] * buy_order_levels  # Adjust the width of the bars as needed

), secondary_y=False)

# Annotations can be added for each bar to display the value on top
for i, value in enumerate(buy_order_amounts_quote):
    fig.add_annotation(
        x=-buy_spread_distributions[i],
        y=value + 10,  # Offset the text slightly above the bar
        text=str(round(value, 2)),
        showarrow=False,
        font=dict(color=colors['buy'], size=10)
    )

for i, value in enumerate(sell_order_amounts_quote):
    fig.add_annotation(
        x=sell_spread_distributions[i],
        y=value + 10,  # Offset the text slightly above the bar
        text=str(round(value, 2)),
        showarrow=False,
        font=dict(color=colors['sell'], size=10)
    )

# Optional: Add horizontal line or extra annotations if needed
# e.g., for average, threshold, or specific markers

# Update the layout to make it responsive and visually appealing
fig.update_layout(
    height=600,
    width=800,
    margin=dict(l=20, r=20, t=50, b=20)
)

# Display the figure in Streamlit
st.plotly_chart(fig, use_container_width=True)

# Create DataFrame for Buy Orders
buy_orders_df = pd.DataFrame({
    "Level": range(1, buy_order_levels + 1),
    "Spread (%)": [-dist for dist in buy_spread_distributions],
    "Amount (Quote)": buy_order_amounts_quote,
    "Take Profit ($)": [float(amount) * (tp / 100) for amount in buy_order_amounts_quote],
    "Stop Loss ($)": [float(amount) * (sl / 100) for amount in buy_order_amounts_quote],
    "Min Trailing Stop ($)": [float(amount) * ((ts_ap - ts_delta) / 100) for amount in buy_order_amounts_quote],
    "TP/SL Ratio": [tp / sl] * buy_order_levels,
    "TS/SL Ratio": [(ts_ap - ts_delta) / sl] * buy_order_levels,
})

# Create DataFrame for Sell Orders
sell_orders_df = pd.DataFrame({
    "Level": range(1, sell_order_levels + 1),
    "Spread (%)": [dist for dist in sell_spread_distributions],
    "Amount (Quote)": sell_order_amounts_quote,
    "Take Profit ($)": [float(amount) * (tp / 100) for amount in sell_order_amounts_quote],
    "Stop Loss ($)": [float(amount) * (sl / 100) for amount in sell_order_amounts_quote],
    "Min Trailing Stop ($)": [float(amount) * ((ts_ap - ts_delta) / 100) for amount in sell_order_amounts_quote],
    "TP/SL Ratio": [tp / sl] * buy_order_levels,
    "TS/SL Ratio": [(ts_ap - ts_delta) / sl] * buy_order_levels,
})

# Display the DataFrames in Streamlit
st.write("Buy Orders:")
st.dataframe(buy_orders_df)
st.write("Sell Orders:")
st.dataframe(sell_orders_df)

c1, c2, c3 = st.columns([2, 2, 1])
with c1:
    config_base = st.text_input("Config Base", value=f"pmm_simple-{connector}-{trading_pair.split('-')[0]}")
with c2:
    config_tag = st.text_input("Config Tag", value="1.1")

id = f"{config_base}-{config_tag}"
config = {
        "id": id.lower(),
        "controller_name": "pmm_simple",
        "controller_type": "market_making",
        "manual_kill_switch": None,
        "candles_config": [],
        "connector_name": connector,
        "trading_pair": trading_pair,
        "total_amount_quote": total_amount_quote,
        "buy_spreads": [Decimal(spread / 100) for spread in buy_spread_distributions],
        "sell_spreads": [Decimal(spread / 100) for spread in sell_spread_distributions],
        "buy_amounts_pct": buy_order_amounts_quote,
        "sell_amounts_pct": sell_order_amounts_quote,
        "executor_refresh_time": executor_refresh_time * 60,
        "cooldown_time": cooldown_time,
        "leverage": leverage,
        "position_mode": position_mode,
        "stop_loss": sl / 100,
        "take_profit": tp / 100,
        "time_limit": time_limit * 60,
        "take_profit_order_type": take_profit_order_type.value,
        "trailing_stop": {
            "activation_price": ts_ap / 100,
            "trailing_delta": ts_delta / 100},
        "top_executor_refresh_time": None,
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