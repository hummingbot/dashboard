import plotly.graph_objects as go
import pandas as pd

def get_candlestick_trace(df):
    df.index = pd.to_datetime(df.timestamp, unit='ms')
    return go.Candlestick(x=df.index,
                          open=df['open'],
                          high=df['high'],
                          low=df['low'],
                          close=df['close'],
                          name="Candlesticks",
                          increasing_line_color='#2ECC71', decreasing_line_color='#E74C3C')
