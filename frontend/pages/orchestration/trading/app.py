import asyncio
import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from frontend.st_utils import get_backend_api_client, initialize_st_page

initialize_st_page(icon="💹", show_readme=False)

# Initialize backend client
backend_api_client = get_backend_api_client()

# Initialize session state
if "selected_market" not in st.session_state:
    st.session_state.selected_market = {"connector": "binance_perpetual", "trading_pair": "BTC-USDT"}
if "auto_refresh_enabled" not in st.session_state:
    st.session_state.auto_refresh_enabled = True
if "order_book_depth" not in st.session_state:
    st.session_state.order_book_depth = 20
if "chart_interval" not in st.session_state:
    st.session_state.chart_interval = "1m"
if "max_candles" not in st.session_state:
    st.session_state.max_candles = 200

# Set refresh interval for real-time updates
REFRESH_INTERVAL = 2  # seconds - faster since candles are cached in memory


async def get_positions():
    """Get current positions."""
    try:
        response = await backend_api_client.trading.get_positions(limit=100)
        if response.get("status") == "success":
            return response.get("data", [])
        return []
    except Exception as e:
        st.error(f"Failed to fetch positions: {e}")
        return []


async def get_active_orders():
    """Get active orders."""
    try:
        response = await backend_api_client.trading.get_active_orders(limit=100)
        if response.get("status") == "success":
            return response.get("data", [])
        return []
    except Exception as e:
        st.error(f"Failed to fetch active orders: {e}")
        return []


async def get_market_data(connector, trading_pair, interval="1m", max_records=200):
    """Get real-time market data including cached candles and order book."""
    try:
        # Get real-time candles from memory cache - very fast updates
        candles_response = await backend_api_client.market_data.get_candles(
            connector=connector,
            trading_pair=trading_pair,
            interval=interval,  # Use configurable interval
            max_records=max_records  # More data for better charts
        )
        
        # Get order book
        order_book_response = await backend_api_client.market_data.get_order_book(
            connector=connector,
            trading_pair=trading_pair,
            depth=st.session_state.order_book_depth
        )
        
        # Get current price
        price_response = await backend_api_client.market_data.get_prices(
            connector=connector,
            trading_pairs=[trading_pair]
        )
        
        # Extract data with better error handling
        candles = []
        order_book = {}
        prices = {}
        
        if candles_response.get("status") == "success":
            candles = candles_response.get("data", [])
        
        if order_book_response.get("status") == "success":
            order_book = order_book_response.get("data", {})
            
        if price_response.get("status") == "success":
            prices = price_response.get("data", {})
        
        return candles, order_book, prices
    except Exception as e:
        st.error(f"Failed to fetch market data: {e}")
        return [], {}, {}


async def place_order(order_data):
    """Place a trading order."""
    try:
        response = await backend_api_client.trading.place_order(**order_data)
        if response.get("status") == "success":
            st.success(f"Order placed successfully! Order ID: {response.get('order_id')}")
            return True
        else:
            st.error(f"Failed to place order: {response.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Failed to place order: {e}")
        return False


