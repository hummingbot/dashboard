import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from CONFIG import AUTH_SYSTEM_ENABLED
from frontend.st_utils import get_backend_api_client, initialize_st_page


def _portfolio_value(state: dict) -> float:
    """Sum portfolio value, excluding paper-trading accounts, testnet exchanges,
    and duplicate wallets (same exchange + identical token holdings)."""
    seen = set()
    total = 0.0
    for account, exchanges in state.items():
        for exchange, tokens_info in exchanges.items():
            if "testnet" in exchange:
                continue
            # Deduplicate: same exchange + same token set = same wallet under different credentials
            fingerprint = (exchange, frozenset((t.get("token"), round(t.get("value", 0), 4)) for t in tokens_info))
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            total += sum(t.get("value", 0) for t in tokens_info)
    return total

initialize_st_page(
    layout="wide",
    show_readme=False
)

# Custom CSS for enhanced styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }

    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #4CAF50;
    }

    .status-active {
        color: #4CAF50;
        font-weight: bold;
    }

    .status-inactive {
        color: #ff6b6b;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">🤖 Hummingbot Dashboard</h1>
    <p style="font-size: 1.2rem; color: #888; margin-bottom: 2rem;">
        Your Command Center for Algorithmic Trading Excellence
    </p>
</div>
""", unsafe_allow_html=True)

# Require authentication when auth system is enabled
if AUTH_SYSTEM_ENABLED and not st.session_state.get("authentication_status"):
    st.info("Please log in to view the dashboard.")
    st.stop()

# Initialize backend client
backend_api_client = get_backend_api_client()

# Fetch data from API
active_bots_count = 0
total_portfolio = 0.0
total_net_pnl = 0.0
total_volume = 0.0
total_tp = 0
total_sl = 0
total_ts = 0
total_tl = 0
total_es = 0
controllers_data = []
api_error = None

try:
    response = backend_api_client.bot_orchestration.get_active_bots_status()
    if response.get("status") == "success":
        active_bots = response.get("data", {})
        for bot_name in active_bots.keys():
            try:
                bot_status = backend_api_client.bot_orchestration.get_bot_status(bot_name)
                if bot_status.get("status") == "success":
                    bot_data = bot_status.get("data", {})
                    if bot_data.get("status") == "running":
                        active_bots_count += 1
                        performance = bot_data.get("performance", {})
                        controller_configs = []
                        try:
                            controller_configs = backend_api_client.controllers.get_bot_controller_configs(bot_name) or []
                        except Exception:
                            pass
                        for controller_id, inner_dict in performance.items():
                            if inner_dict.get("status") == "error":
                                continue
                            controller_config = next(
                                (c for c in controller_configs if c.get("id") == controller_id), {}
                            )
                            if "testnet" in controller_config.get("connector_name", ""):
                                continue
                            cp = inner_dict.get("performance", {})
                            total_net_pnl += cp.get("global_pnl_quote", 0)
                            total_volume += cp.get("volume_traded", 0)
                            close_types = cp.get("close_type_counts", {})
                            total_tp += close_types.get("CloseType.TAKE_PROFIT", 0)
                            total_sl += close_types.get("CloseType.STOP_LOSS", 0)
                            total_ts += close_types.get("CloseType.TRAILING_STOP", 0)
                            total_tl += close_types.get("CloseType.TIME_LIMIT", 0)
                            total_es += close_types.get("CloseType.EARLY_STOP", 0)
                            controllers_data.append({
                                "bot": bot_name,
                                "name": controller_config.get("controller_name", controller_id),
                                "connector": controller_config.get("connector_name", "N/A"),
                                "pair": controller_config.get("trading_pair", "N/A"),
                                "pnl": cp.get("global_pnl_quote", 0),
                                "active": not controller_config.get("manual_kill_switch", False),
                            })
            except Exception:
                continue
except Exception as e:
    api_error = str(e)

try:
    portfolio_state = backend_api_client.portfolio.get_state()
    total_portfolio = _portfolio_value(portfolio_state)
except Exception:
    pass

total_closed = total_tp + total_sl + total_ts + total_tl + total_es
win_count = total_tp + total_ts
win_rate = win_count / total_closed if total_closed > 0 else None

# Compute 7-day portfolio PNL%
# Per-(account, exchange): use value at 7-day cutoff if available, else first appearance.
# This avoids the distortion of accounts that joined the tracker mid-window.
seven_day_pnl_pct = None
try:
    history = backend_api_client.portfolio.get_history()
    history_records = history.get("data", []) if isinstance(history, dict) else history
    if history_records:
        _sorted = sorted(history_records, key=lambda r: pd.to_datetime(r.get("timestamp")))
        _cutoff = pd.to_datetime(_sorted[-1].get("timestamp")) - pd.Timedelta(days=7)

        # For each (account, exchange) key: track the most-recent value at/before cutoff,
        # falling back to the first appearance after cutoff.
        _baseline = {}  # key -> value
        for _rec in _sorted:
            _ts = pd.to_datetime(_rec.get("timestamp"))
            for _acct, _exs in _rec.get("state", {}).items():
                for _ex, _toks in _exs.items():
                    if "testnet" in _ex:
                        continue
                    _key = (_acct, _ex)
                    _val = sum(t.get("value", 0) for t in _toks)
                    if _ts <= _cutoff:
                        _baseline[_key] = _val          # keep updating → most-recent pre-cutoff
                    elif _key not in _baseline:
                        _baseline[_key] = _val          # first appearance after cutoff

        # Current values from latest record (with dedup)
        _current_total = 0.0
        _keys_seen = set()
        for _acct, _exs in _sorted[-1].get("state", {}).items():
            for _ex, _toks in _exs.items():
                if "testnet" in _ex:
                    continue
                _key = (_acct, _ex)
                if _key in _keys_seen:
                    continue
                _keys_seen.add(_key)
                _current_total += sum(t.get("value", 0) for t in _toks)

        _baseline_total = sum(_baseline.get(k, 0) for k in _keys_seen)
        if _baseline_total > 0:
            seven_day_pnl_pct = (_current_total - _baseline_total) / _baseline_total
except Exception:
    pass

# Live Dashboard Overview
st.markdown("## 📊 Live Dashboard Overview")

if api_error:
    st.error(f"Failed to connect to backend API: {api_error}")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>🔄 Active Bots</h3>
        <div class="stat-number">{active_bots_count}</div>
        <p>Currently Running</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    portfolio_display = f"${total_portfolio:,.2f}" if total_portfolio > 0 else "N/A"
    st.markdown(f"""
    <div class="metric-card">
        <h3>💰 Total Portfolio</h3>
        <div class="stat-number">{portfolio_display}</div>
        <p>Across All Accounts</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    win_rate_display = f"{win_rate:.1%}" if win_rate is not None else "N/A"
    win_rate_label = f"{total_closed} closed positions" if total_closed > 0 else "No closed positions"
    st.markdown(f"""
    <div class="metric-card">
        <h3>📈 Win Rate</h3>
        <div class="stat-number">{win_rate_display}</div>
        <p>{win_rate_label}</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    pnl_color = "#4CAF50" if total_net_pnl >= 0 else "#ff6b6b"
    pnl_sign = "+" if total_net_pnl >= 0 else ""
    st.markdown(f"""
    <div class="metric-card">
        <h3>💹 NET PNL</h3>
        <div class="stat-number" style="color: {pnl_color};">{pnl_sign}${total_net_pnl:,.2f}</div>
        <p>${total_volume:,.2f} volume traded</p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    if seven_day_pnl_pct is not None:
        _7d_color = "#4CAF50" if seven_day_pnl_pct >= 0 else "#ff6b6b"
        _7d_sign = "+" if seven_day_pnl_pct >= 0 else ""
        _7d_display = f"{_7d_sign}{seven_day_pnl_pct:.2%}"
    else:
        _7d_color = "#888"
        _7d_display = "N/A"
    st.markdown(f"""
    <div class="metric-card">
        <h3>📅 7D PNL (%)</h3>
        <div class="stat-number" style="color: {_7d_color};">{_7d_display}</div>
        <p>Portfolio 7-day change</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Portfolio performance chart
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📈 Portfolio Value (History)")
    try:
        history = backend_api_client.portfolio.get_history()
        history_records = history.get("data", []) if isinstance(history, dict) else history
        if history_records:
            data = []
            for record in history_records:
                timestamp = record.get("timestamp")
                state = record.get("state", {})
                data.append({"timestamp": timestamp, "value": _portfolio_value(state)})
            if data:
                df = pd.DataFrame(data)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df["timestamp"],
                    y=df["value"],
                    mode="lines",
                    line=dict(color="#4CAF50", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(76, 175, 80, 0.1)",
                    name="Portfolio Value"
                ))
                fig.update_layout(
                    template="plotly_dark",
                    height=350,
                    showlegend=False,
                    margin=dict(l=0, r=0, t=0, b=0),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No portfolio history available.")
        else:
            st.info("No portfolio history available.")
    except Exception as e:
        st.info(f"Portfolio history unavailable: {e}")

with col2:
    st.markdown("### 🎯 Controller Status")
    if controllers_data:
        for ctrl in controllers_data:
            status_icon = "🟢" if ctrl["active"] else "🔴"
            status_label = "Active" if ctrl["active"] else "Stopped"
            pnl_color = "#4CAF50" if ctrl["pnl"] >= 0 else "#ff6b6b"
            pnl_sign = "+" if ctrl["pnl"] >= 0 else ""
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 0.8rem; border-radius: 8px; margin: 0.4rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{ctrl['name']}</strong><br>
                        <small>{ctrl['connector']} · {ctrl['pair']}</small><br>
                        <span class="{'status-active' if ctrl['active'] else 'status-inactive'}">{status_icon} {status_label}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="color: {pnl_color}; font-weight: bold;">{pnl_sign}${ctrl['pnl']:,.2f}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No active bots found.")
