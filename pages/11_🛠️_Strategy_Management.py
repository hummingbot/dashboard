import pandas_ta as ta # noqa
import streamlit as st
import constants
from streamlit_ace import st_ace
from quants_lab.utils.scripts import *
from quants_lab.backtesting.backtesting import Backtesting
from quants_lab.backtesting.backtesting_analysis import BacktestingAnalysis


st.set_page_config(
    page_title="Hummingbot Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title("Strategy management")
create_tab, modify_tab, backtesting_tab = st.tabs(["Create", "Modify", "Backtest"])
with create_tab:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Create your own strategy")
        st.markdown("In this module you'll be able to create your own strategy. Start by choosing a strategy type:")
        selected_type = st.selectbox("Strategy", ["Directional Strategies"])
        strategy_name = st.text_input("Strategy name:", "RandomStrategy")
        selected_exchange = st.selectbox("Exchange:", constants.EXCHANGES)
        selected_trading_pair = st.selectbox("Trading pair:", constants.TRADING_PAIRS)
        selected_interval = st.selectbox("Interval:", constants.INTERVALS)
    with col2:
        st.video("https://www.youtube.com/watch?v=ZM6phvAmaFI")

    st.session_state.strategy_code = st_ace(key="create_code",
                                            value=directional_strategy_template(strategy_name=strategy_name,
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
            # TODO: Warning if this overwrites
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
with backtesting_tab:
    file_path = st.text_input("Folder path: ", "quants_lab/strategy/custom_scripts")
    scripts = load_scripts(directory=file_path)
    if scripts:
        selected_script = st.selectbox("Choose your backtesting script:", scripts)
        classes = load_classes_from_file(selected_script)
        selected_class = st.selectbox("Choose your strategy class:", classes)
        candles_list = load_candles("data/candles")
        selected_candles = st.selectbox("Choose your candles:", candles_list)
        candles = pd.read_csv(selected_candles)
        # if st.button("Backtest!"):
        strategy = selected_class[1]()
        backtesting = Backtesting(strategy=strategy)
        st.subheader("Backtesting params")
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_order_amount = st.number_input("Order amount", 50)
            selected_leverage = st.number_input("Leverage", 10)
        with col2:
            selected_initial_portfolio = st.number_input("Initial Portfolio", 100)
            selected_time_limit = st.number_input("Time Limit (min)", 60)
        with col3:
            selected_tp_multiplier = st.number_input("Take Profit Multiplier", 1.0)
            selected_sl_multiplier = st.number_input("Stop Loss Multiplier", 1.0)
        if st.button("Run backtesting!"):
            positions = backtesting.run_backtesting(
                order_amount=selected_order_amount,
                leverage=selected_leverage,
                initial_portfolio=selected_initial_portfolio,
                take_profit_multiplier=selected_tp_multiplier,
                stop_loss_multiplier=selected_sl_multiplier,
                time_limit=60 * selected_time_limit,
                std_span=None,
            )
            backtesting_analysis = BacktestingAnalysis(positions=positions, candles_df=candles)
            backtesting_analysis.create_base_figure(volume=False, positions=True, extra_rows=1)
            backtesting_analysis.add_trade_pnl(row=2)
            c1, c2 = st.columns([0.2, 0.8])
            with c1:
                st.text(backtesting_analysis.text_report())
            with c2:
                st.plotly_chart(backtesting_analysis.figure(), use_container_width=True)
