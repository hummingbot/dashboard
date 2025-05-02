import plotly.graph_objects as go
import streamlit as st
from hummingbot.core.data_type.common import TradeType
from plotly.subplots import make_subplots

from frontend.components.config_loader import get_default_config_loader
from frontend.components.save_config import render_save_config
from frontend.pages.config.grid_strike.user_inputs import user_inputs
from frontend.pages.config.utils import get_candles
from frontend.st_utils import get_backend_api_client, initialize_st_page
from frontend.visualization import theme
from frontend.visualization.candles import get_candlestick_trace
from frontend.visualization.utils import add_traces_to_fig


def get_grid_trace(start_price, end_price, limit_price):
    """Generate horizontal line traces for the grid with different colors."""
    traces = []
    
    # Start price line
    traces.append(go.Scatter(
        x=[],  # Will be set to full range when plotting
        y=[float(start_price), float(start_price)],
        mode='lines',
        line=dict(color='rgba(0, 255, 0, 1)', width=1.5, dash='solid'),
        name=f'Start Price: {float(start_price):,.2f}',
        hoverinfo='name'
    ))
    
    # End price line
    traces.append(go.Scatter(
        x=[],  # Will be set to full range when plotting
        y=[float(end_price), float(end_price)],
        mode='lines',
        line=dict(color='rgba(0, 255, 0, 1)', width=1.5, dash='dot'),
        name=f'End Price: {float(end_price):,.2f}',
        hoverinfo='name'
    ))
    
    # Limit price line (if provided)
    if limit_price:
        traces.append(go.Scatter(
            x=[],  # Will be set to full range when plotting
            y=[float(limit_price), float(limit_price)],
            mode='lines',
            line=dict(color='rgba(255, 0, 0, 1)', width=1.5, dash='dashdot'),
            name=f'Limit Price: {float(limit_price):,.2f}',
            hoverinfo='name'
        ))
    
    return traces


# Initialize the Streamlit page
initialize_st_page(title="Grid Strike Grid Component", icon="📊", initial_sidebar_state="expanded")
backend_api_client = get_backend_api_client()

get_default_config_loader("grid_strike")
# User inputs
inputs = user_inputs()
st.session_state["default_config"].update(inputs)

# Load candle data
candles = get_candles(
    connector_name=inputs["connector_name"],
    trading_pair=inputs["trading_pair"],
    interval=inputs["interval"],
    days=inputs["days_to_visualize"]
)

# Create a subplot with just 1 row for price action
fig = make_subplots(
    rows=1, cols=1,
    subplot_titles=(f'Grid Strike Grid Component - {inputs["trading_pair"]} ({inputs["interval"]})',),
)

# Add basic candlestick chart
candlestick_trace = get_candlestick_trace(candles)
add_traces_to_fig(fig, [candlestick_trace], row=1, col=1)

# Add grid visualization
grid_traces = get_grid_trace(
    inputs["start_price"], 
    inputs["end_price"], 
    inputs["limit_price"]
)

for trace in grid_traces:
    # Set the x-axis range for all grid traces
    trace.x = [candles.index[0], candles.index[-1]]
    fig.add_trace(trace, row=1, col=1)

# Update y-axis to make sure all grid points and candles are visible
all_prices = []
# Add candle prices
all_prices.extend(candles['high'].tolist())
all_prices.extend(candles['low'].tolist())
# Add grid prices
all_prices.extend([float(inputs["start_price"]), float(inputs["end_price"])])
if inputs["limit_price"]:
    all_prices.append(float(inputs["limit_price"]))

y_min, y_max = min(all_prices), max(all_prices)
padding = (y_max - y_min) * 0.1  # Add 10% padding
fig.update_yaxes(range=[y_min - padding, y_max + padding])

# Update layout for better visualization
layout_updates = {
    "legend": dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01,
        bgcolor="rgba(0,0,0,0.5)"
    ),
    "hovermode": 'x unified',
    "showlegend": True,
    "height": 600,  # Make the chart taller
    "yaxis": dict(
        fixedrange=False,  # Allow y-axis zooming
        autorange=True,  # Enable auto-ranging
    )
}

# Merge the default theme with our updates
fig.update_layout(
    **(theme.get_default_layout() | layout_updates)
)

# Use Streamlit's functionality to display the plot
st.plotly_chart(fig, use_container_width=True)


# Add after user inputs and before saving
def prepare_config_for_save(config):
    """Prepare config for JSON serialization."""
    prepared_config = config.copy()
    
    # Convert position mode enum to value
    prepared_config["position_mode"] = prepared_config["position_mode"].value
    
    # Convert side to value
    prepared_config["side"] = prepared_config["side"].value
    
    # Convert triple barrier order types to values
    if "triple_barrier_config" in prepared_config and prepared_config["triple_barrier_config"]:
        for key in ["open_order_type", "stop_loss_order_type", "take_profit_order_type", "time_limit_order_type"]:
            if key in prepared_config["triple_barrier_config"] and prepared_config["triple_barrier_config"][key] is not None:
                prepared_config["triple_barrier_config"][key] = prepared_config["triple_barrier_config"][key].value
    
    # Remove chart-specific fields
    del prepared_config["candles_connector"]
    del prepared_config["interval"]
    del prepared_config["days_to_visualize"]
    
    return prepared_config


# Render save config component
render_save_config(st.session_state["default_config"]["id"],
                   prepare_config_for_save(st.session_state["default_config"])) 