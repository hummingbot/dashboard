import streamlit as st
from pathlib import Path
from st_pages import Page, show_pages

title = "Hummingbot Dashboard"
icon = "📊"

st.set_page_config(
    page_title=title,
    page_icon=icon,
    layout="wide",
)
st.title(f"{icon} {title}")

current_directory = Path(__file__).parent
readme_path = current_directory / "README.md"
with st.expander("About This Page"):
    st.write(readme_path.read_text())

show_pages(
    [
        Page("main.py", "Hummingbot Dashboard", "📊"),
        Page("pages/strategy_performance/app.py", "Strategy Performance", "🚀"),
        Page("pages/bot_orchestration/app.py", "Bot Orchestration", "🐙"),
        Page("pages/backtesting/app.py", "Backtesting", "⚙️"),
    ]
)

st.title("Welcome!")
st.write("---")
st.code("💡 The purpose of this dashboard is to provide useful information for high frequency trading traders")
st.write("")
st.write("Watch this video to understand how the dashboard works! 🦅")
c1, c2, c3 = st.columns([1, 6, 1])
with c2:
    st.video("https://youtu.be/l6PWbN2pDK8")
st.write("If you want to contribute, post your idea in #dev-channel of [hummingbot discord](https://discord.gg/CjxZtkrH)")
st.write("---")