async def cancel_order(account_name, connector_name, order_id):
    """Cancel an order."""
    try:
        response = await backend_api_client.trading.cancel_order(
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


def create_candlestick_chart(candles_data, order_book_data):
    """Create candlestick chart with order book overlay."""
    if not candles_data:
        return go.Figure()
    
    # Convert candles data to DataFrame
    df = pd.DataFrame(candles_data)
    if df.empty:
        return go.Figure()
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Price Chart", "Order Book", "Volume", ""),
        specs=[[{"colspan": 1}, {"rowspan": 2}], [{"colspan": 1}, None]],
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="Price",
            increasing_line_color='#4caf50',
            decreasing_line_color='#f44336'
        ),
        row=1, col=1
    )
    
    # Add volume bars
    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=df['volume'],
            name="Volume",
            marker_color='rgba(100, 255, 218, 0.6)'
        ),
        row=2, col=1
    )
    
    # Add order book if available
    if order_book_data and order_book_data.get('bids') and order_book_data.get('asks'):
        bids = order_book_data['bids'][:10]  # Top 10 bids
        asks = order_book_data['asks'][:10]  # Top 10 asks
        
        bid_prices = [float(bid['price']) for bid in bids]
        bid_volumes = [float(bid['amount']) for bid in bids]
        ask_prices = [float(ask['price']) for ask in asks]
        ask_volumes = [float(ask['amount']) for ask in asks]
        
        # Bids (buy orders)
        fig.add_trace(
            go.Bar(
                x=bid_volumes,
                y=bid_prices,
                orientation='h',
                name="Bids",
                marker_color='rgba(76, 175, 80, 0.6)',
                hovertemplate="Price: $%{y:.2f}<br>Volume: %{x:.4f}<extra></extra>"
            ),
            row=1, col=2
        )
        
        # Asks (sell orders)
        fig.add_trace(
            go.Bar(
                x=ask_volumes,
                y=ask_prices,
                orientation='h',
                name="Asks",
                marker_color='rgba(244, 67, 54, 0.6)',
                hovertemplate="Price: $%{y:.2f}<br>Volume: %{x:.4f}<extra></extra>"
            ),
            row=1, col=2
        )
    
    # Update layout with dark theme
    fig.update_layout(
        template="plotly_dark",
        height=600,
        showlegend=False,
        title_text="Market Overview",
        title_x=0.5,
        title_font=dict(size=20, color="#64ffda"),
        paper_bgcolor='rgba(15, 20, 25, 0.8)',
        plot_bgcolor='rgba(15, 20, 25, 0.8)',
    )
    
    # Update x-axes
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_xaxes(title_text="Volume", row=1, col=2)
    
    # Update y-axes
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="Price ($)", row=1, col=2)
    
    return fig


def render_positions_table(positions_data):
    """Render positions in a styled table."""
    if not positions_data:
        st.info("No open positions found.")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(positions_data)
    if df.empty:
        st.info("No open positions found.")
        return
    
    # Style the dataframe
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0f1419 0%, #1a1d23 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        border: 1px solid rgba(100, 255, 218, 0.15);
    ">
    <h4 style="color: #64ffda; margin-bottom: 15px;">🎯 Open Positions</h4>
    </div>
    """, unsafe_allow_html=True)
    
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
    """Render active orders in a styled table."""
    if not orders_data:
        st.info("No active orders found.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(orders_data)
    if df.empty:
        st.info("No active orders found.")
        return
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0f1419 0%, #1a1d23 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        border: 1px solid rgba(100, 255, 218, 0.15);
    ">
    <h4 style="color: #64ffda; margin-bottom: 15px;">📋 Active Orders</h4>
    </div>
    """, unsafe_allow_html=True)
    
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
        selected_orders = edited_df[edited_df["cancel"] == True]
        if not selected_orders.empty and st.button(f"❌ Cancel Selected ({len(selected_orders)}) Orders", type="secondary"):
            with st.spinner("Cancelling orders..."):
                for _, order in selected_orders.iterrows():
                    asyncio.run(cancel_order(
                        order.get("account_name", ""),
                        order.get("connector_name", ""),
                        order.get("client_order_id", "")
                    ))
            st.rerun()


