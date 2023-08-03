import streamlit as st
from st_pages import Page, show_pages

from utils.st_utils import initialize_st_page


initialize_st_page(title="Hummingbot Dashboard", icon="📊")

show_pages(
    [
        Page("main.py", "Hummingbot Dashboard", "📊"),
        Page("pages/strategy_performance/app.py", "Strategy Performance", "🚀"),
        Page("pages/bot_orchestration/app.py", "Bot Orchestration", "🐙"),
        Page("pages/backtest_manager/app.py", "Backtest Manager", "⚙️"),
        Page("pages/candles_downloader/app.py", "Candles Downloader", "🗂"),
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
