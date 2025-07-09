import asyncio
import nest_asyncio
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from frontend.st_utils import initialize_st_page, get_backend_api_client
from datetime import datetime, timedelta
from plotly.subplots import make_subplots
import numpy as np

# Enable nested async
nest_asyncio.apply()

# Initialize page
initialize_st_page(
    layout="wide",
    show_readme=False
)

# Session state initialization
if "selected_database" not in st.session_state:
    st.session_state.selected_database = None
if "databases_list" not in st.session_state:
    st.session_state.databases_list = []
if "databases_status" not in st.session_state:
    st.session_state.databases_status = {}
if "show_database_status" not in st.session_state:
    st.session_state.show_database_status = False
if "db_summary" not in st.session_state:
    st.session_state.db_summary = {}
if "db_performance" not in st.session_state:
    st.session_state.db_performance = {}
if "trades_data" not in st.session_state:
    st.session_state.trades_data = []
if "orders_data" not in st.session_state:
    st.session_state.orders_data = []
if "positions_data" not in st.session_state:
    st.session_state.positions_data = []
if "executors_data" not in st.session_state:
    st.session_state.executors_data = []
if "controllers_data" not in st.session_state:
    st.session_state.controllers_data = []
if "page_offset" not in st.session_state:
    st.session_state.page_offset = 0
if "page_limit" not in st.session_state:
    st.session_state.page_limit = 100
if "trade_analysis" not in st.session_state:
    st.session_state.trade_analysis = {}
if "historical_candles" not in st.session_state:
    st.session_state.historical_candles = []

# Get backend client
backend_client = get_backend_api_client()


# Helper functions

def load_databases():
    """Load available databases"""
    try:
        databases = backend_client.archived_bots.list_databases()
        st.session_state.databases_list = databases
        return databases
    except Exception as e:
        st.error(f"Failed to load databases: {str(e)}")
        return []

def load_database_status(db_path: str):
    """Load status for a specific database"""
    try:
        status = backend_client.archived_bots.get_database_status(db_path)
        return status
    except Exception as e:
        return {"status": "error", "error": str(e)}

def load_all_databases_status():
    """Load status for all databases"""
    if not st.session_state.databases_list:
        return
    
    status_dict = {}
    for db_path in st.session_state.databases_list:
        status_dict[db_path] = load_database_status(db_path)
    
    st.session_state.databases_status = status_dict
    return status_dict

def get_healthy_databases():
    """Get list of databases that are not corrupted"""
    healthy_dbs = []
    for db_path, status in st.session_state.databases_status.items():
        # Handle different status formats
        if status.get("status") == "healthy" or status.get("status") == "ok":
            healthy_dbs.append(db_path)
        elif status.get("general_status") == True:
            # Check if all components are "Correct"
            components = ["controllers", "executors", "order_status", "orders", "positions", "trade_fill"]
            all_correct = all(status.get(comp) == "Correct" for comp in components)
            if all_correct:
                healthy_dbs.append(db_path)
    return healthy_dbs

def load_database_summary(db_path: str):
    """Load database summary"""
    try:
        summary = backend_client.archived_bots.get_database_summary(db_path)
        st.session_state.db_summary = summary
        return summary
    except Exception as e:
        st.error(f"Failed to load database summary: {str(e)}")
        return {}

def load_database_performance(db_path: str):
    """Load database performance data"""
    try:
        performance = backend_client.archived_bots.get_database_performance(db_path)
        st.session_state.db_performance = performance
        return performance
    except Exception as e:
        st.error(f"Failed to load performance data: {str(e)}")
        return {}

def load_trades_data(db_path: str, limit: int = 100, offset: int = 0):
    """Load trades data with pagination"""
    try:
        trades = backend_client.archived_bots.get_database_trades(db_path, limit, offset)
        st.session_state.trades_data = trades
        return trades
    except Exception as e:
        st.error(f"Failed to load trades data: {str(e)}")
        return {"trades": [], "total": 0}

def load_orders_data(db_path: str, limit: int = 100, offset: int = 0, status: str = None):
    """Load orders data with pagination"""
    try:
        orders = backend_client.archived_bots.get_database_orders(db_path, limit, offset, status)
        st.session_state.orders_data = orders
        return orders
    except Exception as e:
        st.error(f"Failed to load orders data: {str(e)}")
        return {"orders": [], "total": 0}

