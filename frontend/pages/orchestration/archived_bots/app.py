import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import nest_asyncio
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from frontend.st_utils import get_backend_api_client, initialize_st_page

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
if "bot_runs" not in st.session_state:
    st.session_state.bot_runs = []

# Get backend client
backend_client = get_backend_api_client()


# Helper functions

def detect_timestamp_unit(timestamps):
    """Detect if timestamps are in seconds or milliseconds"""
    if hasattr(timestamps, 'empty') and timestamps.empty:
        return 'ms'  # default to milliseconds
    if not hasattr(timestamps, '__iter__') or len(timestamps) == 0:
        return 'ms'  # default to milliseconds
    
    # Take a sample timestamp
    sample_ts = timestamps[0] if hasattr(timestamps, '__iter__') else timestamps
    
    # If timestamp is greater than 1e10, it's likely milliseconds
    # (1e10 corresponds to year 2001 in seconds, year 1970 in milliseconds)
    if sample_ts > 1e10:
        return 'ms'
    else:
        return 's'

def safe_to_datetime(timestamps, default_unit='ms'):
    """Safely convert timestamps to datetime, auto-detecting unit"""
    if pd.isna(timestamps).all():
        return timestamps
    
    # Check if already datetime
    if hasattr(timestamps, 'dtype') and pd.api.types.is_datetime64_any_dtype(timestamps):
        return timestamps
    
    # Check if Series contains datetime objects
    if hasattr(timestamps, '__iter__') and not isinstance(timestamps, str):
        first_valid = timestamps.dropna().iloc[0] if hasattr(timestamps, 'dropna') else next((t for t in timestamps if pd.notna(t)), None)
        if first_valid is not None and isinstance(first_valid, (pd.Timestamp, datetime)):
            return timestamps
    
    # Handle series/array
    if hasattr(timestamps, '__iter__') and not isinstance(timestamps, str):
        non_null_ts = timestamps.dropna() if hasattr(timestamps, 'dropna') else [t for t in timestamps if pd.notna(t)]
        if len(non_null_ts) == 0:
            return pd.to_datetime(timestamps)
        unit = detect_timestamp_unit(non_null_ts)
    else:
        unit = detect_timestamp_unit([timestamps])
    
    return pd.to_datetime(timestamps, unit=unit)

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
        # Check if 'healthy' field exists at the top level
        if status.get("healthy") == True:
            healthy_dbs.append(db_path)
        # Handle different status formats as fallback
        elif status.get("status") == "healthy" or status.get("status") == "ok":
            healthy_dbs.append(db_path)
        elif "status" in status and isinstance(status["status"], dict):
            # Check if general_status is true in nested status
            if status["status"].get("general_status") == True:
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
        exchanges = df["connector_name"].unique().tolist() if "connector_name" in df.columns else []
        trading_pairs = df["trading_pair"].unique().tolist() if "trading_pair" in df.columns else []
        
        # Get time range
        if "timestamp" in df.columns:
            # Convert timestamps to datetime with auto-detection
            df["timestamp"] = safe_to_datetime(df["timestamp"])
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

def load_bot_runs():
    """Load bot runs data"""
    try:
        bot_runs = backend_client.bot_orchestration.get_bot_runs(limit=1000, offset=0)
        if bot_runs and "data" in bot_runs:
            st.session_state.bot_runs = bot_runs["data"]
            return bot_runs["data"]
        else:
            st.session_state.bot_runs = []
            return []
    except Exception as e:
        st.warning(f"Could not load bot runs: {str(e)}")
        return []

def find_matching_bot_run(db_path: str, bot_runs: List[Dict]):
    """Find the bot run that matches the database file"""
    if not bot_runs:
        return None
    
    # Extract bot name from database path
    # Format: "bots/archived/askarabuuut-20250710-0013/data/askarabuuut-20250710-0013-20250710-001318.sqlite"
    try:
        filename = db_path.split("/")[-1]  # Get filename
        bot_name = filename.split("-20")[0]  # Extract bot name before timestamp
        
        # Find matching bot run
        for run in bot_runs:
            if run.get("bot_name", "").startswith(bot_name):
                return run
        
        return None
    except Exception:
        return None

