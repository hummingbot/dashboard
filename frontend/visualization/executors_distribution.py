import plotly.graph_objects as go
import frontend.visualization.theme as theme


def create_executors_distribution_traces(config):
    colors = theme.get_color_scheme()

    buy_spread_distributions = [spread * 100 for spread in config["buy_spreads"]]
    sell_spread_distributions = [spread * 100 for spread in config["sell_spreads"]]
    buy_order_amounts_quote = [amount * config["total_amount_quote"] for amount in config["buy_amounts_pct"]]
    sell_order_amounts_quote = [amount * config["total_amount_quote"] for amount in config["sell_amounts_pct"]]
    buy_order_levels = len(buy_spread_distributions)
    sell_order_levels = len(sell_spread_distributions)

    # Create the figure with a dark theme and secondary y-axis
    fig = go.Figure()

    # Buy orders on the negative side of x-axis
    fig.add_trace(go.Bar(
        x=[-dist for dist in buy_spread_distributions],
        y=buy_order_amounts_quote,
        name='Buy Orders',
        marker_color=colors['buy'],
        width=[0.2] * buy_order_levels  # Adjust the width of the bars as needed
    ))

    # Sell orders on the positive side of x-axis
    fig.add_trace(go.Bar(
        x=sell_spread_distributions,
        y=sell_order_amounts_quote,
        name='Sell Orders',
        marker_color=colors['sell'],
        width=[0.2] * sell_order_levels  # Adjust the width of the bars as needed
    ))

    # Add annotations for buy orders
    for i, value in enumerate(buy_order_amounts_quote):
        fig.add_annotation(
            x=-buy_spread_distributions[i],
            y=value + 0.01 * max(buy_order_amounts_quote),  # Offset the text slightly above the bar
            text=str(round(value, 2)),
            showarrow=False,
            font=dict(color=colors['buy'], size=10)
        )

    # Add annotations for sell orders
    for i, value in enumerate(sell_order_amounts_quote):
        fig.add_annotation(
            x=sell_spread_distributions[i],
            y=value + 0.01 * max(sell_order_amounts_quote),  # Offset the text slightly above the bar
            text=str(round(value, 2)),
            showarrow=False,
            font=dict(color=colors['sell'], size=10)
        )

    # Apply the theme layout
    layout_settings = theme.get_default_layout("Market Maker Order Distribution")
    fig.update_layout(**layout_settings)
    fig.update_layout(
        xaxis_title="Spread (%)",
        yaxis_title="Order Amount (Quote)",
        bargap=0.1,  # Adjust the gap between the bars
        barmode='relative',  # Stack the bars on top of each other
        showlegend=True
    )
    return fig