import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from frontend.st_utils import get_backend_api_client, initialize_st_page

initialize_st_page(
    title="Trading Hub",
    icon="💹",
    layout="wide",
    show_readme=False
)

# Initialize backend client
backend_api_client = get_backend_api_client()

# Initialize session state
if "selected_market" not in st.session_state:
    st.session_state.selected_market = {"connector": "binance_perpetual", "trading_pair": "BTC-USDT"}
if "auto_refresh_enabled" not in st.session_state:
    st.session_state.auto_refresh_enabled = False  # Start with manual refresh
if "chart_interval" not in st.session_state:
    st.session_state.chart_interval = "1m"
if "max_candles" not in st.session_state:
    st.session_state.max_candles = 100  # Reduced for better performance

# Set refresh interval for real-time updates
REFRESH_INTERVAL = 30  # seconds


def get_positions():
    """Get current positions."""
    try:
        response = backend_api_client.trading.get_positions(limit=100)
        # Handle both response formats
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and response.get("status") == "success":
            return response.get("data", [])
        return []
    except Exception as e:
        st.error(f"Failed to fetch positions: {e}")
        return []


def get_active_orders():
    """Get active orders."""
    try:
        response = backend_api_client.trading.get_active_orders(limit=100)
        # Handle both response formats
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and response.get("status") == "success":
            return response.get("data", [])
        return []
    except Exception as e:
        st.error(f"Failed to fetch active orders: {e}")
        return []


def get_order_history():
    """Get recent order history."""
    try:
        # Try to get orders instead of order_history since that method doesn't exist
        response = backend_api_client.trading.get_orders(limit=50)
        # Handle both response formats
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and response.get("status") == "success":
            return response.get("data", [])
        return []
    except Exception:
        # If get_orders doesn't exist either, just return empty list without warning
        return []


def get_market_data(connector, trading_pair, interval="1m", max_records=100):
    """Get market data with proper error handling."""
    start_time = time.time()
    try:
        # Get candles
        candles = []
        try:
            candles_response = backend_api_client.market_data.get_candles(
                connector=connector,
                trading_pair=trading_pair,
                interval=interval,
                max_records=max_records
            )
            # Handle both response formats
            if isinstance(candles_response, list):
                # Direct list response
                candles = candles_response
            elif isinstance(candles_response, dict) and candles_response.get("status") == "success":
                # Response object with status and data
                candles = candles_response.get("data", [])
        except Exception as e:
            st.warning(f"Could not fetch candles: {e}")

        # Get current price
        prices = {}
        try:
            price_response = backend_api_client.market_data.get_prices(
                connector=connector,
                trading_pairs=[trading_pair]
            )
            # Handle both response formats
            if isinstance(price_response, dict):
                if "status" in price_response and price_response.get("status") == "success":
                    prices = price_response.get("data", {})
                elif "prices" in price_response:
                    # Response has a "prices" field containing the actual price data
                    prices = price_response.get("prices", {})
                else:
                    # Direct dict response with prices
                    prices = price_response
            elif isinstance(price_response, list):
                # If it's a list, try to convert to dict
                prices = {item.get("trading_pair", "unknown"): item.get("price", 0) for item in price_response if
                          isinstance(item, dict)}
        except Exception as e:
            st.warning(f"Could not fetch prices: {e}")

        # Calculate fetch time for performance monitoring
        fetch_time = (time.time() - start_time) * 1000
        st.session_state["last_fetch_time"] = fetch_time
        st.session_state["last_fetch_timestamp"] = time.time()

        return candles, prices
    except Exception as e:
        st.error(f"Failed to fetch market data: {e}")
        return [], {}


def place_order(order_data):
    """Place a trading order."""
    try:
        response = backend_api_client.trading.place_order(**order_data)
        if response.get("status") == "success":
            st.success(f"Order placed successfully! Order ID: {response.get('order_id')}")
            return True
        else:
            st.error(f"Failed to place order: {response.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Failed to place order: {e}")
        return False


def cancel_order(account_name, connector_name, order_id):
    """Cancel an order."""
    try:
        response = backend_api_client.trading.cancel_order(
            account_name=account_name,
            connector_name=connector_name,
            client_order_id=order_id
        )
        if response.get("status") == "success":
            st.success(f"Order {order_id} cancelled successfully!")
            return True
        else:
            st.error(f"Failed to cancel order: {response.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Failed to cancel order: {e}")
        return False


def create_candlestick_chart(candles_data):
    """Create a simple candlestick chart."""
    if not candles_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No candle data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        fig.update_layout(
            template="plotly_dark",
            height=500
        )
        return fig

    try:
        # Convert candles data to DataFrame
        df = pd.DataFrame(candles_data)
        if df.empty:
            return go.Figure()

        # Convert timestamp to datetime for better display
        if 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')

        # Create simple candlestick chart
        fig = go.Figure()

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df['datetime'] if 'datetime' in df.columns else df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name="Price",
                increasing_line_color='#4caf50',
                decreasing_line_color='#f44336'
            )
        )

        # Update layout with dark theme
        fig.update_layout(
            template="plotly_dark",
            height=500,
            showlegend=False,
            title_text="Price Chart",
            title_x=0.5,
            xaxis_title="Time",
            yaxis_title="Price ($)"
        )

        return fig
    except Exception as e:
        # Fallback chart with error message
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error creating chart: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        fig.update_layout(
            template="plotly_dark",
            height=500
        )
        return fig


