import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pandas_ta as ta
import yaml
from hummingbot.connector.connector_base import OrderType

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from utils.backend_api_client import BackendAPIClient
from utils.st_utils import initialize_st_page

# Initialize the Streamlit page
initialize_st_page(title="Trend Follower V1", icon="📈", initial_sidebar_state="expanded")


@st.cache_data
def get_candles(connector_name="binance", trading_pair="BTC-USDT", interval="1m", max_records=5000):
    backend_client = BackendAPIClient(BACKEND_API_HOST, BACKEND_API_PORT)
    return backend_client.get_real_time_candles(connector_name, trading_pair, interval, max_records)

@st.cache_data
def add_indicators(df, sma_fast, sma_slow, entry_threshold):
    # Add indicators
    df.ta.sma(close='close', length=sma_fast, append=True)
    df.ta.sma(close='close', length=sma_slow, append=True)
    df = df.dropna()
    cross_up = ta.cross(df[f"SMA_{sma_fast}"], df[f"SMA_{sma_slow}"], above=True)
    cross_down = ta.cross(df[f"SMA_{sma_fast}"], df[f"SMA_{sma_slow}"], above=False)
    sma_fast = df[f"SMA_{sma_fast}"]
    sma_slow = df[f"SMA_{sma_slow}"]

    # Generate signal
    long_condition = (cross_up == 1) & (df["close"] * (1 - entry_threshold) < sma_fast)
    short_condition = (cross_down == 1) & (df["close"] * (1 + entry_threshold) > sma_fast)

    df["signal"] = 0
    df.loc[long_condition, "signal"] = 1
    df.loc[short_condition, "signal"] = -1
    return df


st.text("This tool will let you create a config for Trend Follower V1 and visualize the strategy.")
st.write("---")

# Inputs for Bollinger Band configuration
st.write("## Candles Configuration")
c1, c2, c3, c4 = st.columns(4)
with c1:
    connector_name = st.text_input("Connector Name", value="binance_perpetual")
    candles_connector = st.text_input("Candles Connector", value="binance_perpetual")
with c2:
    trading_pair = st.text_input("Trading Pair", value="WLD-USDT")
    candles_trading_pair = st.text_input("Candles Trading Pair", value="WLD-USDT")
with c3:
    interval = st.selectbox("Candle Interval", options=["1m", "3m", "5m", "15m", "30m"], index=1)
with c4:
    max_records = st.number_input("Max Records", min_value=100, max_value=10000, value=1000)


st.write("## Positions Configuration")
c1, c2, c3, c4 = st.columns(4)
with c1:
    sl = st.number_input("Stop Loss (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.1)
    tp = st.number_input("Take Profit (%)", min_value=0.0, max_value=100.0, value=3.0, step=0.1)
    take_profit_order_type = st.selectbox("Take Profit Order Type", (OrderType.LIMIT, OrderType.MARKET))
with c2:
    ts_ap = st.number_input("Trailing Stop Activation Price (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1)
    ts_delta = st.number_input("Trailing Stop Delta (%)", min_value=0.0, max_value=100.0, value=0.3, step=0.1)
    time_limit = st.number_input("Time Limit (minutes)", min_value=0, value=60 * 6)
with c3:
    executor_amount_quote = st.number_input("Executor Amount Quote", min_value=10.0, value=100.0, step=1.0)
    max_executors_per_side = st.number_input("Max Executors Per Side", min_value=1, value=2)
    cooldown_time = st.number_input("Cooldown Time (seconds)", min_value=0, value=300)
with c4:
    leverage = st.number_input("Leverage", min_value=1, value=20)
    position_mode = st.selectbox("Position Mode", ("HEDGE", "ONEWAY"))

st.write("## Bollinger Bands Configuration")
c1, c2, c3 = st.columns(3)
with c1:
    sma_fast = st.number_input("Fast SMA Length", min_value=10, max_value=100, value=20)
with c2:
    sma_slow = st.number_input("Slow SMA Length", min_value=20, max_value=500, value=200)
with c3:
    entry_threshold = st.number_input("Entry Threshold (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1) / 100

# Load candle data
candle_data = get_candles(connector_name=candles_connector, trading_pair=candles_trading_pair, interval=interval, max_records=max_records)
df = pd.DataFrame(candle_data)
df.index = pd.to_datetime(df['timestamp'], unit='ms')
candles_processed = add_indicators(df, sma_fast, sma_slow, entry_threshold)


# Prepare data for signals
signals = candles_processed[candles_processed['signal'] != 0]
buy_signals = signals[signals['signal'] == 1]
sell_signals = signals[signals['signal'] == -1]

from plotly.subplots import make_subplots

# Define your color palette
tech_colors = {
    'upper_band': '#4682B4',    # Steel Blue for the Upper Bollinger Band
    'middle_band': '#FFD700',  # Gold for the Middle Bollinger Band
    'lower_band': '#32CD32',   # Green for the Lower Bollinger Band
    'buy_signal': '#1E90FF',   # Dodger Blue for Buy Signals
    'sell_signal': '#FF0000',  # Red for Sell Signals
}

# Create a subplot with 2 rows
fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    vertical_spacing=0.02, subplot_titles=('Candlestick with Moving Averages', 'Trading Signals'),
                    row_heights=[0.7, 0.3])

# Candlestick plot
fig.add_trace(go.Candlestick(x=candles_processed.index,
                             open=candles_processed['open'],
                             high=candles_processed['high'],
                             low=candles_processed['low'],
                             close=candles_processed['close'],
                             name="Candlesticks", increasing_line_color='#2ECC71', decreasing_line_color='#E74C3C'),
              row=1, col=1)

# Moving Averages
fig.add_trace(go.Scatter(x=candles_processed.index, y=candles_processed[f"SMA_{sma_fast}"], line=dict(color='blue'), name=f'Fast SMA ({sma_fast})'), row=1, col=1)
fig.add_trace(go.Scatter(x=candles_processed.index, y=candles_processed[f"SMA_{sma_slow}"], line=dict(color='red'), name=f'Slow SMA ({sma_slow})'), row=1, col=1)

# Signals plot
fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['close'], mode='markers',
                         marker=dict(color=tech_colors['buy_signal'], size=20, symbol='triangle-up'),
                         name='Buy Signal'), row=1, col=1)
fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['close'], mode='markers',
                         marker=dict(color=tech_colors['sell_signal'], size=20, symbol='triangle-down'),
                         name='Sell Signal'), row=1, col=1)

fig.add_trace(go.Scatter(x=signals.index, y=signals['signal'], mode='markers',
                         marker=dict(color=signals['signal'].map({1: tech_colors['buy_signal'], -1: tech_colors['sell_signal']}), size=10),
                         showlegend=False), row=2, col=1)

# Update layout
fig.update_layout(
    height=1000,  # Increased height for better visibility
    title="Bollinger Bands and Trading Signals",
    xaxis_title="Time",
    yaxis_title="Price",
    template="plotly_dark",
    showlegend=False
)

# Update xaxis properties
fig.update_xaxes(
    rangeslider_visible=False,  # Disable range slider for all
    row=1, col=1
)
fig.update_xaxes(
    row=2, col=1
)

# Update yaxis properties
fig.update_yaxes(
    title_text="Price", row=1, col=1
)
fig.update_yaxes(
    title_text="Signal", row=2, col=1
)

# Use Streamlit's functionality to display the plot
st.plotly_chart(fig, use_container_width=True)

c1, c2, c3 = st.columns([2, 2, 1])

with c1:
    config_base = st.text_input("Config Base", value=f"bollinger_v1-{connector_name}-{trading_pair.split('-')[0]}")
with c2:
    config_tag = st.text_input("Config Tag", value="1.1")

id = f"{config_base}-{config_tag}"
config = {
    "id": id,
    "controller_name": "bollinger_v1",
    "controller_type": "directional_trading",
    "manual_kill_switch": None,
    "candles_config": [],
    "connector_name": connector_name,
    "trading_pair": trading_pair,
    "executor_amount_quote": executor_amount_quote,
    "max_executors_per_side": max_executors_per_side,
    "cooldown_time": cooldown_time,
    "leverage": leverage,
    "position_mode": position_mode,
    "stop_loss": sl / 100,
    "take_profit": tp / 100,
    "time_limit": time_limit,
    "take_profit_order_type": take_profit_order_type.value,
    "trailing_stop": {
        "activation_price": ts_ap / 100,
        "trailing_delta": ts_delta / 100
    },
    "candles_connector": candles_connector,
    "candles_trading_pair": candles_trading_pair,
    "interval": interval,
}

yaml_config = yaml.dump(config, default_flow_style=False)

with c3:
    download_config = st.download_button(
        label="Download YAML",
        data=yaml_config,
        file_name=f'{id.lower()}.yml',
        mime='text/yaml'
    )
    upload_config_to_backend = st.button("Upload Config to BackendAPI")


if upload_config_to_backend:
    backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)
    backend_api_client.add_controller_config(config)
    st.success("Config uploaded successfully!")