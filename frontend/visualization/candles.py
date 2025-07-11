import pandas as pd
import plotly.graph_objects as go

from frontend.visualization import theme


def get_candlestick_trace(df):
    return go.Candlestick(x=df.index,
                          open=df['open'],
                          high=df['high'],
                          low=df['low'],
                          close=df['close'],
                          name="Candlesticks",
                          increasing_line_color='#2ECC71', decreasing_line_color='#E74C3C', )


def get_bt_candlestick_trace(df):
    # Convert dict to DataFrame if needed
    if isinstance(df, dict):
        df = pd.DataFrame(df)
    df.index = pd.to_datetime(df.timestamp, unit='s')
    return go.Scatter(x=df.index,
                      y=df['close'],
                      mode='lines',
                      line=dict(color=theme.get_color_scheme()["price"]),
                      )
