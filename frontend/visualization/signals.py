from frontend.visualization import theme
import plotly.graph_objects as go
import pandas_ta as ta  # noqa: F401


def add_bbands_with_threshold(fig, candles, bb_length, bb_std, bb_long_threshold, bb_short_threshold, row=1, col=1):
    tech_colors = theme.get_color_scheme()
    # Add Bollinger Bands
    candles.ta.bbands(length=bb_length, std=bb_std, append=True)

    # Generate conditions
    buy_signals = candles[candles[f"BBP_{bb_length}_{bb_std}"] < bb_long_threshold]
    sell_signals = candles[candles[f"BBP_{bb_length}_{bb_std}"] > bb_short_threshold]

    # Signals plot
    fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['close'], mode='markers',
                             marker=dict(color=tech_colors['buy_signal'], size=10, symbol='triangle-up'),
                             name='Buy Signal'), row=row, col=col)
    fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['close'], mode='markers',
                             marker=dict(color=tech_colors['sell_signal'], size=10, symbol='triangle-down'),
                             name='Sell Signal'), row=row, col=col)
    return fig
