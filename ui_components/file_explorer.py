import streamlit as st
from streamlit_elements import mui, elements

from utils.os_utils import get_directories_from_directory, get_python_files_from_directory, \
    get_yml_files_from_directory, load_file, remove_file
from .dashboard import Dashboard


class FileExplorer(Dashboard.Item):
    _directory = "hummingbot_files/bot_configs"

    @staticmethod
    def set_selected_file(_, node_id):
        st.session_state.selected_file = node_id

    @staticmethod
    def delete_file():
        if st.session_state.selected_file:
            if st.session_state.selected_file.endswith(".py") or st.session_state.selected_file.endswith(".yml"):
                remove_file(st.session_state.selected_file)
            else:
                st.error("You can't delete the directory since it's a volume."
                         "If you want to do it, go to the orchestrate tab and delete the container")

    def edit_file(self):
        short_path = st.session_state.selected_file.replace(self._directory, "")
        if st.session_state.selected_file.endswith(".py"):
            st.session_state.editor_tabs[short_path] = {"content": load_file(st.session_state.selected_file),
                                                        "language": "python"}
        elif st.session_state.selected_file.endswith(".yml"):
            st.session_state.editor_tabs[short_path] = {"content": load_file(st.session_state.selected_file),
                                                        "language": "yaml"}

    def __call__(self):
        bots = [bot.split("/")[-2] for bot in get_directories_from_directory(self._directory) if
                "data_downloader" not in bot]
        with mui.Paper(key=self._key,
                       sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"},
                       elevation=1):
            with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                with mui.Grid(container=True, spacing=4, sx={"display": "flex", "alignItems": "center"}):
                    with mui.Grid(item=True, xs=6, sx={"display": "flex", "alignItems": "center"}):
                        mui.icon.Folder()
                        mui.Typography("File Explorer")
                    with mui.Grid(item=True, xs=6, sx={"display": "flex", "justifyContent": "flex-end"}):
                        mui.IconButton(mui.icon.Delete, onClick=self.delete_file, sx={"mx": 1})
                        mui.IconButton(mui.icon.Edit, onClick=self.edit_file, sx={"mx": 1})
            with mui.Box(sx={"overflow": "auto"}):
                with mui.lab.TreeView(defaultExpandIcon=mui.icon.ChevronRight, defaultCollapseIcon=mui.icon.ExpandMore,
                                      onNodeSelect=lambda event, node_id: self.set_selected_file(event, node_id)):
                    for bot in bots:
                        with mui.lab.TreeItem(nodeId=bot, label=f"🤖{bot}"):
                            for file in get_python_files_from_directory(f"{self._directory}/{bot}/scripts"):
                                mui.lab.TreeItem(nodeId=file, label=f"🐍{file.split('/')[-1]}")
                            for file in get_yml_files_from_directory(f"{self._directory}/{bot}/conf/strategies"):
                                mui.lab.TreeItem(nodeId=file, label=f"📄 {file.split('/')[-1]}")
