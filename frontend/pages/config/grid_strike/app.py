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


def get_grid_range_traces(grid_ranges):
    """Generate horizontal line traces for grid ranges with different colors."""
    dash_styles = ['solid', 'dash', 'dot', 'dashdot', 'longdash']  # 5 different styles
    traces = []
    buy_count = 0
    sell_count = 0
    for i, grid_range in enumerate(grid_ranges):
        # Set color based on trade type
        if grid_range["side"] == TradeType.BUY:
            color = 'rgba(0, 255, 0, 1)'  # Bright green for buy
            dash_style = dash_styles[buy_count % len(dash_styles)]
            buy_count += 1
        else:
            color = 'rgba(255, 0, 0, 1)'  # Bright red for sell
            dash_style = dash_styles[sell_count % len(dash_styles)]
            sell_count += 1
        # Start price line
        traces.append(go.Scatter(
            x=[],  # Will be set to full range when plotting
            y=[float(grid_range["start_price"]), float(grid_range["start_price"])],
            mode='lines',
            line=dict(color=color, width=1.5, dash=dash_style),
            name=f'Range {i} Start: {float(grid_range["start_price"]):,.2f} ({grid_range["side"].name})',
            hoverinfo='name'
        ))
        # End price line
        traces.append(go.Scatter(
            x=[],  # Will be set to full range when plotting
            y=[float(grid_range["end_price"]), float(grid_range["end_price"])],
            mode='lines',
            line=dict(color=color, width=1.5, dash=dash_style),
            name=f'Range {i} End: {float(grid_range["end_price"]):,.2f} ({grid_range["side"].name})',
            hoverinfo='name'
        ))
    return traces


# Initialize the Streamlit page
initialize_st_page(title="Grid Strike", icon="📊", initial_sidebar_state="expanded")
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
    subplot_titles=(f'Grid Strike - {inputs["trading_pair"]} ({inputs["interval"]})',),
)

# Add basic candlestick chart
candlestick_trace = get_candlestick_trace(candles)
add_traces_to_fig(fig, [candlestick_trace], row=1, col=1)

# Add grid range visualization
grid_traces = get_grid_range_traces(inputs["grid_ranges"])
for trace in grid_traces:
    # Set the x-axis range for all grid traces
    trace.x = [candles.index[0], candles.index[-1]]
    fig.add_trace(trace, row=1, col=1)

# Update y-axis to make sure all grid ranges and candles are visible
all_prices = []
# Add candle prices
all_prices.extend(candles['high'].tolist())
all_prices.extend(candles['low'].tolist())
# Add grid range prices
for grid_range in inputs["grid_ranges"]:
    all_prices.extend([float(grid_range["start_price"]), float(grid_range["end_price"])])

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
    grid_ranges = []
    for grid_range in prepared_config["grid_ranges"]:
        grid_range = grid_range.copy()
        grid_range["side"] = grid_range["side"].value
        grid_range["open_order_type"] = grid_range["open_order_type"].value
        grid_range["take_profit_order_type"] = grid_range["take_profit_order_type"].value
        grid_ranges.append(grid_range)
    prepared_config["grid_ranges"] = grid_ranges
    prepared_config["position_mode"] = prepared_config["position_mode"].value
    del prepared_config["candles_connector"]
    del prepared_config["interval"]
    del prepared_config["days_to_visualize"]
    return prepared_config


# Replace the render_save_config line with:
render_save_config(st.session_state["default_config"]["id"],
                   prepare_config_for_save(st.session_state["default_config"]))
