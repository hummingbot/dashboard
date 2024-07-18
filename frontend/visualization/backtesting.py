from plotly.subplots import make_subplots

from frontend.visualization.candles import get_bt_candlestick_trace
from frontend.visualization.executors import add_executors_trace
from frontend.visualization.pnl import get_pnl_trace
from frontend.visualization.theme import get_default_layout


def create_backtesting_figure(df, executors, config):
    # Create subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.02, subplot_titles=('Candlestick', 'PNL Quote'),
                        row_heights=[0.7, 0.3])

    # Add candlestick trace
    fig.add_trace(get_bt_candlestick_trace(df), row=1, col=1)

    # Add executors trace
    fig = add_executors_trace(fig, executors, row=1, col=1)

    # Add PNL trace
    fig.add_trace(get_pnl_trace(executors), row=2, col=1)

    # Apply the theme layout
    layout_settings = get_default_layout(f"Trading Pair: {config['trading_pair']}")
    layout_settings["showlegend"] = False
    fig.update_layout(**layout_settings)

    # Update axis properties
    fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
    fig.update_xaxes(row=2, col=1)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="PNL", row=2, col=1)
    return fig