def create_bot_runs_scatterplot(bot_runs: List[Dict], healthy_databases: List[str]):
    """Create a scatterplot visualization of bot runs with performance data"""
    if not bot_runs:
        return None
    
    # Prepare data for plotting
    plot_data = []
    
    for run in bot_runs:
        try:
            # Parse final status to get performance data
            final_status = json.loads(run.get("final_status", "{}"))
            performance = final_status.get("performance", {})
            
            # Extract performance metrics
            global_pnl = 0
            volume_traded = 0
            realized_pnl = 0
            unrealized_pnl = 0
            
            for controller_name, controller_perf in performance.items():
                if isinstance(controller_perf, dict) and "performance" in controller_perf:
                    perf_data = controller_perf["performance"]
                    global_pnl += perf_data.get("global_pnl_quote", 0)
                    volume_traded += perf_data.get("volume_traded", 0)
                    realized_pnl += perf_data.get("realized_pnl_quote", 0)
                    unrealized_pnl += perf_data.get("unrealized_pnl_quote", 0)
            
            # Calculate duration
            deployed_at = pd.to_datetime(run.get("deployed_at", ""))
            stopped_at = pd.to_datetime(run.get("stopped_at", ""))
            duration_hours = (stopped_at - deployed_at).total_seconds() / 3600 if deployed_at and stopped_at else 0
            
            # Check if database is available
            has_database = any(run.get("bot_name", "") in db for db in healthy_databases)
            
            plot_data.append({
                "bot_name": run.get("bot_name", "Unknown"),
                "strategy": run.get("strategy_name", "Unknown"),
                "global_pnl": global_pnl,
                "volume_traded": volume_traded,
                "realized_pnl": realized_pnl,
                "unrealized_pnl": unrealized_pnl,
                "duration_hours": duration_hours,
                "deployed_at": deployed_at,
                "stopped_at": stopped_at,
                "run_status": run.get("run_status", "Unknown"),
                "deployment_status": run.get("deployment_status", "Unknown"),
                "account": run.get("account_name", "Unknown"),
                "has_database": has_database,
                "bot_id": run.get("id", 0)
            })
            
        except Exception as e:
            continue
    
    if not plot_data:
        return None
    
    df = pd.DataFrame(plot_data)
    
    # Create scatter plot
    fig = go.Figure()
    
    # Add traces for runs with and without databases
    for has_db, label, color, symbol in [(True, "With Database", "#4CAF50", "circle"), 
                                         (False, "No Database", "#9E9E9E", "circle-open")]:
        subset = df[df["has_database"] == has_db]
        if not subset.empty:
            fig.add_trace(go.Scatter(
                x=subset["volume_traded"],
                y=subset["global_pnl"],
                mode="markers",
                name=label,
                marker=dict(
                    size=subset["duration_hours"].apply(lambda x: max(8, min(x * 2, 50))),
                    color=color,
                    symbol=symbol,
                    line=dict(width=2, color="white"),
                    opacity=0.8
                ),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>" +
                    "Strategy: %{customdata[1]}<br>" +
                    "Global PnL: $%{y:.4f}<br>" +
                    "Volume: $%{x:,.0f}<br>" +
                    "Realized PnL: $%{customdata[2]:.4f}<br>" +
                    "Unrealized PnL: $%{customdata[3]:.4f}<br>" +
                    "Duration: %{customdata[4]:.1f}h<br>" +
                    "Deployed: %{customdata[5]}<br>" +
                    "Stopped: %{customdata[6]}<br>" +
                    "Status: %{customdata[7]} / %{customdata[8]}<br>" +
                    "Account: %{customdata[9]}<br>" +
                    "<extra></extra>"
                ),
                customdata=subset[["bot_name", "strategy", "realized_pnl", "unrealized_pnl", 
                                 "duration_hours", "deployed_at", "stopped_at", "run_status", 
                                 "deployment_status", "account"]].values
            ))
    
    # Update layout
    fig.update_layout(
        title="Bot Runs Performance Overview",
        xaxis_title="Volume Traded ($)",
        yaxis_title="Global PnL ($)",
        template="plotly_dark",
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0.1)',
        font=dict(color='white', size=12),
        height=600,
        hovermode="closest",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Add quadrant lines
    fig.add_hline(y=0, line=dict(color="gray", width=1, dash="dash"), opacity=0.5)
    fig.add_vline(x=0, line=dict(color="gray", width=1, dash="dash"), opacity=0.5)
    
    return fig, df