def load_positions_data(db_path: str, limit: int = 100, offset: int = 0):
    """Load positions data"""
    try:
        positions = backend_client.archived_bots.get_database_positions(db_path, limit, offset)
        st.session_state.positions_data = positions
        return positions
    except Exception as e:
        st.error(f"Failed to load positions data: {str(e)}")
        return {"positions": [], "total": 0}

def load_executors_data(db_path: str):
    """Load executors data"""
    try:
        executors = backend_client.archived_bots.get_database_executors(db_path)
        st.session_state.executors_data = executors
        return executors
    except Exception as e:
        st.error(f"Failed to load executors data: {str(e)}")
        return {"executors": []}

def load_controllers_data(db_path: str):
    """Load controllers data"""
    try:
        controllers = backend_client.archived_bots.get_database_controllers(db_path)
        st.session_state.controllers_data = controllers
        return controllers
    except Exception as e:
        st.error(f"Failed to load controllers data: {str(e)}")
        return {"controllers": []}

def get_trade_analysis(db_path: str):
    """Get trade analysis including exchanges and trading pairs"""
    try:
        trades = backend_client.archived_bots.get_database_trades(db_path, limit=10000, offset=0)
        if not trades or "trades" not in trades:
            return {"exchanges": [], "trading_pairs": [], "start_time": None, "end_time": None}
        
        trades_data = trades["trades"]
        if not trades_data:
            return {"exchanges": [], "trading_pairs": [], "start_time": None, "end_time": None}
        
        df = pd.DataFrame(trades_data)
        
        # Extract exchanges and trading pairs
        exchanges = df["exchange"].unique().tolist() if "exchange" in df.columns else []
        trading_pairs = df["trading_pair"].unique().tolist() if "trading_pair" in df.columns else []
        
        # Get time range
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            start_time = df["timestamp"].min()
            end_time = df["timestamp"].max()
        else:
            start_time = None
            end_time = None
        
        return {
            "exchanges": exchanges,
            "trading_pairs": trading_pairs,
            "start_time": start_time,
            "end_time": end_time,
            "trades_df": df
        }
    except Exception as e:
        st.error(f"Failed to analyze trades: {str(e)}")
        return {"exchanges": [], "trading_pairs": [], "start_time": None, "end_time": None}

def get_historical_candles(exchange: str, trading_pair: str, start_time: datetime, end_time: datetime, interval: str = "5m"):
    """Get historical candle data for the specified period"""
    try:
        # Add buffer time for candles
        buffer_time = timedelta(hours=2)  # 2 hours buffer for 20 candles at 5min = 100 minutes
        extended_start = start_time - buffer_time
        extended_end = end_time + buffer_time
        
        # Call backend API to get historical candles
        candles = backend_client.archived_bots.get_historical_candles(
            exchange=exchange,
            trading_pair=trading_pair,
            start_time=extended_start.isoformat(),
            end_time=extended_end.isoformat(),
            interval=interval
        )
        
        return candles
    except Exception as e:
        st.error(f"Failed to get historical candles: {str(e)}")
        return []

def create_performance_chart(performance_data: Dict[str, Any]):
    """Create performance visualization chart"""
    if not performance_data or "daily_pnl" not in performance_data:
        return None
    
    daily_pnl = performance_data["daily_pnl"]
    if not daily_pnl:
        return None
    
    df = pd.DataFrame(daily_pnl)
    
    fig = go.Figure()
    
    # Add cumulative PnL line
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["cumulative_pnl"],
        mode="lines+markers",
        name="Cumulative PnL",
        line=dict(width=2),
        marker=dict(size=4)
    ))
    
    fig.update_layout(title="Daily PnL Performance", height=400)
    return fig

def create_trades_chart(trades_data: List[Dict[str, Any]]):
    """Create trades visualization"""
    if not trades_data:
        return None
    
    df = pd.DataFrame(trades_data)
    
    fig = go.Figure()
    
    # Group by date and sum volume
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date
    daily_volume = df.groupby("date")["amount"].sum().reset_index()
    
    fig.add_trace(go.Bar(
        x=daily_volume["date"],
        y=daily_volume["amount"],
        name="Daily Volume"
    ))
    
    fig.update_layout(title="Trade Volume Over Time", height=400)
    return fig

