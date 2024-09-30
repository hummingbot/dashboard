import plotly.graph_objects as go
from plotly.subplots import make_subplots

import frontend.visualization.theme as theme


def calculate_unrealized_pnl(spreads, break_even_values, accumulated_amount):
    unrealized_pnl = []
    for i in range(len(spreads)):
        distance = abs(spreads[i] - break_even_values[i])
        pnl = accumulated_amount[i] * distance / 100  # PNL calculation
        unrealized_pnl.append(pnl)
    return unrealized_pnl


def create_dca_graph(dca_inputs, dca_amount):
    tech_colors = theme.get_color_scheme()
    dca_order_amounts = [amount_dist * dca_amount for amount_dist in dca_inputs["dca_amounts_pct"]]
    n_levels = len(dca_inputs["dca_spreads"])
    dca_spreads = [spread * 100 for spread in dca_inputs["dca_spreads"]]
    break_even_values = []
    take_profit_values = []
    for level in range(n_levels):
        dca_spreads_normalized = [spread + 0.01 for spread in dca_spreads[:level + 1]]
        amounts = dca_order_amounts[:level + 1]
        break_even = (sum([spread * amount for spread, amount in zip(dca_spreads_normalized, amounts)]) / sum(
            amounts)) - 0.01 if sum(amounts) != 0 else 0
        break_even_values.append(break_even)
        take_profit_values.append(break_even - dca_inputs["take_profit"] * 100)

    accumulated_amount = [sum(dca_order_amounts[:i + 1]) for i in range(len(dca_order_amounts))]

    # Calculate unrealized PNL
    cum_unrealized_pnl = calculate_unrealized_pnl(dca_spreads, break_even_values, accumulated_amount)

    # Create Plotly figure with secondary y-axis and a dark theme
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.update_layout(template="plotly_dark")

    # Update the Scatter Plots and Horizontal Lines
    fig.add_trace(
        go.Scatter(x=list(range(len(dca_spreads))), y=dca_spreads, name='Spread (%)',
                   mode='lines+markers',
                   line=dict(width=3, color=tech_colors['spread'])), secondary_y=False)
    fig.add_trace(
        go.Scatter(x=list(range(len(break_even_values))), y=break_even_values, name='Break Even (%)',
                   mode='lines+markers',
                   line=dict(width=3, color=tech_colors['break_even'])), secondary_y=False)
    fig.add_trace(go.Scatter(x=list(range(len(take_profit_values))), y=take_profit_values, name='Take Profit (%)',
                             mode='lines+markers', line=dict(width=3, color=tech_colors['take_profit'])),
                  secondary_y=False)

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
    stop_loss_value = last_break_even + dca_inputs["stop_loss"] * 100
    # Horizontal Lines for Last Breakeven and Stop Loss
    fig.add_hline(y=last_break_even, line_dash="dash", annotation_text=f"Global Break Even: {last_break_even:.2f} (%)",
                  annotation_position="top left", line_color=tech_colors['break_even'])
    fig.add_hline(y=stop_loss_value, line_dash="dash", annotation_text=f"Stop Loss: {stop_loss_value:.2f} (%)",
                  annotation_position="bottom right", line_color=tech_colors['stop_loss'])

    # Update Annotations for Spread and Break Even
    for i, (spread, be_value, tp_value) in enumerate(
            zip(dca_spreads, break_even_values, take_profit_values)):
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
    dca_max_loss = dca_amount * dca_inputs["stop_loss"]
    profit_per_level = [cum_amount * dca_inputs["take_profit"] for cum_amount in accumulated_amount]
    loots_to_recover = [dca_max_loss / profit for profit in profit_per_level]

    # Define a consistent annotation size and maximum value for the secondary y-axis
    circle_text = "●"  # Unicode character for a circle
    max_secondary_value = max(max(accumulated_amount), max(dca_order_amounts),
                              max(cum_unrealized_pnl))  # Adjust based on your secondary y-axis data

    # Determine an appropriate y-offset for annotations
    y_offset_secondary = max_secondary_value * 0.1  # Adjusts the height relative to the maximum value on the secondary y-axis

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
        x=max(len(dca_inputs["dca_spreads"]), len(break_even_values)) - 1,  # Positioning the annotation to the right
        text=dca_max_loss_annotation_text,
        showarrow=False,
        font=dict(size=20, color='white'),
        bgcolor='red',  # Red background for emphasis
        xanchor="left",
        yanchor="top",
        yref="y2"  # Reference the secondary y-axis
    )
    return fig
