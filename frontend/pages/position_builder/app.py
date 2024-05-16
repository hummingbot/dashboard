import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from decimal import Decimal
import yaml

from frontend.components.st_inputs import normalize, distribution_inputs, get_distribution
from frontend.st_utils import initialize_st_page

# Initialize the Streamlit page
initialize_st_page(title="Position Generator", icon="🔭", initial_sidebar_state="collapsed")

# Page content
st.text("This tool will help you analyze and generate a position config.")
st.write("---")

# Layout in columns
col_quote, col_tp_sl, col_levels, col_spread_dist, col_amount_dist = st.columns([1, 1, 1, 2, 2])

def convert_to_yaml(spreads, order_amounts):
    data = {
        'dca_spreads': [float(spread)/100 for spread in spreads],
        'dca_amounts': [float(amount) for amount in order_amounts]
    }
    return yaml.dump(data, default_flow_style=False)


with col_quote:
    total_amount_quote = st.number_input("Total amount of quote", value=1000)

with col_tp_sl:
    tp = st.number_input("Take Profit (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.1)
    sl = st.number_input("Stop Loss (%)", min_value=0.0, max_value=100.0, value=8.0, step=0.1)

with col_levels:
    n_levels = st.number_input("Number of Levels", min_value=1, value=5)


# Spread and Amount Distributions
spread_dist_type, spread_start, spread_base, spread_scaling, spread_step, spread_ratio, manual_spreads = distribution_inputs(col_spread_dist, "Spread", n_levels)
amount_dist_type, amount_start, amount_base, amount_scaling, amount_step, amount_ratio, manual_amounts = distribution_inputs(col_amount_dist, "Amount", n_levels)

spread_distribution = get_distribution(spread_dist_type, n_levels, spread_start, spread_base, spread_scaling, spread_step, spread_ratio, manual_spreads)
amount_distribution = normalize(get_distribution(amount_dist_type, n_levels, amount_start, amount_base, amount_scaling, amount_step, amount_ratio, manual_amounts))
order_amounts = [Decimal(amount_dist * total_amount_quote) for amount_dist in amount_distribution]
spreads = [Decimal(spread - spread_distribution[0]) for spread in spread_distribution]


# Export Button
if st.button('Export as YAML'):
    yaml_data = convert_to_yaml(spreads, order_amounts)
    st.download_button(
        label="Download YAML",
        data=yaml_data,
        file_name='config.yaml',
        mime='text/yaml'
    )

break_even_values = []
take_profit_values = []
for level in range(n_levels):
    spreads_normalized = [Decimal(spread) + Decimal(0.01) for spread in spreads[:level+1]]
    amounts = order_amounts[:level+1]
    break_even = (sum([spread * amount for spread, amount in zip(spreads_normalized, amounts)]) / sum(amounts)) - Decimal(0.01)
    break_even_values.append(break_even)
    take_profit_values.append(break_even - Decimal(tp))

accumulated_amount = [sum(order_amounts[:i+1]) for i in range(len(order_amounts))]


def calculate_unrealized_pnl(spreads, break_even_values, accumulated_amount):
    unrealized_pnl = []
    for i in range(len(spreads)):
        distance = abs(spreads[i] - break_even_values[i])
        pnl = accumulated_amount[i] * distance / 100  # PNL calculation
        unrealized_pnl.append(pnl)
    return unrealized_pnl

# Calculate unrealized PNL
cum_unrealized_pnl = calculate_unrealized_pnl(spreads, break_even_values, accumulated_amount)


tech_colors = {
    'spread': '#00BFFF',        # Deep Sky Blue
    'break_even': '#FFD700',    # Gold
    'take_profit': '#32CD32',   # Green
    'order_amount': '#1E90FF',  # Dodger Blue
    'cum_amount': '#4682B4',    # Steel Blue
    'stop_loss': '#FF0000',     # Red
}

# Create Plotly figure with secondary y-axis and a dark theme
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.update_layout(template="plotly_dark")

# Update the Scatter Plots and Horizontal Lines
fig.add_trace(go.Scatter(x=list(range(len(spreads))), y=spreads, name='Spread (%)', mode='lines+markers', line=dict(width=3, color=tech_colors['spread'])), secondary_y=False)
fig.add_trace(go.Scatter(x=list(range(len(break_even_values))), y=break_even_values, name='Break Even (%)', mode='lines+markers', line=dict(width=3, color=tech_colors['break_even'])), secondary_y=False)
fig.add_trace(go.Scatter(x=list(range(len(take_profit_values))), y=take_profit_values, name='Take Profit (%)', mode='lines+markers', line=dict(width=3, color=tech_colors['take_profit'])), secondary_y=False)

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
    x=list(range(len(order_amounts))),
    y=order_amounts,
    text=[f"{amt:.2f}" for amt in order_amounts],  # List comprehension to format text labels
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
fig.add_hline(y=last_break_even, line_dash="dash", annotation_text=f"Global Break Even: {last_break_even:.2f} (%)", annotation_position="top left", line_color=tech_colors['break_even'])
fig.add_hline(y=stop_loss_value, line_dash="dash", annotation_text=f"Stop Loss: {stop_loss_value:.2f} (%)", annotation_position="bottom right", line_color=tech_colors['stop_loss'])

# Update Annotations for Spread and Break Even
for i, (spread, be_value, tp_value) in enumerate(zip(spreads, break_even_values, take_profit_values)):
    fig.add_annotation(x=i, y=spread, text=f"{spread:.2f}%", showarrow=True, arrowhead=1, yshift=10, xshift=-2, font=dict(color=tech_colors['spread']))
    fig.add_annotation(x=i, y=be_value, text=f"{be_value:.2f}%", showarrow=True, arrowhead=1, yshift=5, xshift=-2, font=dict(color=tech_colors['break_even']))
    fig.add_annotation(x=i, y=tp_value, text=f"{tp_value:.2f}%", showarrow=True, arrowhead=1, yshift=10, xshift=-2, font=dict(color=tech_colors['take_profit']))
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
max_loss = total_amount_quote * Decimal(sl / 100)
profit_per_level = [cum_amount * Decimal(tp / 100) for cum_amount in accumulated_amount]
loots_to_recover = [max_loss / profit for profit in profit_per_level]

# Define a consistent annotation size and maximum value for the secondary y-axis
circle_text = "●"  # Unicode character for a circle
max_secondary_value = max(max(accumulated_amount), max(order_amounts), max(cum_unrealized_pnl))  # Adjust based on your secondary y-axis data

# Determine an appropriate y-offset for annotations
y_offset_secondary = max_secondary_value * Decimal(0.1)  # Adjusts the height relative to the maximum value on the secondary y-axis

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
max_loss_annotation_text = f"Max Loss (Quote): {max_loss:.2f}"
fig.add_annotation(
    x=max(len(spreads), len(break_even_values)) - 1,  # Positioning the annotation to the right
    text=max_loss_annotation_text,
    showarrow=False,
    font=dict(size=20, color='white'),
    bgcolor='red',                                   # Red background for emphasis
    xanchor="left",
    yanchor="top",
    yref="y2"                                        # Reference the secondary y-axis
)

st.write("---")

# Display in Streamlit
st.plotly_chart(fig)

