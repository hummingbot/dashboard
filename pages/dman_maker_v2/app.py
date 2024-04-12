from math import exp
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from decimal import Decimal
import yaml

from utils.backend_api_client import BackendAPIClient
from utils.st_utils import initialize_st_page
from hummingbot.smart_components.utils.distributions import Distributions


def normalize(values):
    total = sum(values)
    return [Decimal(val / total) for val in values]


def distribution_inputs(column, dist_type_name, levels=3):
    if dist_type_name == "Spread":
        dist_type = column.selectbox(
            f"Type of {dist_type_name} Distribution",
            ("Manual", "GeoCustom", "Geometric", "Fibonacci", "Logarithmic", "Arithmetic"),
            key=f"{column}_{dist_type_name.lower()}_dist_type",
            # Set the default value
        )
    else:
        dist_type = column.selectbox(
            f"Type of {dist_type_name} Distribution",
            ("Manual", "Geometric", "Fibonacci", "Logarithmic", "Arithmetic"),
            key=f"{column}_{dist_type_name.lower()}_dist_type",
            # Set the default value
        )
    base, scaling_factor, step, ratio, manual_values = None, None, None, None, None

    if dist_type != "Manual":
        start = column.number_input(f"{dist_type_name} Start Value", value=1.0,
                                    key=f"{column}_{dist_type_name.lower()}_start")
        if dist_type == "Logarithmic":
            base = column.number_input(f"{dist_type_name} Log Base", value=exp(1),
                                       key=f"{column}_{dist_type_name.lower()}_base")
            scaling_factor = column.number_input(f"{dist_type_name} Scaling Factor", value=2.0,
                                                 key=f"{column}_{dist_type_name.lower()}_scaling")
        elif dist_type == "Arithmetic":
            step = column.number_input(f"{dist_type_name} Step", value=0.1,
                                       key=f"{column}_{dist_type_name.lower()}_step")
        elif dist_type == "Geometric":
            ratio = column.number_input(f"{dist_type_name} Ratio", value=2.0,
                                        key=f"{column}_{dist_type_name.lower()}_ratio")
        elif dist_type == "GeoCustom":
            ratio = column.number_input(f"{dist_type_name} Ratio", value=2.0,
                                        key=f"{column}_{dist_type_name.lower()}_ratio")
    else:
        manual_values = [column.number_input(f"{dist_type_name} for level {i + 1}", value=i + 1.0,
                                             key=f"{column}_{dist_type_name.lower()}_{i}") for i in range(levels)]
        start = None  # As start is not relevant for Manual type

    return dist_type, start, base, scaling_factor, step, ratio, manual_values


def get_distribution(dist_type, n_levels, start, base=None, scaling_factor=None, step=None, ratio=None,
                     manual_values=None):
    if dist_type == "Manual":
        return manual_values
    elif dist_type == "Linear":
        return Distributions.linear(n_levels, start, start + ts_ap)
    elif dist_type == "Fibonacci":
        return Distributions.fibonacci(n_levels, start)
    elif dist_type == "Logarithmic":
        return Distributions.logarithmic(n_levels, base, scaling_factor, start)
    elif dist_type == "Arithmetic":
        return Distributions.arithmetic(n_levels, start, step)
    elif dist_type == "Geometric":
        return Distributions.geometric(n_levels, start, ratio)
    elif dist_type == "GeoCustom":
        return [Decimal("0")] + Distributions.geometric(n_levels - 1, start, ratio)


# Initialize the Streamlit page
initialize_st_page(title="D-Man Maker V2", icon="🧙‍♂️", initial_sidebar_state="collapsed")

# Page content
st.text("This tool will let you create a config for D-Man Maker V2 and upload it to the BackendAPI.")
st.write("---")

c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns(9)

with c1:
    connector = st.text_input("Connector", value="binance_perpetual")
with c2:
    trading_pair = st.text_input("Trading Pair", value="WLD-USDT")
with c3:
    leverage = st.number_input("Leverage", value=20)
with c4:
    total_amount_quote = st.number_input("Total amount of quote", value=1000)