def render_positions_table(positions_data):
    """Render positions table."""
    if not positions_data:
        st.info("No open positions found.")
        return

    # Convert to DataFrame for better display
    df = pd.DataFrame(positions_data)
    if df.empty:
        st.info("No open positions found.")
        return

    st.subheader("🎯 Open Positions")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "unrealized_pnl": st.column_config.NumberColumn(
                "Unrealized PnL",
                format="$%.2f"
            ),
            "entry_price": st.column_config.NumberColumn(
                "Entry Price",
                format="$%.4f"
            ),
            "mark_price": st.column_config.NumberColumn(
                "Mark Price",
                format="$%.4f"
            ),
            "amount": st.column_config.NumberColumn(
                "Amount",
                format="%.6f"
            )
        }
    )


def render_orders_table(orders_data):
    """Render active orders table."""
    if not orders_data:
        st.info("No active orders found.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(orders_data)
    if df.empty:
        st.info("No active orders found.")
        return

    st.subheader("📋 Active Orders")

    # Add cancel button functionality
    edited_df = st.data_editor(
        df,
        column_config={
            "cancel": st.column_config.CheckboxColumn(
                "Cancel",
                help="Select orders to cancel",
                default=False,
            ),
            "price": st.column_config.NumberColumn(
                "Price",
                format="$%.4f"
            ),
            "amount": st.column_config.NumberColumn(
                "Amount",
                format="%.6f"
            )
        },
        disabled=[col for col in df.columns if col != "cancel"],
        hide_index=True,
        use_container_width=True,
        key="orders_editor"
    )

    # Handle order cancellation
    if "cancel" in edited_df.columns:
        selected_orders = edited_df[edited_df["cancel"]]
        if not selected_orders.empty and st.button(f"❌ Cancel Selected ({len(selected_orders)}) Orders", type="secondary"):
            with st.spinner("Cancelling orders..."):
                for _, order in selected_orders.iterrows():
                    cancel_order(
                        order.get("account_name", ""),
                        order.get("connector_name", ""),
                        order.get("client_order_id", "")
                    )
            st.rerun()


# Page Header
st.header("💹 Trading Hub")
st.caption("Execute trades, monitor positions, and analyze markets")

# Simplified Market Selection
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    market_col1, market_col2 = st.columns(2)
    with market_col1:
        connector = st.selectbox(
            "📡 Exchange",
            ["binance_perpetual", "binance", "kucoin", "okx_perpetual"],
            index=0,
            key="market_connector"
        )
    with market_col2:
        trading_pair = st.text_input(
            "💱 Trading Pair",
            value="BTC-USDT",
            key="market_trading_pair"
        )

    # Update session state when market changes
    if (connector != st.session_state.selected_market["connector"] or
            trading_pair != st.session_state.selected_market["trading_pair"]):
        st.session_state.selected_market = {"connector": connector, "trading_pair": trading_pair}

with col2:
    interval = st.selectbox(
        "⏱️ Interval",
        ["1m", "3m", "5m", "15m", "1h"],
        index=0,
        key="interval_selector"
    )
    st.session_state.chart_interval = interval

with col3:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()


# Simplified display function without auto-refresh
def show_trading_data():
    """Fragment to display trading data with simplified layout."""
    connector = st.session_state.selected_market["connector"]
    trading_pair = st.session_state.selected_market["trading_pair"]
    interval = st.session_state.chart_interval
    max_candles = st.session_state.max_candles

    # Get market data
    candles, prices = get_market_data(
        connector, trading_pair, interval, max_candles
    )

    # Show current price and status
    price_col1, price_col2, price_col3 = st.columns([2, 2, 2])

    with price_col1:
        if prices and trading_pair in prices:
            current_price = prices[trading_pair]
            st.metric(
                f"💰 {trading_pair} Price",
                f"${float(current_price):,.2f}"
            )
        else:
            st.metric(f"💰 {trading_pair} Price", "Loading...")

    with price_col2:
        st.metric("⏱️ Interval", f"{interval}")
        if candles:
            st.caption(f"📈 {len(candles)} candles")

    with price_col3:
        if "last_fetch_time" in st.session_state:
            fetch_time = st.session_state["last_fetch_time"]
            st.metric("⚡ Fetch Time", f"{fetch_time:.0f}ms")

    # Chart section
    st.divider()
    fig = create_candlestick_chart(candles)
    st.plotly_chart(fig, use_container_width=True)

    # Data tables section
    st.divider()

    # Get positions, orders, and history
    positions = get_positions()
    orders = get_active_orders()
    order_history = get_order_history()

    # Display in tabs
    tab1, tab2, tab3 = st.tabs(["📊 Positions", "📋 Active Orders", "📜 Order History"])

    with tab1:
        render_positions_table(positions)
    with tab2:
        render_orders_table(orders)
    with tab3:
        render_order_history_table(order_history)


def render_order_history_table(order_history):
    """Render order history table."""
    if not order_history:
        st.info("No order history found.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(order_history)
    if df.empty:
        st.info("No order history found.")
        return

    st.subheader("📜 Order History")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "price": st.column_config.NumberColumn(
                "Price",
                format="$%.4f"
            ),
            "amount": st.column_config.NumberColumn(
                "Amount",
                format="%.6f"
            ),
            "timestamp": st.column_config.DatetimeColumn(
                "Time",
                format="DD/MM/YYYY HH:mm:ss"
            )
        }
    )


# Call the fragment
show_trading_data()
