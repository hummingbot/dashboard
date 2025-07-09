import time
import datetime
import nest_asyncio

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from frontend.st_utils import get_backend_api_client, initialize_st_page

# Enable nested async
nest_asyncio.apply()


initialize_st_page(
    layout="wide",
    show_readme=False
)

# Initialize backend client
backend_api_client = get_backend_api_client()

# Initialize session state
if "selected_account" not in st.session_state:
    st.session_state.selected_account = None
if "selected_connector" not in st.session_state:
    st.session_state.selected_connector = None
if "selected_market" not in st.session_state:
    st.session_state.selected_market = {"connector": "binance_perpetual", "trading_pair": "BTC-USDT"}
if "candles_connector" not in st.session_state:
    st.session_state.candles_connector = None
if "auto_refresh_enabled" not in st.session_state:
    st.session_state.auto_refresh_enabled = False  # Start with manual refresh
if "chart_interval" not in st.session_state:
    st.session_state.chart_interval = "1m"
if "max_candles" not in st.session_state:
    st.session_state.max_candles = 100  # Reduced for better performance

# Set refresh interval for real-time updates
REFRESH_INTERVAL = 30  # seconds


def get_accounts_and_credentials():
    """Get available accounts and their credentials."""
    try:
        accounts_list = backend_api_client.accounts.list_accounts()
        credentials_list = {}
        for account in accounts_list:
            credentials = backend_api_client.accounts.list_account_credentials(account_name=account)
            credentials_list[account] = credentials
        return accounts_list, credentials_list
    except Exception as e:
        st.error(f"Failed to fetch accounts: {e}")
        return [], {}


def get_candles_connectors():
    """Get available candles feed connectors."""
    try:
        # For now, return a hardcoded list of known exchanges that provide candles
        return ["binance", "binance_perpetual", "kucoin", "okx", "okx_perpetual", "gate_io"]
    except Exception as e:
        st.warning(f"Could not fetch candles feed connectors: {e}")
        return []


def get_positions():
    """Get current positions."""
    try:
        response = backend_api_client.trading.get_positions(limit=100)
        # Handle both response formats
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and response.get("status") == "success":
            return response.get("data", [])
        elif isinstance(response, dict) and "data" in response:
            # Handle the actual API response format
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


def get_order_book(connector, trading_pair, depth=10):
    """Get order book data for the selected trading pair."""
    try:
        response = backend_api_client.market_data.get_order_book(
            connector_name=connector,
            trading_pair=trading_pair,
            depth=depth
        )

        # Handle both response formats
        if isinstance(response, dict):
            if "status" in response and response.get("status") == "success":
                return response.get("data", {})
            elif "bids" in response and "asks" in response:
                return response
        return {}
    except Exception as e:
        st.warning(f"Could not fetch order book: {e}")
        return {}


def get_funding_rate(connector, trading_pair):
    """Get funding rate for perpetual contracts."""
    try:
        # Only try to get funding rate for perpetual connectors
        if "perpetual" in connector.lower():
            response = backend_api_client.market_data.get_funding_info(
                connector_name=connector,
                trading_pair=trading_pair
            )
            # Handle both response formats
            if isinstance(response, dict):
                if "status" in response and response.get("status") == "success":
                    return response.get("data", {})
                elif "funding_rate" in response:
                    return response
            return {}
        return {}
    except Exception as e:
        return {}


def get_trade_history(account_name, connector_name, trading_pair):
    """Get trade history for the selected account and trading pair."""
    try:
        # Try to get trades for this specific account/connector/pair
        response = backend_api_client.trading.get_trades(
            account_name=account_name,
            connector_name=connector_name,
            trading_pair=trading_pair,
            limit=100
        )
        # Handle both response formats
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and response.get("status") == "success":
            return response.get("data", [])
        return []
    except Exception:
        # If method doesn't exist, try alternative approach
        try:
            # Get all orders and filter for filled ones
            orders = get_order_history()
            trades = []
            for order in orders:
                if (order.get("status") == "FILLED" and 
                    order.get("trading_pair") == trading_pair and
                    order.get("connector_name") == connector_name):
                    trades.append(order)
            return trades
        except Exception:
            return []


