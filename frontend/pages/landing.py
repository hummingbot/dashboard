import streamlit as st

from frontend.st_utils import initialize_st_page

initialize_st_page(
    layout="wide",
    show_readme=False
)

st.title("🤖 Hummingbot Dashboard")
st.subheader("An open-source platform for creating, backtesting, and optimizing algorithmic trading strategies. Deploy your strategies with Hummingbot.")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🎯 Strategy Development")
    st.write("Create and configure advanced trading strategies with intuitive interfaces and powerful customization options.")

with col2:
    st.markdown("### 📊 Backtesting & Analytics")
    st.write("Test your strategies against historical data and analyze performance with comprehensive metrics and visualizations.")

with col3:
    st.markdown("### ⚡ Live Trading")
    st.write("Deploy and monitor your strategies in real-time with advanced orchestration and performance tracking.")

st.header("🎬 Watch the Dashboard Tutorial")

st.video("https://youtu.be/7eHiMPRBQLQ?si=PAvCq0D5QDZz1h1D")

st.header("💬 Feedback & Community")

st.info("""
Join our community and share your feedback in the **#dashboard** channel of the [Hummingbot Discord](https://discord.gg/hummingbot)! 🙏

Found a bug or have suggestions? Create an issue in the [GitHub repository](https://github.com/hummingbot/dashboard).
""")
