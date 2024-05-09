from streamlit_elements import mui

import constants
from frontend.components.file_explorer_base import FileExplorerBase
from utils.os_utils import load_controllers


class ControllersFileExplorer(FileExplorerBase):
    def add_tree_view(self):
        with mui.lab.TreeView(defaultExpandIcon=mui.icon.ChevronRight, defaultCollapseIcon=mui.icon.ExpandMore,
                              onNodeSelect=lambda event, node_id: self.set_selected_file(event, node_id),
                              defaultExpanded=["directional_strategies"]):
            available_controllers = load_controllers(constants.CONTROLLERS_PATH)
            with mui.lab.TreeItem(nodeId="directional_strategies", label=f"⚔️Directional Strategies"):
                for controller in available_controllers:
                    if available_controllers[controller]["type"] == "directional_trading":
                        mui.lab.TreeItem(nodeId=constants.CONTROLLERS_PATH + "/" + controller + ".py", label=f"🐍{controller}")
            with mui.lab.TreeItem(nodeId="market_making_strategies", label=f"🪙Market Making Strategies"):
                for controller in available_controllers:
                    if available_controllers[controller]["type"] == "market_making":
                        mui.lab.TreeItem(nodeId=constants.CONTROLLERS_PATH + "/" + controller + ".py", label=f"🐍{controller}")
