from streamlit_elements import mui

from ui_components.file_explorer_base import FileExplorerBase
from utils.os_utils import get_directories_from_directory, get_python_files_from_directory, \
    get_yml_files_from_directory, get_log_files_from_directory


class BotsFileExplorer(FileExplorerBase):
    def add_tree_view(self):
        bots = [bot.split("/")[-2] for bot in get_directories_from_directory(self._directory) if
                "data_downloader" not in bot]
        with mui.lab.TreeView(defaultExpandIcon=mui.icon.ChevronRight, defaultCollapseIcon=mui.icon.ExpandMore,
                              onNodeSelect=lambda event, node_id: self.set_selected_file(event, node_id)):
            for bot in bots:
                with mui.lab.TreeItem(nodeId=bot, label=f"🤖{bot}"):
                    with mui.lab.TreeItem(nodeId=f"scripts_{bot}", label="🐍Scripts"):
                        for file in get_python_files_from_directory(f"{self._directory}/{bot}/scripts"):
                            mui.lab.TreeItem(nodeId=file, label=f"📄{file.split('/')[-1]}")
                    with mui.lab.TreeItem(nodeId=f"strategies_{bot}", label="📜Strategies"):
                        for file in get_yml_files_from_directory(f"{self._directory}/{bot}/conf/strategies"):
                            mui.lab.TreeItem(nodeId=file, label=f"📄 {file.split('/')[-1]}")
                    with mui.lab.TreeItem(nodeId=f"logs_{bot}", label="🗄️Logs"):
                        for file in get_log_files_from_directory(f"{self._directory}/{bot}/logs"):
                            mui.lab.TreeItem(nodeId=file, label=f"📄 {file.split('/')[-1]}")
