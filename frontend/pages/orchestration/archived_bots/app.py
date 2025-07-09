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
        if status.get("status") == "healthy" or status.get("status") == "ok":
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
                status_data.append({
                    "Database": db_path,
                    "Status": status.get("status", "unknown"),
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
            
            # Performance chart
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