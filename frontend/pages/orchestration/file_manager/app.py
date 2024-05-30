from types import SimpleNamespace
import streamlit as st
from streamlit_elements import elements, mui

from frontend.components.bots_file_explorer import BotsFileExplorer
from frontend.components.dashboard import Dashboard
from frontend.components.editor import Editor
from frontend.st_utils import initialize_st_page

initialize_st_page(title="Strategy Configs", icon="🗂️")


if "fe_board" not in st.session_state:
    board = Dashboard()
    fe_board = SimpleNamespace(
        dashboard=board,
        file_explorer=BotsFileExplorer(board, 0, 0, 3, 7),
        editor=Editor(board, 4, 0, 9, 7),
    )
    st.session_state.fe_board = fe_board

else:
    fe_board = st.session_state.fe_board

# Add new tabs
for tab_name, content in fe_board.file_explorer.tabs.items():
    if tab_name not in fe_board.editor.tabs:
        fe_board.editor.add_tab(tab_name, content["content"], content["language"])

# Remove deleted tabs
for tab_name in list(fe_board.editor.tabs.keys()):
    if tab_name not in fe_board.file_explorer.tabs:
        fe_board.editor.remove_tab(tab_name)

with elements("file_manager"):
    with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
        with fe_board.dashboard():
            fe_board.file_explorer()
            fe_board.editor()