def get_default_layout(title=None, height=800, width=1200):
    """Get default layout inspired by backtesting result"""
    layout = {
        "template": "plotly_dark",
        "plot_bgcolor": 'rgba(0, 0, 0, 0)',
        "paper_bgcolor": 'rgba(0, 0, 0, 0.1)',
        "font": {"color": 'white', "size": 12},
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

def add_trades_to_chart(fig, trades_data: List[Dict[str, Any]], row=1, col=1):
    """Add trade lines to chart inspired by backtesting result"""
    if not trades_data:
        return fig
    
    trades_df = pd.DataFrame(trades_data)
    trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"])
    
    # Calculate cumulative PnL for each trade
    if "pnl" in trades_df.columns:
        trades_df["cumulative_pnl"] = trades_df["pnl"].cumsum()
    else:
        trades_df["cumulative_pnl"] = 0
    
    # Group trades by time intervals to show trade lines
    for idx, trade in trades_df.iterrows():
        trade_time = trade["timestamp"]
        trade_price = trade["price"]
        
        # Determine trade type
        is_buy = False
        if "trade_type" in trade:
            is_buy = trade["trade_type"] == "BUY"
        elif "side" in trade:
            is_buy = trade["side"] == "BUY"
        
        # Calculate PnL for color
        pnl = trade.get("pnl", 0)
        if pnl > 0:
            color = "green"
        elif pnl < 0:
            color = "red"
        else:
            color = "grey"
        
        # Add trade marker
        fig.add_trace(go.Scatter(
            x=[trade_time],
            y=[trade_price],
            mode="markers",
            marker=dict(
                symbol="triangle-up" if is_buy else "triangle-down",
                size=10,
                color=color,
                line=dict(width=1, color=color)
            ),
            name=f"{'Buy' if is_buy else 'Sell'} Trade",
            showlegend=False,
            hovertemplate=f"<b>{'Buy' if is_buy else 'Sell'} Trade</b><br>" +
                        f"Time: %{{x}}<br>" +
                        f"Price: ${trade_price:.4f}<br>" +
                        f"Amount: {trade.get('amount', 0):.4f}<br>" +
                        f"PnL: ${pnl:.4f}<br>" +
                        "<extra></extra>"
        ), row=row, col=col)
    
    return fig

def get_pnl_trace(trades_data: List[Dict[str, Any]]):
    """Get PnL trace for trades"""
    if not trades_data:
        return None
    
    trades_df = pd.DataFrame(trades_data)
    trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"])
    
    # Calculate cumulative PnL
    if "pnl" in trades_df.columns:
        pnl_values = trades_df["pnl"].values
    else:
        pnl_values = [0] * len(trades_df)
    
    cum_pnl = np.cumsum(pnl_values)
    
    return go.Scatter(
        x=trades_df["timestamp"],
        y=cum_pnl,
        mode='lines',
        line=dict(color='gold', width=2),
        name='Cumulative PnL'
    )

def create_enhanced_performance_chart(candles_data: List[Dict[str, Any]], trades_data: List[Dict[str, Any]], trading_pair: str = ""):
    """Create enhanced performance chart with candles and trades inspired by backtesting result"""
    if not candles_data:
        return None
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.02, 
        subplot_titles=('Price Action', 'Cumulative PnL'),
        row_heights=[0.7, 0.3]
    )
    
    # Add candlestick chart
    candles_df = pd.DataFrame(candles_data)
    candles_df["timestamp"] = pd.to_datetime(candles_df["timestamp"])
    
    fig.add_trace(go.Candlestick(
        x=candles_df["timestamp"],
        open=candles_df["open"],
        high=candles_df["high"],
        low=candles_df["low"],
        close=candles_df["close"],
        name="Price"
    ), row=1, col=1)
    
    # Add trades to price chart
    if trades_data:
        fig = add_trades_to_chart(fig, trades_data, row=1, col=1)
        
        # Add PnL trace to bottom chart
        pnl_trace = get_pnl_trace(trades_data)
        if pnl_trace:
            fig.add_trace(pnl_trace, row=2, col=1)
    
    # Apply theme layout
    layout_settings = get_default_layout(f"Trading Performance: {trading_pair}")
    fig.update_layout(**layout_settings)
    
    # Update axis properties
    fig.update_xaxes(rangeslider_visible=False, row=1, col=1)
    fig.update_xaxes(row=2, col=1)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Cumulative PnL", row=2, col=1)
    
    return fig

# Page header
st.title("🗃️ Archived Bots")
st.write("Access and analyze historical bot database files and trading performance")

