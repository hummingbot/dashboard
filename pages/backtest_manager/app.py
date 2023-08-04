import time
import webbrowser
from types import SimpleNamespace

import streamlit as st
from streamlit_elements import elements, mui

import constants
from quants_lab.strategy.strategy_analysis import StrategyAnalysis
from ui_components.dashboard import Dashboard
from ui_components.directional_strategies_file_explorer import DirectionalStrategiesFileExplorer
from ui_components.directional_strategy_creation_card import DirectionalStrategyCreationCard
from ui_components.editor import Editor
from ui_components.optimization_creation_card import OptimizationCreationCard
from ui_components.optimization_run_card import OptimizationRunCard
from ui_components.optimizations_file_explorer import OptimizationsStrategiesFileExplorer
from utils import os_utils
from utils.os_utils import load_directional_strategies

from utils.st_utils import initialize_st_page


initialize_st_page(title="Backtest Manager", icon="⚙️", initial_sidebar_state="collapsed")

# Start content here
if "strategy_params" not in st.session_state:
    st.session_state.strategy_params = {}

build, backtest, optimize, analyze = st.tabs(["Build", "Backtest", "Optimize", "Analyze"])

with build:
    # TODO:
    #    * Add videos explaining how to the triple barrier method works and how the backtesting is designed,
    #  link to video of how to create a strategy, etc in a toggle.
    #    * Add functionality to start strategy creation from scratch or by duplicating an existing one

    if "ds_board" not in st.session_state:
        board = Dashboard()
        ds_board = SimpleNamespace(
            dashboard=board,
            create_strategy_card=DirectionalStrategyCreationCard(board, 0, 0, 3, 1),
            file_explorer=DirectionalStrategiesFileExplorer(board, 0, 2, 3, 7),
            editor=Editor(board, 4, 2, 9, 7),
        )
        st.session_state.ds_board = ds_board

    else:
        ds_board = st.session_state.ds_board

    # Add new tabs
    for tab_name, content in ds_board.file_explorer.tabs.items():
        if tab_name not in ds_board.editor.tabs:
            ds_board.editor.add_tab(tab_name, content["content"], content["language"])

    # Remove deleted tabs
    for tab_name in list(ds_board.editor.tabs.keys()):
        if tab_name not in ds_board.file_explorer.tabs:
            ds_board.editor.remove_tab(tab_name)

    with elements("directional_strategies"):
        with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
            mui.Typography("🗂Directional Strategies", variant="h3", sx={"margin-bottom": "2rem"})
            with ds_board.dashboard():
                ds_board.create_strategy_card()
                ds_board.file_explorer()
                ds_board.editor()

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

    def run_optuna_dashboard():
        os_utils.execute_bash_command(f"optuna-dashboard sqlite:///data/backtesting/backtesting_report.db")
        time.sleep(5)
        webbrowser.open("http://127.0.0.1:8080/dashboard", new=2)

    if "op_board" not in st.session_state:
        board = Dashboard()
        op_board = SimpleNamespace(
            dashboard=board,
            run_optimization_card=OptimizationRunCard(board, 0, 0, 3, 1),
            create_optimization_card=OptimizationCreationCard(board, 0, 1, 3, 1),
            file_explorer=OptimizationsStrategiesFileExplorer(board, 0, 2, 3, 5),
            editor=Editor(board, 4, 2, 9, 7),
        )
        st.session_state.op_board = op_board

    else:
        op_board = st.session_state.op_board

    # Add new tabs
    for tab_name, content in op_board.file_explorer.tabs.items():
        if tab_name not in op_board.editor.tabs:
            op_board.editor.add_tab(tab_name, content["content"], content["language"])

    # Remove deleted tabs
    for tab_name in list(op_board.editor.tabs.keys()):
        if tab_name not in op_board.file_explorer.tabs:
            op_board.editor.remove_tab(tab_name)

    with elements("optimizations"):
        with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
            with mui.Grid(container=True, spacing=2):
                with mui.Grid(item=True, xs=10):
                    mui.Typography("🧪Optimizations", variant="h3", sx={"margin-bottom": "2rem"})
                with mui.Grid(item=True, xs=2):
                    with mui.Button(variant="outlined", color="primary", size="large",
                                    sx={"height": "100%", "width": "100%"}, onClick=run_optuna_dashboard):
                        mui.icon.AutoGraph()
                        mui.Typography("Run Optuna Dashboard", variant="body1")


            with op_board.dashboard():
                op_board.run_optimization_card()
                op_board.create_optimization_card()
                op_board.file_explorer()
                op_board.editor()


with analyze:
    # TODO:
    #   * Add graphs for all backtesting results
    #   * Add management of backtesting results (delete, rename, save, share, upload s3, etc)
    pass
