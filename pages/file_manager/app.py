import streamlit as st
from streamlit_elements import elements, mui, lazy, sync, event

from types import SimpleNamespace

import streamlit as st
from streamlit_elements import elements, mui, lazy, sync, event

from ui_components.dashboard import Dashboard
from ui_components.file_explorer import FileExplorer
from ui_components.editor import Editor
from utils.st_utils import initialize_st_page

initialize_st_page(title="File Manager", icon="🗂️", initial_sidebar_state="expanded")

if "editor_tabs" not in st.session_state:
    st.session_state.editor_tabs = {}

# TODO: Use this to save the current file selected
if "selected_file" not in st.session_state:
    st.session_state.selected_file = ""

if "w" not in st.session_state:
    board = Dashboard()
    w = SimpleNamespace(
        dashboard=board,
        file_explorer=FileExplorer(board, 0, 0, 3, 7),
        editor=Editor(board, 4, 0, 9, 7),
    )
    st.session_state.w = w
else:
    w = st.session_state.w

for tab_name, content in st.session_state.editor_tabs.items():
    if tab_name not in w.editor._tabs:
        w.editor.add_tab(tab_name, content["content"], content["language"], content["file_path"])

with elements("bot_config"):
    with mui.Paper(style={"padding": "2rem"}, variant="outlined"):
        mui.Typography("Select a file and click ✏️ to edit it or 🗑️ to delete it. Click 💾 to save your changes.", variant="body1", sx={"margin-bottom": "2rem"})
        event.Hotkey("ctrl+s", sync(), bindInputs=True, overrideDefault=True)
        with w.dashboard():
            w.file_explorer()
            w.editor()