# Load databases on first run
if not st.session_state.databases_list:
    with st.spinner("Loading databases..."):
        load_databases()
        if st.session_state.show_database_status:
            load_all_databases_status()

# Database status toggle
st.header("📁 Database Management")

col1, col2 = st.columns([3, 1])

with col1:
    show_status = st.toggle(
        "Show Database Status",
        value=st.session_state.show_database_status,
        help="Toggle to view status of all databases"
    )
    st.session_state.show_database_status = show_status

with col2:
    if st.button("🔄 Refresh List", use_container_width=True):
        with st.spinner("Refreshing..."):
            load_databases()
            if st.session_state.show_database_status:
                load_all_databases_status()
            st.rerun()

# Show database status if toggle is enabled
if st.session_state.show_database_status:
    st.subheader("Database Status")
    
    if st.session_state.databases_list:
        # Load status if not already loaded
        if not st.session_state.databases_status:
            with st.spinner("Loading database status..."):
                load_all_databases_status()
        
        # Display status table
        if st.session_state.databases_status:
            status_data = []
            for db_path, status in st.session_state.databases_status.items():
                # Determine overall status
                overall_status = "unknown"
                if status.get("status") in ["healthy", "ok"]:
                    overall_status = status.get("status")
                elif status.get("general_status") == True:
                    components = ["controllers", "executors", "order_status", "orders", "positions", "trade_fill"]
                    all_correct = all(status.get(comp) == "Correct" for comp in components)
                    overall_status = "healthy" if all_correct else "partial"
                elif status.get("error"):
                    overall_status = "error"
                
                status_data.append({
                    "Database": db_path,
                    "Status": overall_status,
                    "Size (MB)": status.get("size_mb", "N/A"),
                    "Last Modified": status.get("last_modified", "N/A"),
                    "Error": status.get("error", "")
                })
            
            df = pd.DataFrame(status_data)
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("No databases found. Please check your archived bots directory.")

# Database selection
st.subheader("Select Database")

if st.session_state.databases_list:
    # Load status if not already loaded (needed for filtering)
    if not st.session_state.databases_status:
        with st.spinner("Loading database status..."):
            load_all_databases_status()
    
    # Get healthy databases for selection
    healthy_databases = get_healthy_databases()
    
    if healthy_databases:
        selected_db = st.selectbox(
            "Select Database (Healthy only)",
            options=healthy_databases,
            key="db_selector",
            help="Choose a healthy database to analyze"
        )
        
        if selected_db and selected_db != st.session_state.selected_database:
            st.session_state.selected_database = selected_db
            # Reset data when database changes
            st.session_state.db_summary = {}
            st.session_state.db_performance = {}
            st.session_state.trades_data = []
            st.session_state.orders_data = []
            st.session_state.positions_data = []
            st.session_state.executors_data = []
            st.session_state.controllers_data = []
            st.session_state.page_offset = 0
            st.session_state.trade_analysis = {}
            st.session_state.historical_candles = []
            st.rerun()
    else:
        st.warning("No healthy databases found. Please check the database status above.")

else:
    st.warning("No databases found. Please check your archived bots directory.")

