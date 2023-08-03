import streamlit as st
from streamlit_elements import mui, elements

from utils.os_utils import load_file, remove_file
from .dashboard import Dashboard


class FileExplorerBase(Dashboard.Item):

    def __init__(self, board, x, y, w, h, **item_props):
        super().__init__(board, x, y, w, h, **item_props)
        self._tabs = {}
        self.selected_file = None

    def set_selected_file(self, _, node_id):
        self.selected_file = node_id

    def delete_file(self):
        if self.is_file_editable:
            remove_file(self.selected_file)
        else:
            st.error("You can't delete the directory since it's a volume."
                     "If you want to do it, go to the orchestrate tab and delete the container")

    @property
    def tabs(self):
        return self._tabs

    def add_file_to_tab(self):
        language = "python" if self.selected_file.endswith(".py") else "yaml"
        if self.is_file_editable:
            self._tabs[self.selected_file] = {"content": load_file(self.selected_file),
                                                          "language": language}

    def remove_file_from_tab(self):
        if self.is_file_editable and self.selected_file in self._tabs:
            del self._tabs[self.selected_file]

    @property
    def is_file_editable(self):
        return self.selected_file and \
            (self.selected_file.endswith(".py") or self.selected_file.endswith(".yml")
             or "log" in self.selected_file)

    def add_tree_view(self):
        raise NotImplementedError

    def __call__(self):
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
                        mui.IconButton(mui.icon.Edit, onClick=self.add_file_to_tab, sx={"mx": 1})
                        mui.IconButton(mui.icon.Close, onClick=self.remove_file_from_tab, sx={"mx": 1})
            with mui.Box(sx={"overflow": "auto"}):
                self.add_tree_view()

