from streamlit_elements import mui

import constants
from backend.utils.os_utils import get_python_files_from_directory
from frontend.components.file_explorer_base import FileExplorerBase


class OptimizationsStrategiesFileExplorer(FileExplorerBase):
    def add_tree_view(self):
        with mui.lab.TreeView(defaultExpandIcon=mui.icon.ChevronRight, defaultCollapseIcon=mui.icon.ExpandMore,
                              onNodeSelect=lambda event, node_id: self.set_selected_file(event, node_id),
                              defaultExpanded=["optimization_strategies"]):
            with mui.lab.TreeItem(nodeId="optimization_strategies", label=f"🔬Studies"):
                optimizations = get_python_files_from_directory(constants.OPTIMIZATIONS_PATH)
                for optimization in optimizations:
                    mui.lab.TreeItem(nodeId=optimization, label=f"🐍{optimization.split('/')[-1]}")
