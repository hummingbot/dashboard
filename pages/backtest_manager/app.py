import datetime
import threading
import webbrowser

import streamlit as st
from pathlib import Path
from streamlit_ace import st_ace

import constants
from quants_lab.strategy.strategy_analysis import StrategyAnalysis
from utils import os_utils
from utils.file_templates import strategy_optimization_template, directional_strategy_template
from utils.os_utils import load_directional_strategies, save_file, get_function_from_file
import optuna

from utils.st_utils import initialize_st_page


initialize_st_page(title="Backtest Manager", icon="⚙️")

# Start content here
if "strategy_params" not in st.session_state:
    st.session_state.strategy_params = {}

create, modify, backtest, optimize, analyze = st.tabs(["Create", "Modify", "Backtest", "Optimize", "Analyze"])

with create:
    # TODO:
    #    * Add videos explaining how to the triple barrier method works and how the backtesting is designed,
    #  link to video of how to create a strategy, etc in a toggle.
    #    * Add functionality to start strategy creation from scratch or by duplicating an existing one
    c1, c2 = st.columns([4, 1])
    with c1:
        # TODO: Allow change the strategy name and see the effect in the code
        strategy_name = st.text_input("Strategy class name", value="CustomStrategy")
    with c2:
        update_strategy_name = st.button("Update Strategy Name")

    c1, c2 = st.columns([4, 1])
    with c1:
        # TODO: every time that we save and run the optimizations, we should save the code in a file
        #  so the user then can correlate the results with the code.
        if update_strategy_name:
            st.session_state.directional_strategy_code = st_ace(key="create_directional_strategy",
                                               value=directional_strategy_template(strategy_name),
                                               language='python',
                                               keybinding='vscode',
                                               theme='pastel_on_dark')
    with c2:
        if st.button("Save strategy"):
            save_file(name=f"{strategy_name.lower()}.py", content=st.session_state.directional_strategy_code,
                      path=constants.DIRECTIONAL_STRATEGIES_PATH)
            st.success(f"Strategy {strategy_name} saved successfully")

with modify:
    pass

with backtest:
    # TODO:
    #    * Add videos explaining how to the triple barrier method works and how the backtesting is designed,
    #  link to video of how to create a strategy, etc in a toggle.
    #    * Add performance analysis graphs of the backtesting run
    strategies = load_directional_strategies(constants.DIRECTIONAL_STRATEGIES_PATH)
    strategy_to_optimize = st.selectbox("Select strategy to backtest", strategies.keys())
    strategy = strategies[strategy_to_optimize]
    strategy_config = strategy["config"]
    field_schema = strategy_config.schema()["properties"]
    st.write("## Strategy parameters")
    c1, c2 = st.columns([5, 1])
    with c1:
        columns = st.columns(4)
        column_index = 0
        for field_name, properties in field_schema.items():
            field_type = properties["type"]
            with columns[column_index]:
                if field_type in ["number", "integer"]:
                    field_value = st.number_input(field_name,
                                                  value=properties["default"],
                                                  min_value=properties.get("minimum"),
                                                  max_value=properties.get("maximum"),
                                                  key=field_name)
                elif field_type == "string":
                    field_value = st.text_input(field_name, value=properties["default"])
                elif field_type == "boolean":
                    # TODO: Add support for boolean fields in optimize tab
                    field_value = st.checkbox(field_name, value=properties["default"])
                else:
                    raise ValueError(f"Field type {field_type} not supported")
                st.session_state["strategy_params"][field_name] = field_value
            column_index = (column_index + 1) % 4
    with c2:
        add_positions = st.checkbox("Add positions", value=True)
        add_volume = st.checkbox("Add volume", value=True)
        add_pnl = st.checkbox("Add PnL", value=True)

        run_backtesting_button = st.button("Run Backtesting!")
    if run_backtesting_button:
        config = strategy["config"](**st.session_state["strategy_params"])
        strategy = strategy["class"](config=config)
        # TODO: add form for order amount, leverage, tp, sl, etc.

        market_data, positions = strategy.run_backtesting(
            start='2021-04-01',
            order_amount=50,
            leverage=20,
            initial_portfolio=100,
            take_profit_multiplier=2.3,
            stop_loss_multiplier=1.2,
            time_limit=60 * 60 * 3,
            std_span=None,
        )
        strategy_analysis = StrategyAnalysis(
            positions=positions,
            candles_df=market_data,
        )
        st.text(strategy_analysis.text_report())
        # TODO: check why the pnl is not being plotted
        strategy_analysis.create_base_figure(volume=add_volume, positions=add_positions, trade_pnl=add_pnl)
        st.plotly_chart(strategy_analysis.figure(), use_container_width=True)

with optimize:
    # TODO:
    #  * Add videos explaining how to use the optimization tool, quick intro to optuna, etc in a toggle
    with st.container():
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            strategies = load_directional_strategies(constants.DIRECTIONAL_STRATEGIES_PATH)
            strategy_to_optimize = st.selectbox("Select strategy to optimize", strategies.keys())
        with c2:
            today = datetime.datetime.today()
            # TODO: add hints about the study name
            STUDY_NAME = st.text_input("Study name",
                                       f"{strategy_to_optimize}_study_{today.day:02d}-{today.month:02d}-{today.year}")
        with c3:
            generate_optimization_code_button = st.button("Generate Optimization Code")
            if st.button("Launch optuna dashboard"):
                os_utils.execute_bash_command(f"optuna-dashboard sqlite:///data/backtesting/backtesting_report.db")
                webbrowser.open("http://127.0.0.1:8080/dashboard", new=2)

    c1, c2 = st.columns([4, 1])
    if generate_optimization_code_button:
        with c1:
            # TODO: every time that we save and run the optimizations, we should save the code in a file
            #  so the user then can correlate the results with the code.
            st.session_state.optimization_code = st_ace(key="create_optimization_code",
                                       value=strategy_optimization_template(
                                           strategy_info=strategies[strategy_to_optimize]),
                                       language='python',
                                       keybinding='vscode',
                                       theme='pastel_on_dark')
    if "optimization_code" in st.session_state:
        with c2:
            if st.button("Run optimization"):
                save_file(name=f"{STUDY_NAME}.py", content=st.session_state.optimization_code, path=constants.OPTIMIZATIONS_PATH)
                study = optuna.create_study(direction="maximize", study_name=STUDY_NAME,
                                            storage="sqlite:///data/backtesting/backtesting_report.db",
                                            load_if_exists=True)
                objective = get_function_from_file(file_path=f"{constants.OPTIMIZATIONS_PATH}/{STUDY_NAME}.py",
                                                   function_name="objective")


                def optimization_process():
                    study.optimize(objective, n_trials=2000)


                optimization_thread = threading.Thread(target=optimization_process)
                optimization_thread.start()


with analyze:
    # TODO:
    #   * Add graphs for all backtesting results
    #   * Add management of backtesting results (delete, rename, save, share, upload s3, etc)
    pass
