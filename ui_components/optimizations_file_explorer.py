from streamlit_elements import mui

import constants
from ui_components.file_explorer_base import FileExplorerBase
from utils.os_utils import get_python_files_from_directory


class OptimizationsStrategiesFileExplorer(FileExplorerBase):
    def add_tree_view(self):
        with mui.lab.TreeView(defaultExpandIcon=mui.icon.ChevronRight, defaultCollapseIcon=mui.icon.ExpandMore,
                              onNodeSelect=lambda event, node_id: self.set_selected_file(event, node_id),
                              defaultExpanded=["optimization_strategies"]):
            with mui.lab.TreeItem(nodeId="optimization_strategies", label=f"🔬Studies"):
                optimizations = get_python_files_from_directory(constants.OPTIMIZATIONS_PATH)
                for optimization in optimizations:
                    mui.lab.TreeItem(nodeId=optimization, label=f"🐍{optimization.split('/')[-1]}")