def get_market_data(connector, trading_pair, interval="1m", max_records=100, candles_connector=None):
    """Get market data with proper error handling."""
    start_time = time.time()
    try:
        # Get candles
        candles = []
        try:
            # Use candles_connector if provided, otherwise use main connector
            candles_conn = candles_connector if candles_connector else connector
            candles_response = backend_api_client.market_data.get_candles(
                connector_name=candles_conn,
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
                connector_name=connector,
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


def get_default_layout(title=None, height=800, width=1100):
    layout = {
        "template": "plotly_dark",
        "plot_bgcolor": 'rgba(0, 0, 0, 0)',  # Transparent background
        "paper_bgcolor": 'rgba(0, 0, 0, 0.1)',  # Lighter shade for the paper
        "font": {"color": 'white', "size": 12},  # Consistent font color and size
        "height": height,
        "width": width,
        "margin": {"l": 20, "r": 20, "t": 50, "b": 20},
        "xaxis_rangeslider_visible": False,
        "hovermode": "x unified",
        "showlegend": False,
    }
    if title:
        layout["title"] = title
    return layout


def create_candlestick_chart(candles_data, connector_name="", trading_pair="", interval="", trades_data=None):
    """Create a candlestick chart with custom theme and trade markers."""
    if not candles_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No candle data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        fig.update_layout(**get_default_layout(height=600))
        return fig

    try:
        # Convert candles data to DataFrame
        df = pd.DataFrame(candles_data)
        if df.empty:
            return go.Figure()

        # Convert timestamp to datetime for better display
        if 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')

        # Create candlestick chart
        fig = go.Figure()

        # Add candlestick trace
        fig.add_trace(
            go.Candlestick(
                x=df['datetime'] if 'datetime' in df.columns else df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name="Candlesticks",
                increasing_line_color='#2ECC71',
                decreasing_line_color='#E74C3C'
            )
        )

        # Add trade markers if trade data is provided
        if trades_data:
            try:
                trades_df = pd.DataFrame(trades_data)
                if not trades_df.empty:
                    # Convert trade timestamps to datetime
                    if 'timestamp' in trades_df.columns:
                        trades_df['datetime'] = pd.to_datetime(trades_df['timestamp'], unit='s')
                    elif 'created_at' in trades_df.columns:
                        trades_df['datetime'] = pd.to_datetime(trades_df['created_at'])
                    elif 'execution_time' in trades_df.columns:
                        trades_df['datetime'] = pd.to_datetime(trades_df['execution_time'])
                    
                    # Filter trades to chart time range if datetime column exists
                    if 'datetime' in trades_df.columns and 'datetime' in df.columns:
                        chart_start = df['datetime'].min()
                        chart_end = df['datetime'].max()
                        
                        trades_in_range = trades_df[
                            (trades_df['datetime'] >= chart_start) & 
                            (trades_df['datetime'] <= chart_end)
                        ]
                        
                        if not trades_in_range.empty:
                            # Separate buy and sell trades
                            buy_trades = trades_in_range[trades_in_range.get('trade_type', trades_in_range.get('side', '')) == 'buy']
                            sell_trades = trades_in_range[trades_in_range.get('trade_type', trades_in_range.get('side', '')) == 'sell']
                            
                            # Add buy markers (green triangles pointing up)
                            if not buy_trades.empty:
                                fig.add_trace(
                                    go.Scatter(
                                        x=buy_trades['datetime'],
                                        y=buy_trades.get('price', buy_trades.get('avg_price', 0)),
                                        mode='markers',
                                        marker=dict(
                                            symbol='triangle-up',
                                            size=10,
                                            color='#2ECC71',
                                            line=dict(width=1, color='white')
                                        ),
                                        name='Buy Trades',
                                        hovertemplate='<b>BUY</b><br>Price: $%{y:.4f}<br>Time: %{x}<extra></extra>'
                                    )
                                )
                            
                            # Add sell markers (red triangles pointing down)
                            if not sell_trades.empty:
                                fig.add_trace(
                                    go.Scatter(
                                        x=sell_trades['datetime'],
                                        y=sell_trades.get('price', sell_trades.get('avg_price', 0)),
                                        mode='markers',
                                        marker=dict(
                                            symbol='triangle-down',
                                            size=10,
                                            color='#E74C3C',
                                            line=dict(width=1, color='white')
                                        ),
                                        name='Sell Trades',
                                        hovertemplate='<b>SELL</b><br>Price: $%{y:.4f}<br>Time: %{x}<extra></extra>'
                                    )
                                )
            except Exception:
                # If trade markers fail, continue without them
                pass

        # Create title
        title = f"{connector_name}: {trading_pair} ({interval})" if connector_name else "Price Chart"

        # Update layout with custom theme
        fig.update_layout(**get_default_layout(title=title, height=600))

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
        fig.update_layout(**get_default_layout(height=600))
        return fig


def create_order_book_chart(order_book_data, current_price=None, depth_percentage=1.0, trading_pair=""):
    """Create an order book histogram with price on Y-axis and volume on X-axis."""
    if not order_book_data or not order_book_data.get("bids") or not order_book_data.get("asks"):
        fig = go.Figure()
        fig.add_annotation(
            text="No order book data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        fig.update_layout(**get_default_layout(title="Order Book", height=600, width=300))
        return fig, None, None

    try:
        bids = order_book_data.get("bids", [])
        asks = order_book_data.get("asks", [])
        
        if not bids or not asks:
            fig = go.Figure()
            fig.add_annotation(
                text="Insufficient order book data",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )
            fig.update_layout(**get_default_layout(title="Order Book", height=600, width=300))
            return fig, None, None

        # Process bids and asks - they're already objects with price/amount keys
        bids_df = pd.DataFrame(bids)
        asks_df = pd.DataFrame(asks)
        
        # Convert to float
        bids_df['price'] = bids_df['price'].astype(float)
        bids_df['amount'] = bids_df['amount'].astype(float)
        asks_df['price'] = asks_df['price'].astype(float)
        asks_df['amount'] = asks_df['amount'].astype(float)
        
        # Convert amounts to quote asset (USDT) for better normalization
        bids_df['quote_volume'] = bids_df['price'] * bids_df['amount']
        asks_df['quote_volume'] = asks_df['price'] * asks_df['amount']
        
        # Sort bids descending (highest price first) and asks ascending (lowest price first)
        bids_df = bids_df.sort_values('price', ascending=False)
        asks_df = asks_df.sort_values('price', ascending=True)
        
        # Calculate cumulative volumes for better visualization
        bids_df['cumulative_volume'] = bids_df['quote_volume'].cumsum()
        asks_df['cumulative_volume'] = asks_df['quote_volume'].cumsum()
        
        # Filter by depth percentage if current price is available
        if current_price:
            price_range = current_price * (depth_percentage / 100)
            min_price = current_price - price_range
            max_price = current_price + price_range
            
            bids_df = bids_df[bids_df['price'] >= min_price]
            asks_df = asks_df[asks_df['price'] <= max_price]
        
        # Create order book chart
        fig = go.Figure()
        
        # Add bid bars (green, all positive values) - using cumulative volume
        if not bids_df.empty:
            fig.add_trace(
                go.Bar(
                    x=bids_df['cumulative_volume'],  # Using cumulative volume
                    y=bids_df['price'],
                    orientation='h',
                    name='Bids',
                    marker=dict(color='#2ECC71', opacity=0.8),
                    hovertemplate='<b>BID</b><br>Price: $%{y:.4f}<br>Cumulative Volume: $%{x:,.0f}<br>Level Volume: $%{customdata:,.0f}<extra></extra>',
                    customdata=bids_df['quote_volume'],  # Show individual level volume in hover
                    offsetgroup='bids'
                )
            )
        
        # Add ask bars (red, all positive values) - using cumulative volume
        if not asks_df.empty:
            fig.add_trace(
                go.Bar(
                    x=asks_df['cumulative_volume'],  # Using cumulative volume
                    y=asks_df['price'],
                    orientation='h',
                    name='Asks',
                    marker=dict(color='#E74C3C', opacity=0.8),
                    hovertemplate='<b>ASK</b><br>Price: $%{y:.4f}<br>Cumulative Volume: $%{x:,.0f}<br>Level Volume: $%{customdata:,.0f}<extra></extra>',
                    customdata=asks_df['quote_volume'],  # Show individual level volume in hover
                    offsetgroup='asks'
                )
            )
        
        
        # Update layout for histogram style
        layout = get_default_layout(title="Order Book Depth", height=600, width=300)
        layout.update({
            "xaxis": {
                "title": "Cumulative Volume (USDT)",
                "color": "white",
                "showgrid": True,
                "gridcolor": "rgba(255,255,255,0.1)",
                "zeroline": True,
                "zerolinecolor": "rgba(255,255,255,0.3)",
                "zerolinewidth": 1
            },
            "yaxis": {
                "title": "Price ($)",
                "color": "white",
                "showgrid": True,
                "gridcolor": "rgba(255,255,255,0.1)",
                "type": "linear"
            },
            "bargap": 0.02,
            "bargroupgap": 0.02,
            "showlegend": False,
            "hovermode": "closest"
        })
        
        fig.update_layout(**layout)
        
        # Return price range for syncing with candles chart
        price_min = None
        price_max = None
        
        if not bids_df.empty and not asks_df.empty:
            price_min = min(bids_df['price'].min(), asks_df['price'].min())
            price_max = max(bids_df['price'].max(), asks_df['price'].max())
        elif not bids_df.empty:
            price_min = price_max = bids_df['price'].min()
        elif not asks_df.empty:
            price_min = price_max = asks_df['price'].max()
        
        return fig, price_min, price_max
    except Exception as e:
        # Fallback chart with error message
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error creating order book: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        fig.update_layout(**get_default_layout(title="Order Book", height=600, width=300))
        return fig, None, None


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
        if not selected_orders.empty and st.button(f"❌ Cancel Selected ({len(selected_orders)}) Orders",
                                                   type="secondary"):
            with st.spinner("Cancelling orders..."):
                for _, order in selected_orders.iterrows():
                    cancel_order(
                        order.get("account_name", ""),
                        order.get("connector_name", ""),
                        order.get("client_order_id", "")
                    )
            st.rerun()


# Page Header
st.title("💹 Trading Hub")
st.caption("Execute trades, monitor positions, and analyze markets")

# Get accounts and credentials
accounts_list, credentials_dict = get_accounts_and_credentials()
candles_connectors = get_candles_connectors()

# Account and Trading Selection Section - Reorganized
selection_col, market_data_col = st.columns([1, 3])

with selection_col:
    st.subheader("🏦 Account & Market")
    
    # All selection in one column
    if accounts_list:
        # Default to first account if not set
        if st.session_state.selected_account is None:
            st.session_state.selected_account = accounts_list[0]

        selected_account = st.selectbox(
            "📱 Account",
            accounts_list,
            index=accounts_list.index(
                st.session_state.selected_account) if st.session_state.selected_account in accounts_list else 0,
            key="account_selector"
        )
        st.session_state.selected_account = selected_account
    else:
        st.error("No accounts found")
        st.stop()

    if selected_account and credentials_dict.get(selected_account):
        credentials = credentials_dict[selected_account]
        
        # Handle different credential formats
        if isinstance(credentials, list) and credentials:
            # If credentials is a list of strings (connector names)
            if isinstance(credentials[0], str):
                # Convert string list to dict format
                credentials = [{"connector_name": cred} for cred in credentials]
            # If credentials is already a list of dicts, use as is
            elif isinstance(credentials[0], dict):
                credentials = credentials
        elif isinstance(credentials, dict):
            # If credentials is a dict, convert to list of dicts
            credentials = [{"connector_name": k, **v} for k, v in credentials.items()]
        else:
            credentials = []
        
        # For simplicity, just use the first credential available
        default_cred = credentials[0] if credentials else None

        if default_cred and credentials:
            connector = st.selectbox(
                "📡 Exchange",
                [cred["connector_name"] for cred in credentials],
                index=0,
                key="connector_selector"
            )
            st.session_state.selected_connector = connector
        else:
            st.error("No credentials found for this account")
            connector = None
    else:
        st.error("No credentials available")
        connector = None

    trading_pair = st.text_input(
        "💱 Trading Pair",
        value="BTC-USDT",
        key="trading_pair_input"
    )

    # Update selected market
    if connector and trading_pair:
        st.session_state.selected_market = {"connector": connector, "trading_pair": trading_pair}

with market_data_col:
    st.subheader("📊 Market Data")
    
    # Only show metrics if we have a selected market
    if st.session_state.selected_market.get("connector") and st.session_state.selected_market.get("trading_pair"):
        # Get market data for metrics
        connector = st.session_state.selected_market["connector"]
        trading_pair = st.session_state.selected_market["trading_pair"]
        interval = st.session_state.chart_interval
        max_candles = st.session_state.max_candles
        candles_connector = st.session_state.candles_connector
        
        # Create sub-columns for organized display
        price_col, depth_col, funding_col, controls_col = st.columns([1, 1, 1, 1])
        
        with price_col:
            candles, prices = get_market_data(
                connector, trading_pair, interval, max_candles, candles_connector
            )
            
            # Get order book data for bid/ask prices and volumes
            order_book = get_order_book(connector, trading_pair, depth=1000)
            
            if order_book and "bids" in order_book and "asks" in order_book:
                bid_price = float(order_book["bids"][0]["price"]) if order_book["bids"] else 0
                ask_price = float(order_book["asks"][0]["price"]) if order_book["asks"] else 0
                mid_price = (bid_price + ask_price) / 2 if bid_price > 0 and ask_price > 0 else 0
                
                st.metric(f"💰 {trading_pair}", f"${mid_price:.4f}")
                st.metric("📈 Bid Price", f"${bid_price:.4f}")
                st.metric("📉 Ask Price", f"${ask_price:.4f}")
            else:
                # Fallback to current price if no order book
                if prices and trading_pair in prices:
                    current_price = prices[trading_pair]
                    st.metric(
                        f"💰 {trading_pair}",
                        f"${float(current_price):,.4f}"
                    )
                else:
                    st.metric(f"💰 {trading_pair}", "Loading...")
        with depth_col:
            # Order book depth configuration
            depth_percentage = st.number_input(
                "📊 Depth ±%",
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.1,
                format="%.1f",
                key="depth_percentage"
            )
            
            # Calculate depth using the actual API method
            if order_book and "bids" in order_book and "asks" in order_book:
                bid_price = float(order_book["bids"][0]["price"]) if order_book["bids"] else 0
                ask_price = float(order_book["asks"][0]["price"]) if order_book["asks"] else 0
                
                if bid_price > 0 and ask_price > 0:
                    # Calculate prices at depth percentage
                    depth_factor = depth_percentage / 100
                    buy_price = bid_price * (1 - depth_factor)  # Price below current bid
                    sell_price = ask_price * (1 + depth_factor)  # Price above current ask
                    
                    try:
                        # Get buy depth (volume available up to buy_price)
                        buy_response = backend_api_client.market_data.get_quote_volume_for_price(
                            connector_name=connector,
                            trading_pair=trading_pair,
                            price=buy_price,
                            is_buy=True
                        )

                        # Get sell depth (volume available up to sell_price)
                        sell_response = backend_api_client.market_data.get_quote_volume_for_price(
                            connector_name=connector,
                            trading_pair=trading_pair,
                            price=sell_price,
                            is_buy=False
                        )
                            
                        # Handle response format based on your example
                        buy_vol = 0
                        sell_vol = 0

                        if isinstance(buy_response, dict) and "result_quote_volume" in buy_response:
                            buy_vol = buy_response["result_quote_volume"]

                        if isinstance(sell_response, dict) and "result_quote_volume" in sell_response:
                            sell_vol = sell_response["result_quote_volume"]

                        st.metric(
                            f"📊 Asks Depth in quote",
                            f"${float(buy_vol):,.0f}"
                        )
                        st.metric(
                            f"📊 Bids Depth in quote",
                            f"${float(sell_vol):,.0f}"
                        )
                    except Exception as e:
                        # Fallback to simple calculation if API fails
                        total_bid_volume = sum(float(bid["amount"] * bid["price"]) for bid in order_book["bids"])
                        total_ask_volume = sum(float(ask["amount"] * ask["price"]) for ask in order_book["asks"])
                        
                        st.metric(
                            f"📊 Asks Depth in quote",
                            f"${total_bid_volume:,.0f}"
                        )
                        st.metric(
                            f"📊 Bids Depth in quote",
                            f"${total_ask_volume:,.0f}"
                        )
                else:
                    st.metric(f"📊 Depth ±{depth_percentage:.1f}%", "No data")
            else:
                st.metric(f"📊 Depth ±{depth_percentage:.1f}%", "No order book")
        
        with funding_col:
            # Funding rate for perpetual contracts
            if "perpetual" in connector.lower():
                funding_data = get_funding_rate(connector, trading_pair)
                if funding_data and "funding_rate" in funding_data:
                    funding_rate = float(funding_data["funding_rate"]) * 100
                    st.metric(
                        "💸 Funding Rate",
                        f"{funding_rate:.4f}%"
                    )
                else:
                    st.metric("💸 Funding Rate", "N/A")
            else:
                st.metric("💸 Funding Rate", "Spot")
        
        with controls_col:
            # Show fetch time and refresh button together
            if "last_fetch_time" in st.session_state:
                fetch_time = st.session_state["last_fetch_time"]
                st.caption(f"⚡ Fetch: {fetch_time:.0f}ms")
            
            # Refresh button
            if st.button("🔄 Refresh", use_container_width=True, type="primary"):
                st.rerun()
    else:
        st.info("Select account and pair to view extended market data")


# Chart fragment with auto-refresh
@st.fragment(run_every=30)  # Auto-refresh every 30 seconds
def show_trading_data():
    """Fragment to display trading data with auto-refresh and chart controls."""
    connector = st.session_state.selected_market.get("connector")
    trading_pair = st.session_state.selected_market.get("trading_pair")

    if not connector or not trading_pair:
        st.warning("Please select an account and trading pair")
        return

    # Chart and Trade Execution section
    st.divider()
    chart_col, orderbook_col, trade_col = st.columns([3, 1, 1])

    # Get market data first (needed for both charts)
    candles, prices = get_market_data(
        connector, trading_pair, st.session_state.chart_interval, 
        st.session_state.max_candles, st.session_state.candles_connector
    )
    
    # Get order book data
    order_book = get_order_book(connector, trading_pair, depth=20)
    
    # Get current price and depth percentage
    current_price = 0.0
    if prices and trading_pair in prices:
        current_price = float(prices[trading_pair])
    depth_percentage = st.session_state.get("depth_percentage", 1.0)

    with chart_col:
        st.subheader("📈 Price Chart")
        
        # Chart controls in the same fragment
        controls_col1, controls_col2, controls_col3 = st.columns([1, 1, 1])
        
        with controls_col1:
            interval = st.selectbox(
                "⏱️ Chart Interval",
                ["1m", "3m", "5m", "15m", "1h", "4h", "1d"],
                index=0,
                key="chart_interval_selector"
            )
            st.session_state.chart_interval = interval

        with controls_col2:
            candles_connectors = get_candles_connectors()
            if candles_connectors:
                # Add option to use same connector as trading
                candles_options = ["Same as trading"] + candles_connectors
                selected_candles = st.selectbox(
                    "📊 Candles Source",
                    candles_options,
                    index=0,
                    key="chart_candles_connector_selector",
                    help="Some exchanges don't provide candles. Select an alternative source."
                )
                st.session_state.candles_connector = None if selected_candles == "Same as trading" else selected_candles
            else:
                st.session_state.candles_connector = None

        with controls_col3:
            max_candles = st.number_input(
                "📈 Max Candles",
                min_value=50,
                max_value=500,
                value=100,
                step=50,
                key="chart_max_candles_input"
            )
            st.session_state.max_candles = max_candles

        # Get trade history for the selected account/connector/pair
        trades = []
        if st.session_state.selected_account and st.session_state.selected_connector:
            trades = get_trade_history(
                st.session_state.selected_account,
                st.session_state.selected_connector,
                trading_pair
            )
        
        # Add small gap before chart
        st.write("")
        
        # Create candlestick chart
        candles_source = st.session_state.candles_connector if st.session_state.candles_connector else connector
        candlestick_fig = create_candlestick_chart(candles, candles_source, trading_pair, interval, trades)

    with orderbook_col:
        st.subheader("📊 Order Book Depth")
        
        
        # Create and display order book chart
        orderbook_fig, price_min, price_max = create_order_book_chart(
            order_book, current_price, depth_percentage, trading_pair
        )
        
    
    # Display both charts
    with chart_col:
        st.plotly_chart(candlestick_fig, use_container_width=True)
        # Show last update time
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        st.caption(f"🔄 Last updated: {current_time} (auto-refresh every 30s)")
        
    with orderbook_col:
        st.plotly_chart(orderbook_fig, use_container_width=True)

    with trade_col:
        st.subheader("💸 Execute Trade")
        
        if st.session_state.selected_account and st.session_state.selected_connector:
            # Get current price for calculations
            current_price = 0.0
            if prices and trading_pair in prices:
                current_price = float(prices[trading_pair])
            
            # Extract base and quote tokens from trading pair
            base_token, quote_token = trading_pair.split('-')
            
            # Order type selection
            order_type = st.selectbox(
                "Order Type",
                ["market", "limit"],
                key="trade_order_type"
            )
            
            # Side selection
            side = st.selectbox(
                "Side",
                ["buy", "sell"],
                key="trade_side"
            )
            
            # Amount input
            amount = st.number_input(
                "Amount",
                min_value=0.0,
                value=0.001,
                format="%.6f",
                key="trade_amount"
            )
            
            # Base/Quote toggle switch
            is_quote = st.toggle(
                f"Amount in {quote_token}",
                value=False,
                help=f"Toggle to enter amount in {quote_token} instead of {base_token}",
                key="trade_is_quote"
            )
            
            # Show conversion line
            if current_price > 0 and amount > 0:
                if is_quote:
                    # User entered quote amount, show base equivalent
                    base_equivalent = amount / current_price
                    st.caption(f"≈ {base_equivalent:.6f} {base_token}")
                else:
                    # User entered base amount, show quote equivalent
                    quote_equivalent = amount * current_price
                    st.caption(f"≈ {quote_equivalent:.2f} {quote_token}")
            
            # Price input for limit orders
            if order_type == "limit":
                default_price = current_price if current_price > 0 else 0.0
                price = st.number_input(
                    "Price",
                    min_value=0.0,
                    value=default_price,
                    format="%.4f",
                    key="trade_price"
                )
                
                # Show updated conversion for limit orders
                if price > 0 and amount > 0:
                    if is_quote:
                        base_equivalent = amount / price
                        st.caption(f"At limit price: ≈ {base_equivalent:.6f} {base_token}")
                    else:
                        quote_equivalent = amount * price
                        st.caption(f"At limit price: ≈ {quote_equivalent:.2f} {quote_token}")
            else:
                price = None
            
            # Submit button
            st.write("")
            if st.button("🚀 Place Order", type="primary", use_container_width=True, key="place_order_btn"):
                if amount > 0:
                    # Convert amount to base if needed
                    final_amount = amount
                    conversion_price = price if order_type == "limit" and price else current_price
                    
                    if is_quote and conversion_price > 0:
                        # Convert quote amount to base amount
                        final_amount = amount / conversion_price
                        st.success(f"Converting {amount} {quote_token} to {final_amount:.6f} {base_token}")
                    
                    order_data = {
                        "account_name": st.session_state.selected_account,
                        "connector_name": st.session_state.selected_connector,
                        "trading_pair": st.session_state.selected_market["trading_pair"],
                        "order_type": order_type,
                        "trade_type": side,
                        "amount": final_amount
                    }
                    if order_type == "limit" and price:
                        order_data["price"] = price
                    
                    with st.spinner("Placing order..."):
                        place_order(order_data)
                else:
                    st.error("Please enter a valid amount")
            
            st.write("")
            st.info(f"🎯 {st.session_state.selected_connector}\n{st.session_state.selected_market['trading_pair']}")
        else:
            st.warning("Please select an account and exchange to execute trades")

    # Data tables section
    st.divider()

    # Get positions, orders, and history
    positions = get_positions()
    orders = get_active_orders()
    order_history = get_order_history()

    # Display in tabs - Balances first
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Balances", "📊 Positions", "📋 Active Orders", "📜 Order History"])

    with tab1:
        render_balances_table()
    with tab2:
        render_positions_table(positions)
    with tab3:
        render_orders_table(orders)
    with tab4:
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


def get_balances():
    """Get account balances."""
    try:
        if not st.session_state.selected_account:
            return []

        # Get portfolio state for the selected account
        portfolio_state = backend_api_client.portfolio.get_state(
            account_names=[st.session_state.selected_account]
        )

        # Extract balances
        balances = []
        if st.session_state.selected_account in portfolio_state:
            for exchange, tokens in portfolio_state[st.session_state.selected_account].items():
                for token_info in tokens:
                    balances.append({
                        "exchange": exchange,
                        "token": token_info["token"],
                        "total": token_info["units"],
                        "available": token_info["available_units"],
                        "price": token_info["price"],
                        "value": token_info["value"]
                    })
        return balances
    except Exception as e:
        st.error(f"Failed to fetch balances: {e}")
        return []


def render_balances_table():
    """Render balances table."""
    balances = get_balances()

    if not balances:
        st.info("No balances found.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(balances)
    if df.empty:
        st.info("No balances found.")
        return

    st.subheader(f"💰 Account Balances - {st.session_state.selected_account}")

    # Calculate total value
    total_value = df['value'].sum()
    st.metric("Total Portfolio Value", f"${total_value:,.2f}")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "total": st.column_config.NumberColumn(
                "Total Balance",
                format="%.6f"
            ),
            "available": st.column_config.NumberColumn(
                "Available",
                format="%.6f"
            ),
            "price": st.column_config.NumberColumn(
                "Price",
                format="$%.4f"
            ),
            "value": st.column_config.NumberColumn(
                "Value (USD)",
                format="$%.2f"
            )
        }
    )


# Trade execution is now integrated with the chart above

# Call the fragment
show_trading_data()