def get_historical_candles(connector_name: str, trading_pair: str, start_time: datetime, end_time: datetime, interval: str = "5m"):
    """Get historical candle data for the specified period"""
    try:
        # Add buffer time for candles
        buffer_time = timedelta(hours=1)  # 2 hours buffer for 20 candles at 5min = 100 minutes
        extended_start = start_time - buffer_time
        extended_end = end_time + buffer_time
        
        # Call backend API to get historical candles using market_data service
        candles = backend_client.market_data.get_historical_candles(
            connector_name=connector_name,
            trading_pair=trading_pair,
            interval=interval,
            start_time=int(extended_start.timestamp()),
            end_time=int(extended_end.timestamp())
        )
        
        return candles
    except Exception as e:
        st.error(f"Failed to get historical candles: {str(e)}")
        return []

def create_performance_chart(performance_data: Dict[str, Any]):
    """Create performance visualization chart"""
    if not performance_data or "performance_data" not in performance_data:
        return None
    
    perf_data = performance_data["performance_data"]
    if not perf_data:
        return None
    
    df = pd.DataFrame(perf_data)
    
    # Convert timestamp to datetime with auto-detection
    df["timestamp"] = safe_to_datetime(df["timestamp"])
    
    fig = go.Figure()
    
    # Add net PnL line
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["net_pnl_quote"],
        mode="lines+markers",
        name="Net PnL",
        line=dict(width=2, color='#4CAF50'),
        marker=dict(size=4)
    ))
    
    # Add realized PnL line
    if "realized_trade_pnl_quote" in df.columns:
        # Calculate cumulative realized PnL
        df["cumulative_realized_pnl"] = df["realized_trade_pnl_quote"].cumsum()
        fig.add_trace(go.Scatter(
            x=df["timestamp"],
            y=df["cumulative_realized_pnl"],
            mode="lines",
            name="Cumulative Realized PnL",
            line=dict(width=2, color='#2196F3')
        ))
    
    # Add unrealized PnL line  
    if "unrealized_trade_pnl_quote" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["timestamp"],
            y=df["unrealized_trade_pnl_quote"],
            mode="lines",
            name="Unrealized PnL",
            line=dict(width=1, color='#FF9800')
        ))
    
    fig.update_layout(
        title="Trading Performance Over Time",
        height=400,
        template='plotly_dark',
        xaxis_title="Time",
        yaxis_title="PnL (Quote)",
        showlegend=True
    )
    return fig

def create_trades_chart(trades_data: List[Dict[str, Any]]):
    """Create trades visualization"""
    if not trades_data:
        return None
    
    df = pd.DataFrame(trades_data)
    
    fig = go.Figure()
    
    # Group by date and sum volume
    df["date"] = safe_to_datetime(df["timestamp"]).dt.date
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

def add_trades_to_chart(fig, trades_data: List[Dict[str, Any]]):
    """Add trade lines to chart inspired by backtesting result"""
    if not trades_data:
        return fig
    
    trades_df = pd.DataFrame(trades_data)
    trades_df["timestamp"] = safe_to_datetime(trades_df["timestamp"])
    
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
            is_buy = trade["trade_type"].upper() == "BUY"
        elif "side" in trade:
            is_buy = trade["side"].upper() == "BUY"
        elif "order_type" in trade:
            is_buy = trade["order_type"].upper() == "BUY"
        
        # Use trade type for color - Buy=green, Sell=red
        color = "green" if is_buy else "red"
        
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
                        "<extra></extra>"
        ))
    
    return fig

def get_pnl_trace(trades_data: List[Dict[str, Any]]):
    """Get PnL trace for trades"""
    if not trades_data:
        return None
    
    trades_df = pd.DataFrame(trades_data)
    trades_df["timestamp"] = safe_to_datetime(trades_df["timestamp"])
    
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

