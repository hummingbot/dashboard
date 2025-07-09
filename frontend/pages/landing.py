import streamlit as st

from frontend.components.styling import create_page_header
from frontend.st_utils import initialize_st_page

initialize_st_page(
    layout="wide",
    show_readme=False
)

create_page_header(
    title="Hummingbot Dashboard",
    subtitle="An open-source platform for creating, backtesting, and optimizing algorithmic trading strategies. "
             "Deploy your strategies with Hummingbot.",
    icon="🤖"
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="metric-card">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
            <h3 class="highlight-text">Strategy Development</h3>
            <p class="secondary-text">
                Create and configure advanced trading strategies with intuitive interfaces and powerful customization options.
            </p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="metric-card">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
            <h3 class="highlight-text">Backtesting & Analytics</h3>
            <p class="secondary-text">
                Test your strategies against historical data and analyze performance with comprehensive metrics and
                visualizations.
            </p>
        </div>
        """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="metric-card">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
            <h3 class="highlight-text">Live Trading</h3>
            <p class="secondary-text">
                Deploy and monitor your strategies in real-time with advanced orchestration and performance tracking.
            </p>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<h2 class="section-header">🎬 Watch the Dashboard Tutorial</h2>', unsafe_allow_html=True)

st.video("https://youtu.be/7eHiMPRBQLQ?si=PAvCq0D5QDZz1h1D")

st.markdown('<h2 class="section-header">💬 Feedback & Community</h2>', unsafe_allow_html=True)

st.markdown("""
    <div class="info-card">
        <p style="color: #a0aec0; font-size: 1.1rem; line-height: 1.6; margin-bottom: 1rem;">
            Join our community and share your feedback in the <strong>#dashboard</strong> channel of the
            <a href="https://discord.gg/hummingbot" class="highlight-text">Hummingbot Discord</a>! 🙏
        </p>
        <p style="color: #a0aec0; font-size: 1.1rem; line-height: 1.6; margin: 0;">
            Found a bug or have suggestions? Create an issue in the
            <a href="https://github.com/hummingbot/dashboard" class="highlight-text">GitHub repository</a>.
        </p>
    </div>
    """, unsafe_allow_html=True)
