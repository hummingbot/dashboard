import time
import webbrowser
from types import SimpleNamespace

import streamlit as st
from streamlit_elements import elements, mui

from frontend.components.dashboard import Dashboard
from frontend.components.editor import Editor
from frontend.components.optimization_creation_card import OptimizationCreationCard
from frontend.components.optimization_run_card import OptimizationRunCard
from frontend.components.optimizations_file_explorer import OptimizationsStrategiesFileExplorer
from utils import os_utils

from utils.st_utils import initialize_st_page

initialize_st_page(title="Optimize", icon="🧪", initial_sidebar_state="collapsed")

def run_optuna_dashboard():
    os_utils.execute_bash_command(f"optuna-dashboard sqlite:///data/backtesting/backtesting_report.db")
    time.sleep(5)
    webbrowser.open("http://127.0.0.1:8080/dashboard", new=2)


if "op_board" not in st.session_state:
    board = Dashboard()
    op_board = SimpleNamespace(
        dashboard=board,
        create_optimization_card=OptimizationCreationCard(board, 0, 0, 6, 1),
        run_optimization_card=OptimizationRunCard(board, 6, 0, 6, 1),
        file_explorer=OptimizationsStrategiesFileExplorer(board, 0, 2, 3, 7),
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
                pass
            with mui.Grid(item=True, xs=2):
                with mui.Fab(variant="extended", color="primary", size="large", onClick=run_optuna_dashboard):
                    mui.Typography("Open Optuna Dashboard", variant="body1")

        with op_board.dashboard():
            op_board.create_optimization_card()
            op_board.run_optimization_card()
            op_board.file_explorer()
            op_board.editor()
