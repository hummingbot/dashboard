from streamlit_elements import mui

import constants
from ui_components.file_explorer_base import FileExplorerBase
from utils.os_utils import get_directories_from_directory, get_python_files_from_directory, \
    get_yml_files_from_directory, get_log_files_from_directory


class MasterConfFileExplorer(FileExplorerBase):
    def add_tree_view(self):
        directory = constants.HUMMINGBOT_TEMPLATES
        configs = [conf.split("/")[-2] for conf in get_directories_from_directory(directory) if "master_bot_conf" in conf]
        with mui.lab.TreeView(defaultExpandIcon=mui.icon.ChevronRight, defaultCollapseIcon=mui.icon.ExpandMore,
                              onNodeSelect=lambda event, node_id: self.set_selected_file(event, node_id),
                              defaultExpanded=["master_bot_conf"]):
            for conf in configs:
                with mui.lab.TreeItem(nodeId=conf, label=f"🤖{conf}"):
                    with mui.lab.TreeItem(nodeId=f"scripts_{conf}", label="🐍Scripts"):
                        for file in get_python_files_from_directory(f"{directory}/{conf}/scripts"):
                            mui.lab.TreeItem(nodeId=file, label=f"📄{file.split('/')[-1]}")
                    with mui.lab.TreeItem(nodeId=f"strategies_{conf}", label="📜Strategies"):
                        for file in get_yml_files_from_directory(f"{directory}/{conf}/conf/strategies"):
                            mui.lab.TreeItem(nodeId=file, label=f"📄 {file.split('/')[-1]}")
                    with mui.lab.TreeItem(nodeId=f"configs_{conf}", label="🗄Client Config"):
                        for file in get_yml_files_from_directory(f"{directory}/{conf}/conf"):
                            mui.lab.TreeItem(nodeId=file, label=f"📄 {file.split('/')[-1]}")
                    with mui.lab.TreeItem(nodeId=f"keys_{conf}", label="🔑Keys"):
                        for file in get_yml_files_from_directory(f"{directory}/{conf}/conf/connectors"):
                            mui.lab.TreeItem(nodeId=file, label=f"🔑 {file.split('/')[-1]}")
                    with mui.lab.TreeItem(nodeId=f"logs_{conf}", label="🗄️Logs"):
                        for file in get_log_files_from_directory(f"{directory}/{conf}/logs"):
                            mui.lab.TreeItem(nodeId=file, label=f"📄 {file.split('/')[-1]}")
