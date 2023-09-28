from streamlit_elements import mui

import constants
from ui_components.file_explorer_base import FileExplorerBase
from utils.os_utils import get_python_files_from_directory


class DirectionalStrategiesFileExplorer(FileExplorerBase):
    def add_tree_view(self):
        with mui.lab.TreeView(defaultExpandIcon=mui.icon.ChevronRight, defaultCollapseIcon=mui.icon.ExpandMore,
                              onNodeSelect=lambda event, node_id: self.set_selected_file(event, node_id),
                              defaultExpanded=["directional_strategies"]):
            with mui.lab.TreeItem(nodeId="directional_strategies", label=f"⚔️Directional Strategies"):
                strategies = get_python_files_from_directory(constants.CONTROLLERS_PATH)
                for strategy in strategies:
                    mui.lab.TreeItem(nodeId=strategy, label=f"🐍{strategy.split('/')[-1]}")
