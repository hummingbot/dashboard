import numpy as np
import plotly.graph_objects as go

import frontend.visualization.theme as theme


def create_executors_distribution_traces(buy_spreads, sell_spreads, buy_amounts_pct, sell_amounts_pct,
                                         total_amount_quote):
    colors = theme.get_color_scheme()

    buy_spread_distributions = [spread * 100 for spread in buy_spreads]
    sell_spread_distributions = [spread * 100 for spread in sell_spreads]
    
    # Normalize amounts across both buy and sell sides (matching controller logic)
    total_pct = sum(buy_amounts_pct) + sum(sell_amounts_pct)
    normalized_buy_amounts_pct = [amt_pct / total_pct for amt_pct in buy_amounts_pct]
    normalized_sell_amounts_pct = [amt_pct / total_pct for amt_pct in sell_amounts_pct]
    
    buy_order_amounts_quote = [amount * total_amount_quote for amount in normalized_buy_amounts_pct]
    sell_order_amounts_quote = [amount * total_amount_quote for amount in normalized_sell_amounts_pct]
    buy_order_levels = len(buy_spread_distributions)
    sell_order_levels = len(sell_spread_distributions)

    # Calculate total volumes
    total_buy_volume = sum(buy_order_amounts_quote)
    total_sell_volume = sum(sell_order_amounts_quote)

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
            y=value + 0.03 * max(buy_order_amounts_quote),  # Offset the text slightly above the bar
            text=str(round(value, 2)),
            showarrow=False,
            font=dict(color=colors['buy'], size=10)
        )

    # Add annotations for sell orders
    for i, value in enumerate(sell_order_amounts_quote):
        fig.add_annotation(
            x=sell_spread_distributions[i],
            y=value + 0.03 * max(sell_order_amounts_quote),  # Offset the text slightly above the bar
            text=str(round(value, 2)),
            showarrow=False,
            font=dict(color=colors['sell'], size=10)
        )

    max_y = max(max(buy_order_amounts_quote), max(sell_order_amounts_quote))
    # Add annotations for total volumes
    fig.add_annotation(
        x=-np.mean(buy_spread_distributions),
        y=max_y,
        text=f'Total Buy\n{round(total_buy_volume, 2)}',
        showarrow=False,
        font=dict(color=colors['buy'], size=12, family="Arial Black"),
        align='center'
    )

    fig.add_annotation(
        x=np.mean(sell_spread_distributions),
        y=max_y,
        text=f'Total Sell\n{round(total_sell_volume, 2)}',
        showarrow=False,
        font=dict(color=colors['sell'], size=12, family="Arial Black"),
        align='center'
    )

    # Apply the theme layout
    layout_settings = theme.get_default_layout("Market Maker Order Distribution")
    fig.update_layout(**layout_settings)
    fig.update_layout(
        xaxis_title="Spread (%)",
        yaxis_title="Order Amount (Quote)",
        bargap=0.1,  # Adjust the gap between the bars
        barmode='relative',  # Stack the bars on top of each other
        showlegend=True,
        height=600
    )
    return fig
