import streamlit as st
from st_pages import Page, Section, show_pages
from streamlit_authenticator import Authenticate

from utils.os_utils import read_yaml_file, dump_dict_to_yaml


config = read_yaml_file("credentials.yml")

if "authenticator" not in st.session_state:
    st.session_state.authenticator = Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )

if st.session_state["authentication_status"]:
    config["credentials"] = st.session_state.authenticator.credentials
    dump_dict_to_yaml(config, "credentials.yml")
    with st.sidebar:
        st.session_state.authenticator.logout('Logout', 'sidebar')
        st.write(f'Welcome *{st.session_state["name"]}*')
    show_pages(
        [
            Page("main.py", "Hummingbot Dashboard", "📊"),
            Section("Bot Orchestration", "🐙"),
            Page("pages/master_conf/app.py", "Credentials", "🗝️"),
            Page("pages/bot_orchestration/app.py", "Instances", "🦅"),
            Page("pages/file_manager/app.py", "File Explorer", "🗂"),
            Section("Backtest Manager", "⚙️"),
            Page("pages/candles_downloader/app.py", "Get Data", "💾"),
            Page("pages/backtest_manager/create.py", "Create", "⚔️"),
            Page("pages/backtest_manager/optimize.py", "Optimize", "🧪"),
            Page("pages/backtest_manager/analyze.py", "Analyze", "🔬"),
            # Page("pages/backtest_manager/simulate.py", "Simulate", "📈"),
            Page("pages/launch_bot/app.py", "Deploy", "🙌"),
            Section("Community Pages", "👨‍👩‍👧‍👦"),
            Page("pages/strategy_performance/app.py", "Strategy Performance", "🚀"),
            Page("pages/db_inspector/app.py", "DB Inspector", "🔍"),
            Page("pages/token_spreads/app.py", "Token Spreads", "🧙"),
            Page("pages/tvl_vs_mcap/app.py", "TVL vs Market Cap", "🦉"),
        ]
    )
    # initialize_st_page(title="Hummingbot Dashboard", icon="📊", initial_sidebar_state="expanded")
    st.write("Watch this video to understand how the dashboard works! 🦅")
    c1, c2, c3 = st.columns([1, 6, 1])
    st.write("---")
    with c2:
        st.video("https://youtu.be/2q9HSyIPuf4")
    st.write(
        "Please give us feedback in the **#dashboard** channel of the [Hummingbot Discord](https://discord.gg/hummingbot)! 🙏")
else:
    show_pages([
        Page("main.py", "Hummingbot Dashboard", "📊"),
    ])
    name, authentication_status, username = st.session_state.authenticator.login('Login', 'main')
    if st.session_state["authentication_status"] == False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] == None:
        st.warning('Please enter your username and password')
    st.write("---")
    st.write("If you are pre-authorized, you can login with your pre-authorized mail!")
    st.session_state.authenticator.register_user('Register', 'main')