def create_comprehensive_dashboard(candles_data: List[Dict[str, Any]], trades_data: List[Dict[str, Any]], performance_data: Dict[str, Any], trading_pair: str = ""):
    """Create comprehensive trading dashboard with multiple panels"""
    if not candles_data or not performance_data:
        return None
    
    # Create subplots with shared x-axis
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(
            f'{trading_pair} Price & Trades',
            'PnL & Fees vs Position'
        ),
        row_heights=[0.75, 0.25],
        specs=[[{"secondary_y": False}],
               [{"secondary_y": True}]]
    )
    
    # Prepare data
    candles_df = pd.DataFrame(candles_data)
    candles_df["timestamp"] = safe_to_datetime(candles_df["timestamp"])
    
    perf_data = performance_data.get("performance_data", [])
    perf_df = None
    if perf_data:
        perf_df = pd.DataFrame(perf_data)
        perf_df["timestamp"] = safe_to_datetime(perf_df["timestamp"])
    
    # Row 1: Candlestick chart with trades
    fig.add_trace(go.Candlestick(
        x=candles_df["timestamp"],
        open=candles_df["open"],
        high=candles_df["high"],
        low=candles_df["low"],
        close=candles_df["close"],
        name="Price",
        showlegend=False
    ), row=1, col=1)
    
    # Add trades to price chart and average price lines from performance data
    if trades_data:
        trades_df = pd.DataFrame(trades_data)
        trades_df["timestamp"] = safe_to_datetime(trades_df["timestamp"])
        
        # Add individual trade markers
        for idx, trade in trades_df.iterrows():
            is_buy = False
            if "trade_type" in trade:
                is_buy = trade["trade_type"].upper() == "BUY"
            elif "side" in trade:
                is_buy = trade["side"].upper() == "BUY"
            
            color = "green" if is_buy else "red"
            fig.add_trace(go.Scatter(
                x=[trade["timestamp"]],
                y=[trade["price"]],
                mode="markers",
                marker=dict(
                    symbol="triangle-up" if is_buy else "triangle-down",
                    size=8,
                    color=color,
                    line=dict(width=1, color=color)
                ),
                name=f"{'Buy' if is_buy else 'Sell'} Trade",
                showlegend=False,
                hovertemplate=f"<b>{'Buy' if is_buy else 'Sell'}</b><br>Price: ${trade['price']:.4f}<br>Amount: {trade.get('amount', 0):.4f}<extra></extra>"
            ), row=1, col=1)
    
    # Add dynamic average price lines from performance data
    if perf_data and perf_df is not None:
        # Filter performance data to only include rows with valid average prices
        buy_avg_data = perf_df[perf_df["buy_avg_price"] > 0].copy()
        sell_avg_data = perf_df[perf_df["sell_avg_price"] > 0].copy()
        
        # Add buy average price line (evolving over time)
        if not buy_avg_data.empty:
            fig.add_trace(go.Scatter(
                x=buy_avg_data["timestamp"],
                y=buy_avg_data["buy_avg_price"],
                mode="lines",
                name="Buy Avg Price",
                line=dict(color="green", width=2, dash="dash"),
                showlegend=True,
                hovertemplate="<b>Buy Avg Price</b><br>Time: %{x}<br>Price: $%{y:.4f}<extra></extra>"
            ), row=1, col=1)
            
            # Add final buy average price as horizontal line
            final_buy_avg = buy_avg_data["buy_avg_price"].iloc[-1]
            fig.add_hline(
                y=final_buy_avg,
                line=dict(color="green", width=1, dash="dot"),
                annotation_text=f"Final Buy Avg: ${final_buy_avg:.4f}",
                annotation_position="bottom right",
                annotation_font_color="green",
                annotation_font_size=10,
                row=1, col=1
            )
        
        # Add sell average price line (evolving over time)
        if not sell_avg_data.empty:
            fig.add_trace(go.Scatter(
                x=sell_avg_data["timestamp"],
                y=sell_avg_data["sell_avg_price"],
                mode="lines",
                name="Sell Avg Price",
                line=dict(color="red", width=2, dash="dash"),
                showlegend=True,
                hovertemplate="<b>Sell Avg Price</b><br>Time: %{x}<br>Price: $%{y:.4f}<extra></extra>"
            ), row=1, col=1)
            
            # Add final sell average price as horizontal line
            final_sell_avg = sell_avg_data["sell_avg_price"].iloc[-1]
            fig.add_hline(
                y=final_sell_avg,
                line=dict(color="red", width=1, dash="dot"),
                annotation_text=f"Final Sell Avg: ${final_sell_avg:.4f}",
                annotation_position="top right",
                annotation_font_color="red",
                annotation_font_size=10,
                row=1, col=1
            )
    
    if perf_data and perf_df is not None:
        # Row 2: Net PnL, Unrealized PnL, and Fees (left y-axis) + Position (right y-axis)
        fig.add_trace(go.Scatter(
            x=perf_df["timestamp"],
            y=perf_df["net_pnl_quote"],
            mode="lines",
            name="Net PnL",
            line=dict(color='#4CAF50', width=2),
            showlegend=True
        ), row=2, col=1, secondary_y=False)
        
        fig.add_trace(go.Scatter(
            x=perf_df["timestamp"],
            y=perf_df["unrealized_trade_pnl_quote"],
            mode="lines", 
            name="Unrealized PnL",
            line=dict(color='#FF9800', width=2),
            showlegend=True
        ), row=2, col=1, secondary_y=False)
        
        fig.add_trace(go.Scatter(
            x=perf_df["timestamp"],
            y=perf_df["fees_quote"].cumsum(),
            mode="lines",
            name="Cumulative Fees",
            line=dict(color='#F44336', width=2),
            showlegend=True
        ), row=2, col=1, secondary_y=False)
        
        fig.add_trace(go.Scatter(
            x=perf_df["timestamp"],
            y=perf_df["net_position"],
            mode="lines",
            name="Net Position",
            line=dict(color='#2196F3', width=2),
            showlegend=True
        ), row=2, col=1, secondary_y=True)
    
    # Update layout
    fig.update_layout(
        height=700,
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0.1)',
        font=dict(color='white', size=12),
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update axis properties
    fig.update_xaxes(rangeslider_visible=False)
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="PnL & Fees ($)", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Position", row=2, col=1, secondary_y=True)
    
    return fig