with c5:
    position_mode = st.selectbox("Position Mode", ("HEDGE", "ONEWAY"), index=0)
with c6:
    cooldown_time = st.number_input("Cooldown Time", value=60)
with c7:
    executor_refresh_time = st.number_input("Refresh Time (minutes)", value=60)
with c8:
    top_executor_refresh_time = st.number_input("Top Refresh Time (seconds)", value=60)
with c9:
    executor_activation_bounds = st.number_input("Activation Bounds (%)", value=0.1)

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
buy_order_amounts_quote = [Decimal(amount * total_amount_quote) for amount in
                           all_orders_amount_normalized[:buy_order_levels]]
sell_order_amounts_quote = [Decimal(amount * total_amount_quote) for amount in
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

# Layout in columns
col_dca_quote, col_tp_sl, col_levels, col_spread_dist, col_amount_dist = st.columns([1, 1, 1, 2, 2])

buy_executor_levels = [f"BUY_{i}" for i in range(buy_order_levels)]
sell_executor_levels = [f"SELL_{i}" for i in range(sell_order_levels)]
with col_dca_quote:
    executor_level = st.selectbox("Executor Level", buy_executor_levels + sell_executor_levels)
    side, level = executor_level.split("_")
    if side == "BUY":
        dca_amount = buy_order_amounts_quote[int(level)]
    else:
        dca_amount = sell_order_amounts_quote[int(level)]
    st.write(f"DCA Amount: {dca_amount:.2f}")

with col_tp_sl:
    ts_ap = st.number_input("Trailing Stop Activation Price (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1)
    ts_delta = st.number_input("Trailing Stop Delta (%)", min_value=0.0, max_value=100.0, value=0.3, step=0.1)
    sl = st.number_input("Stop Loss (%)", min_value=0.0, max_value=100.0, value=3.0, step=0.1)

with col_levels:
    n_levels = st.number_input("Number of Levels", min_value=1, value=5)
    tp = st.number_input("Take Profit (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.1)
    time_limit = st.number_input("Time Limit (minutes)", min_value=0, value=60 * 6)

# Spread and Amount Distributions
spread_dist_type, spread_start, spread_base, spread_scaling, spread_step, spread_ratio, manual_spreads = distribution_inputs(
    col_spread_dist, "Spread", n_levels)
amount_dist_type, amount_start, amount_base, amount_scaling, amount_step, amount_ratio, manual_amounts = distribution_inputs(
    col_amount_dist, "Amount", n_levels)

spread_distribution = get_distribution(spread_dist_type, n_levels, spread_start, spread_base, spread_scaling,
                                       spread_step, spread_ratio, manual_spreads)
amount_distribution = normalize(
    get_distribution(amount_dist_type, n_levels, amount_start, amount_base, amount_scaling, amount_step, amount_ratio,
                     manual_amounts))
dca_order_amounts = [Decimal(amount_dist * dca_amount) for amount_dist in amount_distribution]
dca_spreads = [Decimal(spread - spread_distribution[0]) for spread in spread_distribution]

break_even_values = []
take_profit_values = []
for level in range(n_levels):
    dca_spreads_normalized = [Decimal(spread) + Decimal(0.01) for spread in dca_spreads[:level + 1]]
    amounts = dca_order_amounts[:level + 1]
    break_even = (sum([spread * amount for spread, amount in zip(dca_spreads_normalized, amounts)]) / sum(
        amounts)) - Decimal(0.01)
    break_even_values.append(break_even)
    take_profit_values.append(break_even - Decimal(ts_ap))

accumulated_amount = [sum(dca_order_amounts[:i + 1]) for i in range(len(dca_order_amounts))]


def calculate_unrealized_pnl(spreads, break_even_values, accumulated_amount):
    unrealized_pnl = []
    for i in range(len(spreads)):
        distance = abs(spreads[i] - break_even_values[i])
        pnl = accumulated_amount[i] * distance / 100  # PNL calculation
        unrealized_pnl.append(pnl)
    return unrealized_pnl


# Calculate unrealized PNL
cum_unrealized_pnl = calculate_unrealized_pnl(dca_spreads, break_even_values, accumulated_amount)

tech_colors = {
    'spread': '#00BFFF',  # Deep Sky Blue
    'break_even': '#FFD700',  # Gold
    'take_profit': '#32CD32',  # Green
    'order_amount': '#1E90FF',  # Dodger Blue
    'cum_amount': '#4682B4',  # Steel Blue
    'stop_loss': '#FF0000',  # Red
}

# Create Plotly figure with secondary y-axis and a dark theme
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.update_layout(template="plotly_dark")

# Update the Scatter Plots and Horizontal Lines
fig.add_trace(go.Scatter(x=list(range(len(dca_spreads))), y=dca_spreads, name='Spread (%)', mode='lines+markers',
                         line=dict(width=3, color=tech_colors['spread'])), secondary_y=False)
fig.add_trace(
    go.Scatter(x=list(range(len(break_even_values))), y=break_even_values, name='Break Even (%)', mode='lines+markers',
               line=dict(width=3, color=tech_colors['break_even'])), secondary_y=False)
fig.add_trace(go.Scatter(x=list(range(len(take_profit_values))), y=take_profit_values, name='Take Profit (%)',
                         mode='lines+markers', line=dict(width=3, color=tech_colors['take_profit'])), secondary_y=False)

# Add the new Bar Plot for Cumulative Unrealized PNL
fig.add_trace(go.Bar(
    x=list(range(len(cum_unrealized_pnl))),
    y=cum_unrealized_pnl,
    text=[f"{pnl:.2f}" for pnl in cum_unrealized_pnl],
    textposition='auto',
    textfont=dict(color='white', size=12),
    name='Cum Unrealized PNL',
    marker=dict(color='#FFA07A', opacity=0.6)  # Light Salmon color, adjust as needed
), secondary_y=True)

fig.add_trace(go.Bar(
    x=list(range(len(dca_order_amounts))),
    y=dca_order_amounts,
    text=[f"{amt:.2f}" for amt in dca_order_amounts],  # List comprehension to format text labels
    textposition='auto',
    textfont=dict(
        color='white',
        size=12
    ),
    name='Order Amount',
    marker=dict(color=tech_colors['order_amount'], opacity=0.5),
), secondary_y=True)

# Modify the Bar Plot for Accumulated Amount
fig.add_trace(go.Bar(
    x=list(range(len(accumulated_amount))),
    y=accumulated_amount,
    text=[f"{amt:.2f}" for amt in accumulated_amount],  # List comprehension to format text labels
    textposition='auto',
    textfont=dict(
        color='white',
        size=12
    ),
    name='Cum Amount',
    marker=dict(color=tech_colors['cum_amount'], opacity=0.5),
), secondary_y=True)

# Add Horizontal Lines for Last Breakeven Price and Stop Loss Level
last_break_even = break_even_values[-1]
stop_loss_value = last_break_even + Decimal(sl)
# Horizontal Lines for Last Breakeven and Stop Loss
fig.add_hline(y=last_break_even, line_dash="dash", annotation_text=f"Global Break Even: {last_break_even:.2f} (%)",
              annotation_position="top left", line_color=tech_colors['break_even'])
fig.add_hline(y=stop_loss_value, line_dash="dash", annotation_text=f"Stop Loss: {stop_loss_value:.2f} (%)",
              annotation_position="bottom right", line_color=tech_colors['stop_loss'])

# Update Annotations for Spread and Break Even
for i, (spread, be_value, tp_value) in enumerate(zip(dca_spreads, break_even_values, take_profit_values)):
    fig.add_annotation(x=i, y=spread, text=f"{spread:.2f}%", showarrow=True, arrowhead=1, yshift=10, xshift=-2,
                       font=dict(color=tech_colors['spread']))
    fig.add_annotation(x=i, y=be_value, text=f"{be_value:.2f}%", showarrow=True, arrowhead=1, yshift=5, xshift=-2,
                       font=dict(color=tech_colors['break_even']))
    fig.add_annotation(x=i, y=tp_value, text=f"{tp_value:.2f}%", showarrow=True, arrowhead=1, yshift=10, xshift=-2,
                       font=dict(color=tech_colors['take_profit']))
# Update Layout with a Dark Theme
fig.update_layout(
    title="Spread, Accumulated Amount, Break Even, and Take Profit by Order Level",
    xaxis_title="Order Level",
    yaxis_title="Spread (%)",
    yaxis2_title="Amount (Quote)",
    height=800,
    width=1800,
    plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent background
    paper_bgcolor='rgba(0, 0, 0, 0.1)',  # Lighter shade for the paper
    font=dict(color='white')  # Font color
)

# Calculate metrics
dca_max_loss = dca_amount * Decimal(sl / 100)
profit_per_level = [cum_amount * Decimal(ts_ap / 100) for cum_amount in accumulated_amount]
loots_to_recover = [dca_max_loss / profit for profit in profit_per_level]

# Define a consistent annotation size and maximum value for the secondary y-axis
circle_text = "●"  # Unicode character for a circle
max_secondary_value = max(max(accumulated_amount), max(dca_order_amounts),
                          max(cum_unrealized_pnl))  # Adjust based on your secondary y-axis data

# Determine an appropriate y-offset for annotations
y_offset_secondary = max_secondary_value * Decimal(
    0.1)  # Adjusts the height relative to the maximum value on the secondary y-axis

# Add annotations to the Plotly figure for the secondary y-axis
for i, loot in enumerate(loots_to_recover):
    fig.add_annotation(
        x=i,
        y=max_secondary_value + y_offset_secondary,  # Position above the maximum value using the offset
        text=f"{circle_text}<br>LTR: {round(loot, 2)}",  # Circle symbol and loot value in separate lines
        showarrow=False,
        font=dict(size=16, color='purple'),
        xanchor="center",  # Centers the text above the x coordinate
        yanchor="bottom",  # Anchors the text at its bottom to avoid overlapping
        align="center",
        yref="y2"  # Reference the secondary y-axis
    )
# Add Max Loss Metric as an Annotation
dca_max_loss_annotation_text = f"DCA Max Loss (Quote): {dca_max_loss:.2f}"
fig.add_annotation(
    x=max(len(dca_spreads), len(break_even_values)) - 1,  # Positioning the annotation to the right
    text=dca_max_loss_annotation_text,
    showarrow=False,
    font=dict(size=20, color='white'),
    bgcolor='red',  # Red background for emphasis
    xanchor="left",
    yanchor="top",
    yref="y2"  # Reference the secondary y-axis
)

st.write("---")

# Display in Streamlit
st.plotly_chart(fig)
c1, c2, c3 = st.columns([2, 2, 1])
with c1:
    config_base = st.text_input("Config Base", value=f"{connector}-{trading_pair.split('-')[0]}")
with c2:
    config_tag = st.text_input("Config Tag", value="1.1")

id = f"{config_base}-{config_tag}"
config = {
        "id": id.lower(),
        "controller_name": "dman_maker_v2",
        "controller_type": "market_making",
        "manual_kill_switch": None,
        "candles_config": [],
        "connector_name": connector,
        "trading_pair": trading_pair,
        "total_amount_quote": total_amount_quote,
        "buy_spreads": buy_spread_distributions,
        "sell_spreads": sell_spread_distributions,
        "buy_amounts_pct": buy_order_amounts_quote,
        "sell_amounts_pct": sell_order_amounts_quote,
        "executor_refresh_time": executor_refresh_time * 60,
        "cooldown_time": cooldown_time,
        "leverage": leverage,
        "position_mode": position_mode,
        "stop_loss": sl / 100,
        "take_profit": tp / 100,
        "time_limit": time_limit * 60,
        "take_profit_order_type": 2,
        "trailing_stop": {
            "activation_price": ts_ap / 100,
            "trailing_delta": ts_delta / 100},
        "dca_amounts": dca_order_amounts,
        "dca_spreads": [spread / 100 for spread in dca_spreads],
        "top_executor_refresh_time": top_executor_refresh_time,
        "executor_activation_bounds": [executor_activation_bounds / 100],
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
    backend_api_client = BackendAPIClient.get_instance()
    backend_api_client.add_controller_config(config)
    st.success("Config uploaded successfully!")