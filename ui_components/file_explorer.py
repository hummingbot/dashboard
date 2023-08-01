import streamlit as st
from streamlit_elements import media, mui, sync, lazy

from utils.os_utils import get_directories_from_directory
from .dashboard import Dashboard


class FileExplorer(Dashboard.Item):
    _directory = "hummingbot_files/bot_configs"

    @staticmethod
    def set_selected_file(_, node_id):
        st.session_state.selected_file = node_id

    def __call__(self):
        bots = [bot.split("/")[-2] for bot in get_directories_from_directory("hummingbot_files/bot_configs") if "data_downloader" not in bot]
        with mui.Paper(key=self._key, sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"}, elevation=1):
            with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                mui.icon.Folder()
                mui.Typography("File Explorer")

            with mui.lab.TreeView(defaultExpandIcon=mui.icon.ChevronRight, defaultCollapseIcon=mui.icon.ExpandMore,
                                  onNodeSelect=lazy(lambda event, node_id: self.set_selected_file(event, node_id))):
                for bot in bots:
                    with mui.lab.TreeItem(nodeId=bot, label=f"🤖{bot}"):
                        for file in get_python_files_from_directory(f"hummingbot_files/bot_configs/{bot}/scripts"):
                            mui.lab.TreeItem(nodeId=file, label=f"🐍{file.split('/')[-1]}")
                        for file in get_yml_files_from_directory(f"hummingbot_files/bot_configs/{bot}/conf/strategies"):
                            mui.lab.TreeItem(nodeId=file, label=f"📄 {file.split('/')[-1]}")