def render_trading_panel():
    """Render the trading panel for placing orders."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0f1419 0%, #1a1d23 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        border: 1px solid rgba(100, 255, 218, 0.15);
        position: relative;
    ">
    <div style="
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #64ffda 0%, #00bcd4 100%);
        border-radius: 15px 15px 0 0;
    "></div>
    <h4 style="color: #64ffda; margin-bottom: 20px; margin-top: 10px;">⚡ Quick Trade</h4>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("trading_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            account_name = st.text_input("Account Name", value="master_account")
            connector_name = st.selectbox(
                "Connector", 
                ["binance_perpetual", "binance", "kucoin", "okx_perpetual"],
                index=0
            )
            trading_pair = st.text_input("Trading Pair", value="BTC-USDT")
        
        with col2:
            side = st.selectbox("Side", ["BUY", "SELL"])
            order_type = st.selectbox("Order Type", ["MARKET", "LIMIT", "LIMIT_MAKER"])
            amount = st.number_input("Amount", min_value=0.0, value=0.001, format="%.6f")
        
        # Conditional price input for limit orders
        price = None
        if order_type in ["LIMIT", "LIMIT_MAKER"]:
            price = st.number_input("Price", min_value=0.0, value=50000.0, format="%.2f")
        
        position_action = st.selectbox("Position Action", ["OPEN", "CLOSE"])
        
        submitted = st.form_submit_button("🚀 Place Order", type="primary", use_container_width=True)
        
        if submitted:
            order_data = {
                "account_name": account_name,
                "connector_name": connector_name,
                "trading_pair": trading_pair,
                "side": side,
                "amount": amount,
                "order_type": order_type,
                "position_action": position_action
            }
            if price is not None:
                order_data["price"] = price
            
            with st.spinner("Placing order..."):
                success = asyncio.run(place_order(order_data))
                if success:
                    time.sleep(1)
                    st.rerun()


# Page Header
st.markdown("""
<div style="
    background: linear-gradient(135deg, #0f1419 0%, #1a1d23 50%, #2d3748 100%);
    padding: 40px;
    border-radius: 20px;
    margin-bottom: 30px;
    text-align: center;
    color: #e2e8f0;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    border: 1px solid rgba(100, 255, 218, 0.1);
    position: relative;
    overflow: hidden;
">
<div style="
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #64ffda 0%, #00bcd4 50%, #64ffda 100%);
"></div>
<h1 style="
    margin: 0; 
    font-size: 3rem; 
    font-weight: 800;
    background: linear-gradient(135deg, #64ffda 0%, #00bcd4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 0 30px rgba(100, 255, 218, 0.5);
">💹 Trading Hub</h1>
<p style="
    margin: 15px 0 0 0; 
    font-size: 1.3rem; 
    opacity: 0.8;
    color: #94a3b8;
    font-weight: 300;
">Execute trades, monitor positions, and analyze markets</p>
</div>
""", unsafe_allow_html=True)

# Market Selection and Controls
col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

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
    order_book_depth = st.selectbox(
        "📊 Book Depth",
        [10, 20, 50, 100],
        index=1,
        key="depth_selector"
    )
    st.session_state.order_book_depth = order_book_depth

with col4:
    if st.button("▶️ Auto" if not st.session_state.auto_refresh_enabled else "⏸️ Stop", 
                 use_container_width=True):
        st.session_state.auto_refresh_enabled = not st.session_state.auto_refresh_enabled

with col5:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()


@st.fragment(run_every=REFRESH_INTERVAL if st.session_state.auto_refresh_enabled else None)
def show_trading_data():
    """Fragment to display trading data with auto-refresh."""
    connector = st.session_state.selected_market["connector"]
    trading_pair = st.session_state.selected_market["trading_pair"]
    
    # Get market data
    candles, order_book, prices = asyncio.run(get_market_data(connector, trading_pair))
    
    # Show current price and refresh status
    price_col1, price_col2, price_col3 = st.columns([2, 2, 2])
    
    with price_col1:
        if prices and trading_pair in prices:
            current_price = prices[trading_pair]
            st.metric(
                f"💰 {trading_pair} Price",
                f"${current_price:,.2f}" if isinstance(current_price, (int, float)) else str(current_price)
            )
        else:
            st.metric(f"💰 {trading_pair} Price", "Loading...")
    
    with price_col2:
        if st.session_state.auto_refresh_enabled:
            st.info(f"🔄 Auto-refresh: {REFRESH_INTERVAL}s")
        else:
            st.empty()
    
    with price_col3:
        st.metric("📊 Order Book Depth", f"{st.session_state.order_book_depth} levels")
    
    # Main layout: Chart + Trading Panel
    chart_col, trading_col = st.columns([3, 1])
    
    with chart_col:
        # Create and display chart
        fig = create_candlestick_chart(candles, order_book)
        st.plotly_chart(fig, use_container_width=True)
    
    with trading_col:
        # Trading panel
        render_trading_panel()
    
    # Positions and Orders section
    st.markdown("---")
    
    # Get positions and orders data
    positions = asyncio.run(get_positions())
    orders = asyncio.run(get_active_orders())
    
    # Display positions and orders
    pos_col, ord_col = st.columns(2)
    
    with pos_col:
        render_positions_table(positions)
    
    with ord_col:
        render_orders_table(orders)


# Call the fragment
show_trading_data()