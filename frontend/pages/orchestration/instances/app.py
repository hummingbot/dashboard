import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

from frontend.st_utils import get_backend_api_client, initialize_st_page

initialize_st_page(icon="🦅", show_readme=False)

# Initialize backend client
backend_api_client = get_backend_api_client()

# Initialize session state for auto-refresh
if "auto_refresh_enabled" not in st.session_state:
    st.session_state.auto_refresh_enabled = True

# Set refresh interval
REFRESH_INTERVAL = 10  # seconds


def stop_bot(bot_name):
    """Stop a running bot."""
    try:
        backend_api_client.bot_orchestration.stop_and_archive_bot(bot_name)
        st.success(f"Bot {bot_name} stopped and archived successfully")
        time.sleep(2)  # Give time for the backend to process
    except Exception as e:
        st.error(f"Failed to stop bot {bot_name}: {e}")


def archive_bot(bot_name):
    """Archive a stopped bot."""
    try:
        backend_api_client.docker.stop_container(bot_name)
        backend_api_client.docker.remove_container(bot_name)
        st.success(f"Bot {bot_name} archived successfully")
        time.sleep(1)
    except Exception as e:
        st.error(f"Failed to archive bot {bot_name}: {e}")


def stop_controllers(bot_name, controllers):
    """Stop selected controllers."""
    success_count = 0
    for controller in controllers:
        try:
            backend_api_client.controllers.update_bot_controller_config(
                bot_name,
                controller,
                {"manual_kill_switch": True}
            )
            success_count += 1
        except Exception as e:
            st.error(f"Failed to stop controller {controller}: {e}")

    if success_count > 0:
        st.success(f"Successfully stopped {success_count} controller(s)")
        # Temporarily disable auto-refresh to prevent immediate state reset
        st.session_state.auto_refresh_enabled = False

    return success_count > 0


def start_controllers(bot_name, controllers):
    """Start selected controllers."""
    success_count = 0
    for controller in controllers:
        try:
            backend_api_client.controllers.update_bot_controller_config(
                bot_name,
                controller,
                {"manual_kill_switch": False}
            )
            success_count += 1
        except Exception as e:
            st.error(f"Failed to start controller {controller}: {e}")

    if success_count > 0:
        st.success(f"Successfully started {success_count} controller(s)")
        # Temporarily disable auto-refresh to prevent immediate state reset
        st.session_state.auto_refresh_enabled = False

    return success_count > 0


