import asyncio
import time

import nest_asyncio
import pandas as pd
import streamlit as st

from frontend.st_utils import get_backend_api_client, initialize_st_page

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

initialize_st_page(title="Instances", icon="🦅")

# Initialize backend client
backend_api_client = get_backend_api_client()

# Initialize session state for auto-refresh
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = 0

# Set refresh interval
REFRESH_INTERVAL = 10  # seconds


def stop_bot(bot_name):
    """Stop a running bot."""
    try:
        backend_api_client.bot_orchestration.stop_and_archive_bot(bot_name)
        st.success(f"Bot {bot_name} stopped and archived successfully")
        # Clear any cached data that might keep showing the bot
        if 'last_refresh' in st.session_state:
            st.session_state.last_refresh = 0  # Force refresh
        time.sleep(2)  # Give more time for the backend to process
        st.rerun()
    except Exception as e:
        st.error(f"Failed to stop bot {bot_name}: {e}")


def archive_bot(bot_name):
    """Archive a stopped bot."""
    try:
        backend_api_client.docker.stop_container(bot_name)
        backend_api_client.docker.remove_container(bot_name)
        st.success(f"Bot {bot_name} archived successfully")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Failed to archive bot {bot_name}: {e}")


def stop_controllers(bot_name, controllers):
    """Stop selected controllers."""
    success_count = 0
    for controller in controllers:
        try:
            # Try the most likely method first
            result = None
            if hasattr(backend_api_client.bot_orchestration, 'stop_controller_from_bot'):
                if asyncio.iscoroutinefunction(backend_api_client.bot_orchestration.stop_controller_from_bot):
                    result = asyncio.run(backend_api_client.bot_orchestration.stop_controller_from_bot(bot_name, controller))
                else:
                    result = backend_api_client.bot_orchestration.stop_controller_from_bot(bot_name, controller)
            elif hasattr(backend_api_client, 'stop_controller_from_bot'):
                if asyncio.iscoroutinefunction(backend_api_client.stop_controller_from_bot):
                    result = asyncio.run(backend_api_client.stop_controller_from_bot(bot_name, controller))
                else:
                    result = backend_api_client.stop_controller_from_bot(bot_name, controller)
            else:
                st.error(f"Method stop_controller_from_bot not found")
                continue
            
            success_count += 1
        except Exception as e:
            st.error(f"Failed to stop controller {controller}: {e}")
    
    if success_count > 0:
        st.success(f"Successfully stopped {success_count} controller(s)")
    
    return success_count > 0


def start_controllers(bot_name, controllers):
    """Start selected controllers."""
    success_count = 0
    for controller in controllers:
        try:
            # Try the most likely method first
            result = None
            if hasattr(backend_api_client.bot_orchestration, 'start_controller_from_bot'):
                if asyncio.iscoroutinefunction(backend_api_client.bot_orchestration.start_controller_from_bot):
                    result = asyncio.run(backend_api_client.bot_orchestration.start_controller_from_bot(bot_name, controller))
                else:
                    result = backend_api_client.bot_orchestration.start_controller_from_bot(bot_name, controller)
            elif hasattr(backend_api_client, 'start_controller_from_bot'):
                if asyncio.iscoroutinefunction(backend_api_client.start_controller_from_bot):
                    result = asyncio.run(backend_api_client.start_controller_from_bot(bot_name, controller))
                else:
                    result = backend_api_client.start_controller_from_bot(bot_name, controller)
            else:
                st.error(f"Method start_controller_from_bot not found")
                continue
            
            success_count += 1
        except Exception as e:
            st.error(f"Failed to start controller {controller}: {e}")
    
    if success_count > 0:
        st.success(f"Successfully started {success_count} controller(s)")
    
    return success_count > 0


