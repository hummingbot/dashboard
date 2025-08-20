import random
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from frontend.st_utils import initialize_st_page

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
    
    .feature-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        margin: 1rem 0;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #4CAF50;
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
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

# Generate sample data for demonstration
def generate_sample_data():
    """Generate sample trading data for visualization"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    
    # Sample portfolio performance
    portfolio_values = []
    base_value = 10000
    for i in range(len(dates)):
        change = random.uniform(-0.02, 0.03)  # -2% to +3% daily change
        base_value *= (1 + change)
        portfolio_values.append(base_value)
    
    return pd.DataFrame({
        'date': dates,
        'portfolio_value': portfolio_values,
        'daily_return': [random.uniform(-0.05, 0.08) for _ in range(len(dates))]
    })

# Quick Stats Dashboard
st.markdown("## 📊 Live Dashboard Overview")

# Mock data warning
st.warning("""
⚠️ **Demo Data Notice**: The metrics, charts, and statistics shown below are simulated/mocked data for demonstration purposes. 
This showcases how real trading data would be presented in the dashboard once connected to live trading bots.
""")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <h3>🔄 Active Bots</h3>
        <div class="stat-number pulse">3</div>
        <p>Currently Trading</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <h3>💰 Total Portfolio</h3>
        <div class="stat-number">$12,847</div>
        <p style="color: #4CAF50;">+2.3% Today</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h3>📈 Win Rate</h3>
        <div class="stat-number">74.2%</div>
        <p>Last 30 Days</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card">
        <h3>⚡ Total Trades</h3>
        <div class="stat-number">1,247</div>
        <p>This Month</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Performance Chart
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📈 Portfolio Performance (30 Days)")
    
    # Generate and display sample performance chart
    df = generate_sample_data()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['portfolio_value'],
        mode='lines+markers',
        line=dict(color='#4CAF50', width=3),
        fill='tonexty',
        fillcolor='rgba(76, 175, 80, 0.1)',
        name='Portfolio Value'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        height=400,
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🎯 Strategy Status")
    
    strategies = [
        {"name": "Market Making", "status": "active", "pnl": "+$342"},
        {"name": "Arbitrage", "status": "active", "pnl": "+$156"},
        {"name": "Grid Trading", "status": "active", "pnl": "+$89"},
        {"name": "DCA Bot", "status": "inactive", "pnl": "+$234"},
    ]
    
    for strategy in strategies:
        status_class = "status-active" if strategy["status"] == "active" else "status-inactive"
        status_icon = "🟢" if strategy["status"] == "active" else "🔴"
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{strategy['name']}</strong><br>
                    <span class="{status_class}">{status_icon} {strategy['status'].title()}</span>
                </div>
                <div style="text-align: right;">
                    <span style="color: #4CAF50; font-weight: bold;">{strategy['pnl']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Feature Showcase
st.markdown("## 🚀 Platform Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 3rem;">🎯</div>
            <h3>Strategy Development</h3>
        </div>
        <ul style="list-style: none; padding: 0;">
            <li>✨ Visual Strategy Builder</li>
            <li>🔧 Advanced Configuration</li>
            <li>📝 Custom Parameters</li>
            <li>🧪 Testing Environment</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 3rem;">📊</div>
            <h3>Analytics & Insights</h3>
        </div>
        <ul style="list-style: none; padding: 0;">
            <li>📈 Real-time Performance</li>
            <li>🔍 Advanced Backtesting</li>
            <li>📋 Detailed Reports</li>
            <li>🎨 Interactive Charts</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 3rem;">⚡</div>
            <h3>Live Trading</h3>
        </div>
        <ul style="list-style: none; padding: 0;">
            <li>🤖 Automated Execution</li>
            <li>📡 Real-time Monitoring</li>
            <li>🛡️ Risk Management</li>
            <li>🔔 Smart Alerts</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Quick Actions
st.markdown("## ⚡ Quick Actions")

# Alert for mocked navigation
st.info("ℹ️ **Note**: This is a mocked landing page. The Quick Actions buttons below are for demonstration purposes and the page navigation is not functional.")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🚀 Deploy Strategy", use_container_width=True, type="primary"):
        st.error("🚫 Navigation unavailable - This is a mocked landing page for demonstration purposes.")

with col2:
    if st.button("📊 View Performance", use_container_width=True):
        st.error("🚫 Navigation unavailable - This is a mocked landing page for demonstration purposes.")

with col3:
    if st.button("🔍 Backtesting", use_container_width=True):
        st.error("🚫 Navigation unavailable - This is a mocked landing page for demonstration purposes.")

with col4:
    if st.button("🗃️ Archived Bots", use_container_width=True):
        st.error("🚫 Navigation unavailable - This is a mocked landing page for demonstration purposes.")

st.divider()

# Community & Resources
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🎬 Learn & Explore")
    
    st.video("https://youtu.be/7eHiMPRBQLQ?si=PAvCq0D5QDZz1h1D")

with col2:
    st.markdown("### 💬 Join Our Community")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 15px; color: white;">
        <h4>🌟 Connect with Traders</h4>
        <p>Join thousands of algorithmic traders sharing strategies and insights!</p>
        <br>
        <a href="https://discord.gg/hummingbot" target="_blank" 
           style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; 
                  border-radius: 8px; text-decoration: none; color: white; font-weight: bold;">
           💬 Join Discord
        </a>
        <br><br>
        <a href="https://github.com/hummingbot/dashboard" target="_blank"
           style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; 
                  border-radius: 8px; text-decoration: none; color: white; font-weight: bold;">
           🐛 Report Issues
        </a>
    </div>
    """, unsafe_allow_html=True)

# Footer stats
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🌍 Global Users", "10,000+")

with col2:
    st.metric("💱 Exchanges", "20+")

with col3:
    st.metric("🔄 Daily Volume", "$2.5M+")

with col4:
    st.metric("⭐ GitHub Stars", "7,800+")
