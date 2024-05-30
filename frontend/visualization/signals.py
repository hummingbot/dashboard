from frontend.visualization import theme
import plotly.graph_objects as go
import pandas_ta as ta  # noqa: F401


def get_signal_traces(buy_signals, sell_signals):
    tech_colors = theme.get_color_scheme()
    traces = [
        go.Scatter(x=buy_signals.index, y=buy_signals['close'], mode='markers',
                   marker=dict(color=tech_colors['buy_signal'], size=10, symbol='triangle-up'),
                   name='Buy Signal'),
        go.Scatter(x=sell_signals.index, y=sell_signals['close'], mode='markers',
                   marker=dict(color=tech_colors['sell_signal'], size=10, symbol='triangle-down'),
                   name='Sell Signal')
    ]
    return traces

def get_bollinger_v1_signal_traces(df, bb_length, bb_std, bb_long_threshold, bb_short_threshold):
    # Add Bollinger Bands
    candles = df.copy()
    candles.ta.bbands(length=bb_length, std=bb_std, append=True)

    # Generate conditions
    buy_signals = candles[candles[f"BBP_{bb_length}_{bb_std}"] < bb_long_threshold]
    sell_signals = candles[candles[f"BBP_{bb_length}_{bb_std}"] > bb_short_threshold]

    return get_signal_traces(buy_signals, sell_signals)


def get_macdbb_v1_signal_traces(df, bb_length, bb_std, bb_long_threshold, bb_short_threshold, macd_fast, macd_slow,
                                macd_signal):
    tech_colors = theme.get_color_scheme()
    # Add Bollinger Bands
    df.ta.bbands(length=bb_length, std=bb_std, append=True)
    # Add MACD
    df.ta.macd(fast=macd_fast, slow=macd_slow, signal=macd_signal, append=True)
    # Decision Logic
    bbp = df[f"BBP_{bb_length}_{bb_std}"]
    macdh = df[f"MACDh_{macd_fast}_{macd_slow}_{macd_signal}"]
    macd = df[f"MACD_{macd_fast}_{macd_slow}_{macd_signal}"]

    buy_signals = df[(bbp < bb_long_threshold) & (macdh > 0) & (macd < 0)]
    sell_signals = df[(bbp > bb_short_threshold) & (macdh < 0) & (macd > 0)]

    return get_signal_traces(buy_signals, sell_signals)


def get_supertrend_v1_signal_traces(df, length, multiplier, percentage_threshold):
    # Add indicators
    df.ta.supertrend(length=length, multiplier=multiplier, append=True)
    df["percentage_distance"] = abs(df["close"] - df[f"SUPERT_{length}_{multiplier}"]) / df["close"]

    # Generate long and short conditions
    buy_signals = df[(df[f"SUPERTd_{length}_{multiplier}"] == 1) & (df["percentage_distance"] < percentage_threshold)]
    sell_signals = df[(df[f"SUPERTd_{length}_{multiplier}"] == -1) & (df["percentage_distance"] < percentage_threshold)]

    return get_signal_traces(buy_signals, sell_signals)
