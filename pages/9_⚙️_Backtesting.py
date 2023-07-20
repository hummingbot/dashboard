import streamlit as st


st.set_page_config(
    page_title="Hummingbot Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("⚙️ Backtesting")

create, modify, backtest, optimize, analyze = st.tabs(["Create", "Modify", "Backtest", "Optimize", "Analyze"])

with create:
    pass

with modify:
    pass

with backtest:
    pass

with optimize:
    pass

with analyze:
    pass