# Page header
st.title("🗃️ Archived Bots")

# Load databases and bot runs on first run
if not st.session_state.databases_list:
    with st.spinner("Loading databases..."):
        load_databases()
        load_all_databases_status()
        load_bot_runs()

# Bot Runs Overview Section
st.subheader("📊 Bot Runs Overview")

# Get healthy databases for scatterplot
if st.session_state.databases_list:
    # Load status if not already loaded (needed for filtering)
    if not st.session_state.databases_status:
        with st.spinner("Loading database status..."):
            load_all_databases_status()
    
    healthy_databases = get_healthy_databases()
else:
    healthy_databases = []

# Create and display scatterplot
if st.session_state.bot_runs:
    scatterplot_result = create_bot_runs_scatterplot(st.session_state.bot_runs, healthy_databases)
    if scatterplot_result:
        fig, runs_df = scatterplot_result
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_runs = len(runs_df)
            st.metric("Total Runs", total_runs)
        
        with col2:
            profitable_runs = len(runs_df[runs_df["global_pnl"] > 0])
            profit_rate = (profitable_runs / total_runs * 100) if total_runs > 0 else 0
            st.metric("Profitable Runs", f"{profitable_runs} ({profit_rate:.1f}%)")
        
        with col3:
            total_pnl = runs_df["global_pnl"].sum()
            st.metric("Total PnL", f"${total_pnl:,.2f}")
        
        with col4:
            total_volume = runs_df["volume_traded"].sum()
            st.metric("Total Volume", f"${total_volume:,.0f}")
    else:
        st.warning("No bot runs data available for visualization.")
else:
    st.info("Loading bot runs data...")

st.divider()

# Database Analysis Section
st.subheader("🔍 Database Analysis")

