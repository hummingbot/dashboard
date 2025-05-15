from types import SimpleNamespace

import streamlit as st
from streamlit_elements import elements, mui

from frontend.components.controllers_file_explorer import ControllersFileExplorer
from frontend.components.dashboard import Dashboard
from frontend.components.directional_strategy_creation_card import DirectionalStrategyCreationCard
from frontend.components.editor import Editor
from frontend.st_utils import initialize_st_page

initialize_st_page(title="Create", icon="️⚔️")

# TODO:
#    * Add videos explaining how to the triple barrier method works and how the backtesting is designed,
#  link to video of how to create a strategy, etc in a toggle.
#    * Add functionality to start strategy creation from scratch or by duplicating an existing one

if "ds_board" not in st.session_state:
    board = Dashboard()
    ds_board = SimpleNamespace(
        dashboard=board,
        create_strategy_card=DirectionalStrategyCreationCard(board, 0, 0, 12, 1),
        file_explorer=ControllersFileExplorer(board, 0, 2, 3, 7),
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
        with ds_board.dashboard():
            ds_board.create_strategy_card()
            ds_board.file_explorer()
            ds_board.editor()