# Main content - only show if database is selected
if st.session_state.selected_database:
    db_path = st.session_state.selected_database
    
    # Load database summary if not already loaded
    if not st.session_state.db_summary:
        with st.spinner("Loading database summary..."):
            load_database_summary(db_path)
    
    # Database status section
    st.header("📊 Database Overview")
    
    if st.session_state.db_summary:
        summary = st.session_state.db_summary
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Trades",
                value=summary.get("total_trades", 0)
            )
        
        with col2:
            st.metric(
                "Total Orders", 
                value=summary.get("total_orders", 0)
            )
        
        with col3:
            st.metric(
                "Active Positions",
                value=summary.get("active_positions", 0)
            )
        
        with col4:
            st.metric(
                "Controllers",
                value=summary.get("total_controllers", 0)
            )
        
        # Database info
        if "database_info" in summary:
            db_info = summary["database_info"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Database Size",
                    f"{db_info.get('size_mb', 0):.2f} MB"
                )
            
            with col2:
                st.metric(
                    "Last Modified",
                    db_info.get("last_modified", "Unknown")
                )
    
    # Tabs for different data views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Performance", 
        "💹 Trades", 
        "📋 Orders", 
        "📍 Positions", 
        "⚙️ Executors", 
        "🎛️ Controllers"
    ])
    
    with tab1:
        st.subheader("Performance Analysis")
        
        # Load performance data if not already loaded
        if not st.session_state.db_performance:
            with st.spinner("Loading performance data..."):
                load_database_performance(db_path)
        
        if st.session_state.db_performance:
            performance = st.session_state.db_performance
            
            # Performance metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total PnL",
                    value=f"${performance.get('total_pnl', 0):,.2f}",
                    delta=f"{performance.get('pnl_change_pct', 0):.1f}%"
                )
            
            with col2:
                st.metric(
                    "Win Rate",
                    value=f"{performance.get('win_rate', 0):.1f}%"
                )
            
            with col3:
                st.metric(
                    "Max Drawdown",
                    value=f"${performance.get('max_drawdown', 0):,.2f}"
                )
            
            with col4:
                st.metric(
                    "Sharpe Ratio",
                    value=f"{performance.get('sharpe_ratio', 0):.2f}"
                )
            
            # Enhanced performance analysis
            st.subheader("Enhanced Trading Analysis")
            
            # Load trade analysis if not already loaded
            if not st.session_state.trade_analysis:
                with st.spinner("Analyzing trades..."):
                    st.session_state.trade_analysis = get_trade_analysis(db_path)
            
            analysis = st.session_state.trade_analysis
            
            if analysis.get("exchanges") and analysis.get("trading_pairs"):
                # Show exchange and trading pair info
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"**Exchanges:** {', '.join(analysis['exchanges'])}")
                
                with col2:
                    st.info(f"**Trading Pairs:** {', '.join(analysis['trading_pairs'])}")
                
                # Select exchange and trading pair for candle analysis
                if len(analysis["exchanges"]) > 1:
                    selected_exchange = st.selectbox(
                        "Select Exchange for Candle Analysis",
                        options=analysis["exchanges"]
                    )
                else:
                    selected_exchange = analysis["exchanges"][0]
                
                if len(analysis["trading_pairs"]) > 1:
                    selected_pair = st.selectbox(
                        "Select Trading Pair for Candle Analysis",
                        options=analysis["trading_pairs"]
                    )
                else:
                    selected_pair = analysis["trading_pairs"][0]
                
                # Candle interval selection
                candle_interval = st.selectbox(
                    "Candle Interval",
                    options=["1m", "5m", "15m", "1h"],
                    index=1,  # Default to 5m
                    help="Select the candle interval for analysis"
                )
                
                # Button to load enhanced chart
                if st.button("🔄 Load Enhanced Chart with Candles", use_container_width=True):
                    if analysis.get("start_time") and analysis.get("end_time"):
                        with st.spinner("Loading historical candles..."):
                            candles = get_historical_candles(
                                selected_exchange,
                                selected_pair,
                                analysis["start_time"],
                                analysis["end_time"],
                                candle_interval
                            )
                            st.session_state.historical_candles = candles
                
                # Display enhanced chart if candles are available
                if st.session_state.historical_candles:
                    trades_data = analysis.get("trades_df", pd.DataFrame())
                    trades_list = trades_data.to_dict("records") if not trades_data.empty else []
                    
                    enhanced_chart = create_enhanced_performance_chart(
                        st.session_state.historical_candles,
                        trades_list,
                        selected_pair
                    )
                    
                    if enhanced_chart:
                        st.plotly_chart(enhanced_chart, use_container_width=True)
                    else:
                        st.warning("Unable to create enhanced chart. Check candle data format.")
                else:
                    st.info("Click 'Load Enhanced Chart' to view candles with trades overlay.")
            else:
                st.warning("No trade data available for enhanced analysis.")
            
            # Original performance chart
            st.subheader("Daily PnL Performance")
            chart = create_performance_chart(performance)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
        
        else:
            st.warning("No performance data available for this database.")
    
    with tab2:
        st.subheader("Trade History")
        
        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("◀️ Previous", disabled=st.session_state.page_offset <= 0):
                st.session_state.page_offset = max(0, st.session_state.page_offset - st.session_state.page_limit)
                st.rerun()
        
        with col2:
            page_num = (st.session_state.page_offset // st.session_state.page_limit) + 1
            st.write(f"Page {page_num}")
        
        with col3:
            if st.button("Next ▶️"):
                st.session_state.page_offset += st.session_state.page_limit
                st.rerun()
        
        # Load trades data
        if st.button("🔄 Load Trades", use_container_width=True):
            with st.spinner("Loading trades..."):
                load_trades_data(db_path, st.session_state.page_limit, st.session_state.page_offset)
        
        if st.session_state.trades_data and "trades" in st.session_state.trades_data:
            trades = st.session_state.trades_data["trades"]
            
            if trades:
                # Create trades dataframe
                df = pd.DataFrame(trades)
                
                # Display trades table
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=400
                )
                
                # Trades chart
                chart = create_trades_chart(trades)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
            else:
                st.info("No trades found in this database.")
    
    with tab3:
        st.subheader("Order History")
        
        # Order status filter
        col1, col2 = st.columns([3, 1])
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                options=["All", "FILLED", "PARTIALLY_FILLED", "CANCELLED", "PENDING"],
                help="Filter orders by their execution status"
            )
        
        with col2:
            if st.button("🔄 Load Orders", use_container_width=True):
                with st.spinner("Loading orders..."):
                    status = None if status_filter == "All" else status_filter
                    load_orders_data(db_path, st.session_state.page_limit, st.session_state.page_offset, status)
        
        if st.session_state.orders_data and "orders" in st.session_state.orders_data:
            orders = st.session_state.orders_data["orders"]
            
            if orders:
                df = pd.DataFrame(orders)
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("No orders found matching the selected criteria.")
    
    with tab4:
        st.subheader("Position History")
        
        if st.button("🔄 Load Positions", use_container_width=True):
            with st.spinner("Loading positions..."):
                load_positions_data(db_path, st.session_state.page_limit, st.session_state.page_offset)
        
        if st.session_state.positions_data and "positions" in st.session_state.positions_data:
            positions = st.session_state.positions_data["positions"]
            
            if positions:
                df = pd.DataFrame(positions)
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("No positions found in this database.")
    
    with tab5:
        st.subheader("Executor Analysis")
        
        if st.button("🔄 Load Executors", use_container_width=True):
            with st.spinner("Loading executors..."):
                load_executors_data(db_path)
        
        if st.session_state.executors_data and "executors" in st.session_state.executors_data:
            executors = st.session_state.executors_data["executors"]
            
            if executors:
                df = pd.DataFrame(executors)
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("No executors found in this database.")
    
    with tab6:
        st.subheader("Controller Configuration")
        
        if st.button("🔄 Load Controllers", use_container_width=True):
            with st.spinner("Loading controllers..."):
                load_controllers_data(db_path)
        
        if st.session_state.controllers_data and "controllers" in st.session_state.controllers_data:
            controllers = st.session_state.controllers_data["controllers"]
            
            if controllers:
                for i, controller in enumerate(controllers):
                    with st.expander(f"Controller {i+1}: {controller.get('controller_name', 'Unknown')}"):
                        st.json(controller)
            else:
                st.info("No controllers found in this database.")