# Database selection and controls in one row
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if healthy_databases:
        selected_db = st.selectbox(
            "Select Database",
            options=healthy_databases,
            key="db_selector",
            help="Choose a database to analyze in detail"
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
        st.warning("No healthy databases found.")

with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        with st.spinner("Refreshing..."):
            load_databases()
            load_all_databases_status()
            load_bot_runs()
            st.rerun()

with col3:
    load_dashboard_btn = st.button("📊 Load Dashboard", use_container_width=True, type="primary", disabled=not st.session_state.selected_database)

# Main content - only show if database is selected
if st.session_state.selected_database:
    db_path = st.session_state.selected_database
    
    # Load database summary if not already loaded
    if not st.session_state.db_summary:
        with st.spinner("Loading database summary..."):
            load_database_summary(db_path)
    
    # Find matching bot run
    matching_bot_run = find_matching_bot_run(db_path, st.session_state.bot_runs)
    
    # Compact summary in one row
    if st.session_state.db_summary and matching_bot_run:
        summary = st.session_state.db_summary
        bot_name = matching_bot_run.get('bot_name', 'N/A')
        strategy = matching_bot_run.get('strategy_name', 'N/A')
        deployed_date = pd.to_datetime(matching_bot_run.get('deployed_at', '')).strftime('%m/%d %H:%M') if matching_bot_run.get('deployed_at') else 'N/A'
        
        st.info(f"🤖 **{bot_name}** | {strategy} | Deployed: {deployed_date} | {summary.get('total_trades', 0)} trades on {summary.get('exchanges', ['N/A'])[0]} {summary.get('trading_pairs', ['N/A'])[0]}")
    
    # Handle Load Dashboard button click
    if load_dashboard_btn:
        with st.spinner("Loading comprehensive dashboard..."):
            try:
                # Load all necessary data
                load_database_performance(db_path)
                load_trades_data(db_path, 10000, 0)  # Load more trades for analysis
                st.session_state.trade_analysis = get_trade_analysis(db_path)
                
                st.success("✅ Dashboard loaded!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Failed to load dashboard: {str(e)}")
    
    st.divider()
    
    # Main Dashboard
    if st.session_state.db_performance and st.session_state.trades_data and st.session_state.trade_analysis:
        performance = st.session_state.db_performance
        summary = performance.get("summary", {})
        analysis = st.session_state.trade_analysis
        
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            net_pnl = summary.get('final_net_pnl_quote', 0)
            st.metric(
                "Net PnL (Quote)",
                value=f"${net_pnl:,.6f}",
                delta=f"{net_pnl:+.6f}" if net_pnl != 0 else None
            )
        
        with col2:
            fees = summary.get('total_fees_quote', 0)
            st.metric(
                "Total Fees (Quote)",
                value=f"${fees:,.4f}"
            )
        
        with col3:
            realized_pnl = summary.get('final_realized_pnl_quote', 0)
            st.metric(
                "Realized PnL",
                value=f"${realized_pnl:,.6f}",
                delta=f"{realized_pnl:+.6f}" if realized_pnl != 0 else None
            )
        
        with col4:
            volume = summary.get('total_volume_quote', 0)
            st.metric(
                "Total Volume",
                value=f"${volume:,.2f}"
            )
        
        st.divider()
        
        if analysis.get("exchanges") and analysis.get("trading_pairs"):
            # Simple controls
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_exchange = analysis["exchanges"][0] if len(analysis["exchanges"]) == 1 else st.selectbox(
                    "Exchange", options=analysis["exchanges"]
                )
                
                selected_pair = analysis["trading_pairs"][0] if len(analysis["trading_pairs"]) == 1 else st.selectbox(
                    "Trading Pair", options=analysis["trading_pairs"]
                )
            
            with col2:
                candle_interval = st.selectbox(
                    "Candle Interval",
                    options=["1m", "5m", "15m", "1h"],
                    index=1,  # Default to 5m
                )
            
            # Auto-load candles when interval changes
            candle_key = f"{selected_exchange}_{selected_pair}_{candle_interval}"
            if st.session_state.get("candle_key") != candle_key and analysis.get("start_time") and analysis.get("end_time"):
                with st.spinner("Loading historical candles..."):
                    candles = get_historical_candles(
                        selected_exchange,
                        selected_pair,
                        analysis["start_time"],
                        analysis["end_time"],
                        candle_interval
                    )
                    st.session_state.historical_candles = candles
                    st.session_state.candle_key = candle_key
            
            # Display comprehensive dashboard
            if st.session_state.historical_candles:
                trades_data = analysis.get("trades_df", pd.DataFrame())
                trades_list = trades_data.to_dict("records") if not trades_data.empty else []
                
                dashboard = create_comprehensive_dashboard(
                    st.session_state.historical_candles,
                    trades_list,
                    performance,
                    selected_pair
                )
                
                if dashboard:
                    st.plotly_chart(dashboard, use_container_width=True)
                else:
                    st.warning("Unable to create dashboard. Check data format.")
            else:
                st.info("Loading candles data...")
        else:
            st.warning("⚠️ No trading data found for analysis.")
    else:
        st.info("Click 'Load Dashboard' to view comprehensive trading analysis.")

else:
    st.info("Please select a database to begin analysis.")

# Auto-refresh fragment for database list  
@st.fragment(run_every=30)
def auto_refresh_databases():
    """Auto-refresh database list every 30 seconds"""
    try:
        if st.session_state.get("auto_refresh_enabled", False):
            load_databases()
    except Exception:
        # Gracefully handle fragment lifecycle issues
        pass

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