@st.fragment
def render_bot_card(bot_name):
    """Render a bot performance card using native Streamlit components."""
    try:
        # Get bot status first
        if asyncio.iscoroutinefunction(backend_api_client.bot_orchestration.get_bot_status):
            bot_status = asyncio.run(backend_api_client.bot_orchestration.get_bot_status(bot_name))
        else:
            bot_status = backend_api_client.bot_orchestration.get_bot_status(bot_name)
        
        # Only try to get controller configs if bot exists and is running
        controller_configs = []
        if bot_status.get("status") == "success":
            bot_data = bot_status.get("data", {})
            is_running = bot_data.get("status") == "running"
            if is_running:
                try:
                    if asyncio.iscoroutinefunction(backend_api_client.controllers.get_bot_controller_configs):
                        controller_configs = asyncio.run(backend_api_client.controllers.get_bot_controller_configs(bot_name))
                    else:
                        controller_configs = backend_api_client.controllers.get_bot_controller_configs(bot_name)
                    controller_configs = controller_configs if controller_configs else []
                except Exception as e:
                    # If controller configs fail, continue without them
                    st.warning(f"Could not fetch controller configs for {bot_name}: {e}")
                    controller_configs = []
        
        if bot_status.get("status") == "error":
            # Error state
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.error(f"🤖 **{bot_name}** - Not Available")
                st.error(f"An error occurred while fetching bot status of {bot_name}. Please check the bot client.")
        else:
            bot_data = bot_status.get("data", {})
            is_running = bot_data.get("status") == "running"
            performance = bot_data.get("performance", {})
            error_logs = bot_data.get("error_logs", [])
            general_logs = bot_data.get("general_logs", [])
            
            # Bot header
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    if is_running:
                        st.success(f"🤖 **{bot_name}** - Running")
                    else:
                        st.warning(f"🤖 **{bot_name}** - Stopped")
                
                with col3:
                    if is_running:
                        if st.button("⏹️ Stop", key=f"stop_{bot_name}", use_container_width=True):
                            stop_bot(bot_name)
                    else:
                        if st.button("📦 Archive", key=f"archive_{bot_name}", use_container_width=True):
                            archive_bot(bot_name)
            
            if is_running:
                # Calculate totals
                active_controllers = []
                stopped_controllers = []
                error_controllers = []
                total_global_pnl_quote = 0
                total_volume_traded = 0
                total_unrealized_pnl_quote = 0
                
                for controller, inner_dict in performance.items():
                    controller_status = inner_dict.get("status")
                    if controller_status == "error":
                        error_controllers.append({
                            "Controller": controller,
                            "Error": inner_dict.get("error", "Unknown error")
                        })
                        continue
                    
                    controller_performance = inner_dict.get("performance", {})
                    controller_config = next(
                        (config for config in controller_configs if config.get("id") == controller), {}
                    )
                    
                    controller_name = controller_config.get("controller_name", controller)
                    connector_name = controller_config.get("connector_name", "N/A")
                    trading_pair = controller_config.get("trading_pair", "N/A")
                    kill_switch_status = controller_config.get("manual_kill_switch", False)
                    
                    realized_pnl_quote = controller_performance.get("realized_pnl_quote", 0)
                    unrealized_pnl_quote = controller_performance.get("unrealized_pnl_quote", 0)
                    global_pnl_quote = controller_performance.get("global_pnl_quote", 0)
                    volume_traded = controller_performance.get("volume_traded", 0)
                    
                    close_types = controller_performance.get("close_type_counts", {})
                    tp = close_types.get("CloseType.TAKE_PROFIT", 0)
                    sl = close_types.get("CloseType.STOP_LOSS", 0)
                    time_limit = close_types.get("CloseType.TIME_LIMIT", 0)
                    ts = close_types.get("CloseType.TRAILING_STOP", 0)
                    refreshed = close_types.get("CloseType.EARLY_STOP", 0)
                    failed = close_types.get("CloseType.FAILED", 0)
                    close_types_str = f"TP: {tp} | SL: {sl} | TS: {ts} | TL: {time_limit} | ES: {refreshed} | F: {failed}"
                    
                    controller_info = {
                        "Select": False,
                        "Controller": controller_name,
                        "Connector": connector_name,
                        "Trading Pair": trading_pair,
                        "Realized PNL ($)": round(realized_pnl_quote, 2),
                        "Unrealized PNL ($)": round(unrealized_pnl_quote, 2),
                        "NET PNL ($)": round(global_pnl_quote, 2),
                        "Volume ($)": round(volume_traded, 2),
                        "Close Types": close_types_str,
                        "_controller_id": controller
                    }
                    
                    if kill_switch_status:
                        stopped_controllers.append(controller_info)
                    else:
                        active_controllers.append(controller_info)
                    
                    total_global_pnl_quote += global_pnl_quote
                    total_volume_traded += volume_traded
                    total_unrealized_pnl_quote += unrealized_pnl_quote
                
                total_global_pnl_pct = total_global_pnl_quote / total_volume_traded if total_volume_traded > 0 else 0
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("🏦 NET PNL", f"${total_global_pnl_quote:.2f}")
                with col2:
                    st.metric("📊 NET PNL (%)", f"{total_global_pnl_pct:.2%}")
                with col3:
                    st.metric("💸 Volume Traded", f"${total_volume_traded:.2f}")
                with col4:
                    st.metric("💹 Unrealized PNL", f"${total_unrealized_pnl_quote:.2f}")
                
                # Active Controllers
                if active_controllers:
                    st.markdown("##### 🚀 Active Controllers")
                    active_df = pd.DataFrame(active_controllers)
                    
                    edited_active_df = st.data_editor(
                        active_df,
                        column_config={
                            "Select": st.column_config.CheckboxColumn(
                                "Select",
                                help="Select controllers to stop",
                                default=False,
                            ),
                            "_controller_id": None,  # Hide this column
                        },
                        disabled=[col for col in active_df.columns if col != "Select"],
                        hide_index=True,
                        use_container_width=True,
                        key=f"active_table_{bot_name}"
                    )
                    
                    selected_active = [
                        row["_controller_id"] 
                        for _, row in edited_active_df.iterrows() 
                        if row["Select"]
                    ]
                    
                    if selected_active:
                        if st.button(f"⏹️ Stop Selected ({len(selected_active)})", 
                                   key=f"stop_active_{bot_name}", 
                                   type="secondary"):
                            with st.spinner(f"Stopping {len(selected_active)} controller(s)..."):
                                if stop_controllers(bot_name, selected_active):
                                    time.sleep(1)
                                    st.rerun()
                
                # Stopped Controllers
                if stopped_controllers:
                    st.markdown("##### 💤 Stopped Controllers")
                    stopped_df = pd.DataFrame(stopped_controllers)
                    
                    edited_stopped_df = st.data_editor(
                        stopped_df,
                        column_config={
                            "Select": st.column_config.CheckboxColumn(
                                "Select",
                                help="Select controllers to start",
                                default=False,
                            ),
                            "_controller_id": None,  # Hide this column
                        },
                        disabled=[col for col in stopped_df.columns if col != "Select"],
                        hide_index=True,
                        use_container_width=True,
                        key=f"stopped_table_{bot_name}"
                    )
                    
                    selected_stopped = [
                        row["_controller_id"] 
                        for _, row in edited_stopped_df.iterrows() 
                        if row["Select"]
                    ]
                    
                    if selected_stopped:
                        if st.button(f"▶️ Start Selected ({len(selected_stopped)})", 
                                   key=f"start_stopped_{bot_name}", 
                                   type="primary"):
                            with st.spinner(f"Starting {len(selected_stopped)} controller(s)..."):
                                if start_controllers(bot_name, selected_stopped):
                                    time.sleep(1)
                                    st.rerun()
                
                # Error Controllers
                if error_controllers:
                    st.markdown("##### 💀 Controllers with Errors")
                    error_df = pd.DataFrame(error_controllers)
                    st.dataframe(error_df, use_container_width=True, hide_index=True)
                
                # Logs sections
                with st.expander("📋 Error Logs"):
                    if error_logs:
                        for log in error_logs[:50]:
                            timestamp = log.get("timestamp", "")
                            message = log.get("msg", "")
                            logger_name = log.get("logger_name", "")
                            st.text(f"{timestamp} - {logger_name}: {message}")
                    else:
                        st.info("No error logs available.")
                
                with st.expander("📝 General Logs"):
                    if general_logs:
                        for log in general_logs[:50]:
                            timestamp = pd.to_datetime(int(log.get("timestamp", 0)), unit="s")
                            message = log.get("msg", "")
                            logger_name = log.get("logger_name", "")
                            st.text(f"{timestamp} - {logger_name}: {message}")
                    else:
                        st.info("No general logs available.")
            
            st.divider()
            
    except Exception as e:
        st.error(f"🤖 **{bot_name}** - Error")
        st.error(f"An error occurred while fetching bot status: {str(e)}")
        st.divider()