else:
    st.info("Please select a database to begin analysis.")

# Auto-refresh fragment for database list
@st.fragment(run_every=30)
def auto_refresh_databases():
    """Auto-refresh database list every 30 seconds"""
    if st.session_state.get("auto_refresh_enabled", False):
        load_databases()

# Auto-refresh toggle
st.sidebar.markdown("### ⚙️ Settings")
auto_refresh = st.sidebar.checkbox(
    "Auto-refresh database list",
    value=st.session_state.get("auto_refresh_enabled", False),
    help="Automatically refresh the database list every 30 seconds"
)
st.session_state.auto_refresh_enabled = auto_refresh

if auto_refresh:
    auto_refresh_databases()

# Export functionality
if st.session_state.selected_database:
    st.sidebar.markdown("### 📤 Export Data")
    
    export_format = st.sidebar.selectbox(
        "Export Format",
        options=["CSV", "JSON", "Excel"],
        help="Choose the format for data export"
    )
    
    if st.sidebar.button("📥 Export Current Data", use_container_width=True):
        try:
            # Implementation would depend on the specific data to export
            st.sidebar.success("Export functionality would be implemented here")
        except Exception as e:
            st.sidebar.error(f"Export failed: {str(e)}")

# Help section
st.sidebar.markdown("### ❓ Help")
st.sidebar.info(
    "💡 **Tips:**\n"
    "- Select a database to start analyzing\n"
    "- Use tabs to navigate different data views\n"
    "- Enable auto-refresh for real-time updates\n"
    "- Use pagination for large datasets\n"
    "- Export data for external analysis"
)