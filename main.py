import streamlit as st
from st_pages import Page, Section, show_pages

from utils.st_utils import initialize_st_page

initialize_st_page(title="Hummingbot Dashboard", icon="📊", initial_sidebar_state="expanded")

show_pages(
    [
        Page("main.py", "Hummingbot Dashboard", "📊"),
        Section("Bot Orchestration", "🐙"),
        Page("pages/master_conf/app.py", "Credentials", "🗝️"),
        Page("pages/launch_bot/app.py", "Launch Bot", "🙌"),
        Page("pages/bot_orchestration/app.py", "Instances", "🦅"),
        Page("pages/file_manager/app.py", "Strategy Configs", "🗂"),
        Section("Backtest Manager", "⚙️"),
        Page("pages/candles_downloader/app.py", "Get Data", "💾"),
        Page("pages/backtest_manager/create.py", "Create", "⚔️"),
        Page("pages/backtest_manager/optimize.py", "Optimize", "🧪"),
        Page("pages/backtest_manager/analyze.py", "Analyze", "🔬"),
        Page("pages/backtest_manager/analyze_v2.py", "Analyze v2", "🔬"),
        Page("pages/backtest_manager/simulate.py", "Simulate", "📈"),
        Section("Community Pages", "👨‍👩‍👧‍👦"),
        Page("pages/strategy_performance/app.py", "Strategy Performance", "🚀"),
        Page("pages/db_inspector/app.py", "DB Inspector", "🔍"),
        Page("pages/token_spreads/app.py", "Token Spreads", "🧙"),
        Page("pages/tvl_vs_mcap/app.py", "TVL vs Market Cap", "🦉"),
    ]
)

st.write("Watch this video to understand how the dashboard works! 🦅")
c1, c2, c3 = st.columns([1, 6, 1])
st.write("---")
with c2:
    st.video("https://youtu.be/2q9HSyIPuf4")
st.write("Please give us feedback in the **#dashboard** channel of the [Hummingbot Discord](https://discord.gg/hummingbot)! 🙏")
