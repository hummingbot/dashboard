import pandas_ta as ta  # noqa: F401
import plotly.graph_objects as go

from frontend.visualization import theme


def get_bbands_traces(candles, bb_length, bb_std):
    tech_colors = theme.get_color_scheme()
    candles.ta.bbands(length=bb_length, std=bb_std, append=True)
    bb_lower = f'BBL_{bb_length}_{bb_std}'
    bb_middle = f'BBM_{bb_length}_{bb_std}'
    bb_upper = f'BBU_{bb_length}_{bb_std}'
    traces = [
        go.Scatter(x=candles.index, y=candles[bb_upper], line=dict(color=tech_colors['upper_band']),
                   name='Upper Band'),
        go.Scatter(x=candles.index, y=candles[bb_middle], line=dict(color=tech_colors['middle_band']),
                   name='Middle Band'),
        go.Scatter(x=candles.index, y=candles[bb_lower], line=dict(color=tech_colors['lower_band']),
                   name='Lower Band'),
    ]
    return traces