# Main app
st.markdown("### 🏠 Local Instances")

# Auto-refresh controls
col1, col2, col3 = st.columns([3, 1, 1])
with col2:
    if st.button("▶️ Start Auto-refresh" if not st.session_state.auto_refresh else "⏸️ Stop Auto-refresh", 
                 use_container_width=True):
        st.session_state.auto_refresh = not st.session_state.auto_refresh
        st.rerun()

with col3:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()


@st.fragment(run_every=REFRESH_INTERVAL if st.session_state.auto_refresh else None)
def show_bot_instances():
    """Fragment to display bot instances with auto-refresh."""
    current_time = time.time()
    
    # Debounce rapid refreshes, but allow forced refresh when last_refresh is 0
    if (current_time - st.session_state.last_refresh < 2 and 
        st.session_state.last_refresh != 0):  # Allow forced refresh
        if st.session_state.auto_refresh:
            st.info(f"🔄 Auto-refreshing every {REFRESH_INTERVAL} seconds")
        return
    
    st.session_state.last_refresh = current_time
    
    try:
        # Always fetch fresh data - don't rely on any caching
        if asyncio.iscoroutinefunction(backend_api_client.bot_orchestration.get_active_bots_status):
            active_bots_response = asyncio.run(backend_api_client.bot_orchestration.get_active_bots_status())
        else:
            active_bots_response = backend_api_client.bot_orchestration.get_active_bots_status()
        
        if active_bots_response.get("status") == "success":
            active_bots = active_bots_response.get("data", {})
            
            # Filter out any bots that might be in transitional state
            truly_active_bots = {}
            for bot_name, bot_info in active_bots.items():
                try:
                    # Double-check each bot's status
                    if asyncio.iscoroutinefunction(backend_api_client.bot_orchestration.get_bot_status):
                        bot_status = asyncio.run(backend_api_client.bot_orchestration.get_bot_status(bot_name))
                    else:
                        bot_status = backend_api_client.bot_orchestration.get_bot_status(bot_name)
                    if bot_status.get("status") == "success":
                        bot_data = bot_status.get("data", {})
                        # Only include if the bot is actually running or stopped (not archived)
                        if bot_data.get("status") in ["running", "stopped"]:
                            truly_active_bots[bot_name] = bot_info
                except Exception:
                    # If we can't get status, skip this bot
                    continue
            
            if truly_active_bots:
                # Show refresh status
                if st.session_state.auto_refresh:
                    st.info(f"🔄 Auto-refreshing every {REFRESH_INTERVAL} seconds")
                
                # Render each bot
                for bot_name in truly_active_bots.keys():
                    render_bot_card(bot_name)
            else:
                st.info("No active bot instances found. Deploy a bot to see it here.")
        else:
            st.error("Failed to fetch active bots status.")
            
    except Exception as e:
        st.error(f"Failed to connect to backend: {e}")
        st.info("Please make sure the backend is running and accessible.")


# Call the fragment
show_bot_instances()