import pandas_ta as ta # noqa
import streamlit as st
import constants
from streamlit_ace import st_ace
from quants_lab.utils.scripts import *

st.set_page_config(
    page_title="Hummingbot Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("Strategy management")
create_tab, modify_tab = st.tabs(["Create", "Modify"])
with create_tab:
    strategy_name = st.text_input("Strategy name:", "RandomStrategy")
    selected_exchange = st.selectbox("Exchange:", constants.EXCHANGES)
    selected_trading_pair = st.selectbox("Trading pair:", constants.TRADING_PAIRS)
    selected_interval = st.selectbox("Interval:", constants.INTERVALS)
    st.session_state.strategy_code = st_ace(value=directional_strategy_template(strategy_name=strategy_name,
                                                                                exchange=selected_exchange,
                                                                                trading_pair=selected_trading_pair,
                                                                                interval=selected_interval),
                                            language='python',
                                            keybinding='vscode',
                                            theme='pastel_on_dark')
    st.subheader("Save your progress")
    col1, col2, col3, col4 = st.columns([1, 1, 0.3, 0.3])
    with col1:
        file_name = st.text_input("File name:", strategy_name)
    with col2:
        file_path = st.text_input("File path:", "quants_lab/strategy/custom_scripts")
    with col3:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("Save strategy"):
            save_script(name=f"{file_name}.py",
                        content=st.session_state.strategy_code,
                        path=file_path)
    with col4:
        # TODO: Add code sintax analyzer
        code_review = check_code(st.session_state.strategy_code)

with modify_tab:
    file_path = st.text_input("Scripts folder:", "quants_lab/strategy/custom_scripts")
    scripts = load_scripts(directory=file_path)
    if scripts:
        selected_script = st.selectbox("Choose your script:", scripts)
        modified_script = st_ace(value=open_and_read_file(selected_script),
                                 language='python',
                                 keybinding='vscode',
                                 theme='pastel_on_dark')
        if st.button("Save changes"):
            save_script(name=selected_script.split("/")[-1],
                        content=modified_script,
                        path=file_path)

    else:
        st.info("We couldn't find any script here")
