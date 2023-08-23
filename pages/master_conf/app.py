import glob
import os
from types import SimpleNamespace
import streamlit as st
from streamlit_elements import elements, mui

import constants
from ui_components.dashboard import Dashboard
from ui_components.editor import Editor
from ui_components.launch_master_bot_card import LaunchMasterBotCard
from ui_components.master_conf_file_explorer import MasterConfFileExplorer
from utils.st_utils import initialize_st_page


initialize_st_page(title="Master Conf", icon="🗝️", initial_sidebar_state="expanded")


if "mc_board" not in st.session_state:
    board = Dashboard()
    mc_board = SimpleNamespace(
        dashboard=board,
        launch_master_bot=LaunchMasterBotCard(board, 0, 0, 12, 1),
        file_explorer=MasterConfFileExplorer(board, 0, 4, 3, 7),
        editor=Editor(board, 4, 4, 9, 7),
    )
    st.session_state.mc_board = mc_board

else:
    mc_board = st.session_state.mc_board

# Add new tabs
for tab_name, content in mc_board.file_explorer.tabs.items():
    if tab_name not in mc_board.editor.tabs:
        mc_board.editor.add_tab(tab_name, content["content"], content["language"])

# Remove deleted tabs
for tab_name in list(mc_board.editor.tabs.keys()):
    if tab_name not in mc_board.file_explorer.tabs:
        mc_board.editor.remove_tab(tab_name)



with elements("file_manager"):
    with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
        with mc_board.dashboard():
            mc_board.launch_master_bot()
            mc_board.file_explorer()
            mc_board.editor()