def parse_bot_launch_time(bot_name):
    """Extract launch datetime from bot name pattern …-YYYYMMDD-HHMMSS."""
    match = re.search(r'(\d{8})-(\d{6})$', bot_name)
    if match:
        try:
            return datetime.strptime(
                f"{match.group(1)}-{match.group(2)}", "%Y%m%d-%H%M%S"
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def is_simulated_connector(connector_name: str) -> bool:
    return connector_name.endswith("_paper_trade") or "testnet" in connector_name


def get_price_connector(connector_name: str) -> str:
    """Normalize simulated connectors to their live market-data equivalent."""
    normalized = connector_name.replace("_paper_trade", "")
    normalized = re.sub(r"(^|[_-])testnet(?=$|[_-])", r"\1", normalized)
    normalized = re.sub(r"[_-]{2,}", "_", normalized).strip("_-")
    return normalized or connector_name


BNH_PRICES_FILE = Path(__file__).parents[4] / "data" / "bnh_entry_prices.json"


def _load_bnh_prices() -> dict:
    if BNH_PRICES_FILE.exists():
        try:
            return json.loads(BNH_PRICES_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_bnh_prices(data: dict):
    BNH_PRICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    BNH_PRICES_FILE.write_text(json.dumps(data, indent=2))


def get_bnh_entry_price(bot_name: str, controller_id: str, current_price: float):
    """Return the stored entry price, writing it the first time it is seen."""
    key = f"{bot_name}_{controller_id}"
    prices = _load_bnh_prices()
    if key not in prices and current_price is not None:
        prices[key] = current_price
        _save_bnh_prices(prices)
    return prices.get(key)


def fetch_current_price(connector_name: str, trading_pair: str):
    try:
        response = backend_api_client.market_data.get_prices(
            get_price_connector(connector_name), trading_pair
        )
        if isinstance(response, dict):
            if response.get("status") == "success":
                return response.get("data", {}).get(trading_pair)
            if "prices" in response:
                return response.get("prices", {}).get(trading_pair)
            return response.get(trading_pair)
    except Exception:
        pass
    return None


def render_bot_card(bot_name):
    """Render a bot performance card using native Streamlit components."""
    try:
        # Get bot status first
        bot_status = backend_api_client.bot_orchestration.get_bot_status(bot_name)

        # Only try to get controller configs if bot exists and is running
        controller_configs = []
        if bot_status.get("status") == "success":
            bot_data = bot_status.get("data", {})
            is_running = bot_data.get("status") == "running"
            if is_running:
                try:
                    controller_configs = backend_api_client.controllers.get_bot_controller_configs(bot_name)
                    controller_configs = controller_configs if controller_configs else []
                except Exception as e:
                    # If controller configs fail, continue without them
                    st.warning(f"Could not fetch controller configs for {bot_name}: {e}")
                    controller_configs = []

        with st.container(border=True):

            if bot_status.get("status") == "error":
                # Error state
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.error(f"🤖 **{bot_name}** - Not Available")
                st.error(f"An error occurred while fetching bot status of {bot_name}. Please check the bot client.")
            else:
                bot_data = bot_status.get("data", {})
                is_running = bot_data.get("status") == "running"
                performance = bot_data.get("performance", {})
                simulated = bool(controller_configs) and all(
                    is_simulated_connector(c.get("connector_name", ""))
                    for c in controller_configs
                )

                # Bot header
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    if is_running:
                        if simulated:
                            st.info(f"📄 **{bot_name}** - Running (Paper/Testnet)")
                        else:
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

                        # Buy-and-hold benchmark
                        current_price = None
                        entry_price = None
                        bnh_return = None
                        if connector_name != "N/A" and trading_pair != "N/A":
                            current_price = fetch_current_price(connector_name, trading_pair)
                            entry_price = get_bnh_entry_price(bot_name, controller, current_price)
                            if entry_price and current_price and entry_price != 0:
                                bnh_return = (current_price - entry_price) / entry_price

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
                            "ID": controller_config.get("id"),
                            "Controller": controller_name,
                            "Connector": connector_name,
                            "Trading Pair": trading_pair,
                            "Realized PNL ($)": round(realized_pnl_quote, 2),
                            "Unrealized PNL ($)": round(unrealized_pnl_quote, 2),
                            "NET PNL ($)": round(global_pnl_quote, 2),
                            "Volume ($)": round(volume_traded, 2),
                            "Close Types": close_types_str,
                            "B&H Entry ($)": round(entry_price, 4) if entry_price is not None else "—",
                            "B&H Current ($)": round(current_price, 4) if current_price is not None else "—",
                            "B&H Return (%)": f"{bnh_return:.2%}" if bnh_return is not None else "—",
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

                    # Per-bot 7D PNL%: if bot launched within last 7 days, current session = 7D window
                    launch_time = parse_bot_launch_time(bot_name)
                    if launch_time is not None:
                        bot_age_days = (datetime.now(timezone.utc) - launch_time).total_seconds() / 86400
                        seven_day_pnl_pct = total_global_pnl_pct if bot_age_days <= 7 else None
                    else:
                        seven_day_pnl_pct = None

                    # Display metrics
                    col1, col2, col3, col4, col5 = st.columns(5)

                    with col1:
                        st.metric("🏦 NET PNL", f"${total_global_pnl_quote:.2f}")
                    with col2:
                        st.metric("💹 Unrealized PNL", f"${total_unrealized_pnl_quote:.2f}")
                    with col3:
                        st.metric("📊 NET PNL (%)", f"{total_global_pnl_pct:.2%}")
                    with col4:
                        st.metric("💸 Volume Traded", f"${total_volume_traded:.2f}")
                    with col5:
                        if seven_day_pnl_pct is not None:
                            st.metric("📅 7D PNL (%)", f"{seven_day_pnl_pct:.2%}")
                        else:
                            st.metric("📅 7D PNL (%)", "N/A")

                    # Active Controllers
                    if active_controllers:
                        st.success("🚀 **Active Controllers:** Controllers currently running and trading")
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
                                    stop_controllers(bot_name, selected_active)
                                    time.sleep(1)

                        with st.expander("🔧 Active Controller Parameters"):
                            for ctrl_info in active_controllers:
                                ctrl_id = ctrl_info["_controller_id"]
                                config = next((c for c in controller_configs if c.get("id") == ctrl_id), {})
                                st.markdown(f"**{ctrl_info['Controller']}** — `{ctrl_id}`")
                                st.json(config, expanded=False)

                    # Stopped Controllers
                    if stopped_controllers:
                        st.warning("💤 **Stopped Controllers:** Controllers that are paused or stopped")
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
                                    start_controllers(bot_name, selected_stopped)
                                    time.sleep(1)

                        with st.expander("🔧 Stopped Controller Parameters"):
                            for ctrl_info in stopped_controllers:
                                ctrl_id = ctrl_info["_controller_id"]
                                config = next((c for c in controller_configs if c.get("id") == ctrl_id), {})
                                st.markdown(f"**{ctrl_info['Controller']}** — `{ctrl_id}`")
                                st.json(config, expanded=False)

                    # Error Controllers
                    if error_controllers:
                        st.error("💀 **Controllers with Errors:** Controllers that encountered errors")
                        error_df = pd.DataFrame(error_controllers)
                        st.dataframe(error_df, use_container_width=True, hide_index=True)

                # Datadog logs link
                datadog_query = quote(f"@bot_name:{bot_name}")
                datadog_url = f"https://app.us5.datadoghq.com/logs?query={datadog_query}"
                st.markdown(f"📋 [View Logs in Datadog ↗]({datadog_url})")

    except Exception as e:
        with st.container(border=True):
            st.error(f"🤖 **{bot_name}** - Error")
            st.error(f"An error occurred while fetching bot status: {str(e)}")


# Page Header
st.title("🦅 Hummingbot Instances")

# Auto-refresh controls
col1, col2, col3 = st.columns([3, 1, 1])

# Create placeholder for status message
status_placeholder = col1.empty()

with col2:
    if st.button("▶️ Start Auto-refresh" if not st.session_state.auto_refresh_enabled else "⏸️ Stop Auto-refresh",
                 use_container_width=True):
        st.session_state.auto_refresh_enabled = not st.session_state.auto_refresh_enabled

with col3:
    if st.button("🔄 Refresh Now", use_container_width=True):
        # Re-enable auto-refresh if it was temporarily disabled
        if not st.session_state.auto_refresh_enabled:
            st.session_state.auto_refresh_enabled = True
        pass


@st.fragment(run_every=REFRESH_INTERVAL if st.session_state.auto_refresh_enabled else None)
def show_bot_instances():
    """Fragment to display bot instances with auto-refresh."""
    try:
        active_bots_response = backend_api_client.bot_orchestration.get_active_bots_status()

        if active_bots_response.get("status") == "success":
            active_bots = active_bots_response.get("data", {})

            # Filter out any bots that might be in transitional state
            truly_active_bots = {}
            for bot_name, bot_info in active_bots.items():
                try:
                    bot_status = backend_api_client.bot_orchestration.get_bot_status(bot_name)
                    if bot_status.get("status") == "success":
                        bot_data = bot_status.get("data", {})
                        if bot_data.get("status") in ["running", "stopped"]:
                            truly_active_bots[bot_name] = bot_info
                except Exception:
                    continue

            if truly_active_bots:
                # Show refresh status
                if st.session_state.auto_refresh_enabled:
                    status_placeholder.info(f"🔄 Auto-refreshing every {REFRESH_INTERVAL} seconds")
                else:
                    status_placeholder.warning("⏸️ Auto-refresh paused. Click 'Refresh Now' to resume.")

                # Render each bot
                for bot_name in truly_active_bots.keys():
                    render_bot_card(bot_name)
            else:
                status_placeholder.info("No active bot instances found. Deploy a bot to see it here.")
        else:
            st.error("Failed to fetch active bots status.")

    except Exception as e:
        st.error(f"Failed to connect to backend: {e}")
        st.info("Please make sure the backend is running and accessible.")


# Call the fragment
show_bot_instances()
