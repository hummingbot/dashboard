from functools import partial
import streamlit as st
from streamlit_elements import mui, editor, sync, lazy, event

from backend.utils.os_utils import save_file
from .dashboard import Dashboard


class Editor(Dashboard.Item):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._dark_theme = False
        self._index = 0
        self._tabs = {}
        self._editor_box_style = {
            "flex": 1,
            "minHeight": 0,
            "borderBottom": 1,
            "borderTop": 1,
            "borderColor": "divider"
        }

    def save_file(self):
        if len(self._tabs) > 0:
            label = list(self._tabs.keys())[self._index]
            content = self.get_content(label)
            file_name = label.split("/")[-1]
            path = "/".join(label.split("/")[:-1])
            save_file(name=file_name, content=content, path=path)
            st.info("File saved")

    def _change_tab(self, _, index):
        self._index = index

    @property
    def tabs(self):
        return self._tabs
    
    def update_content(self, label, content):
        self._tabs[label]["content"] = content

    def add_tab(self, label, default_content, language):
        self._tabs[label] = {
            "content": default_content,
            "language": language,
        }

    def remove_tab(self, label):
        del self._tabs[label]

    def get_content(self, label):
        return self._tabs[label]["content"]

    def __call__(self):
        with mui.Paper(key=self._key, sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"}, elevation=1):

            with self.title_bar("0px 15px 0px 15px"):
                with mui.Grid(container=True, spacing=4, sx={"display": "flex", "alignItems": "center"}):
                    with mui.Grid(item=True, xs=10, sx={"display": "flex", "alignItems": "center"}):
                        mui.icon.Terminal()
                        mui.Typography("Editor", variant="h6", sx={"marginLeft": 1})
                        with mui.Tabs(value=self._index, onChange=self._change_tab, scrollButtons=True,
                                      variant="scrollable", sx={"flex": 1}):
                            for label in self._tabs.keys():
                                mui.Tab(label=label)
                    with mui.Grid(item=True, xs=2, sx={"display": "flex", "justifyContent": "flex-end"}):
                        mui.Button("Apply Changes", variant="contained", onClick=sync())
                        mui.Button("Save Changes", variant="contained", onClick=self.save_file, sx={"mx": 1})

            for index, (label, tab) in enumerate(self._tabs.items()):
                with mui.Box(sx=self._editor_box_style, hidden=(index != self._index)):
                    editor.Monaco(
                        css={"padding": "0 2px 0 2px"},
                        defaultValue=tab["content"],
                        language=tab["language"],
                        onChange=lazy(partial(self.update_content, label)),
                        theme="vs-dark" if self._dark_mode else "light",
                        path=label,
                        options={
                            "wordWrap": True,
                            "fontSize": 16.5,
                        }
                    )

            with mui.Stack(direction="row", spacing=2, alignItems="center", sx={"padding": "10px"}):
                event.Hotkey("ctrl+s", sync(), bindInputs=True, overrideDefault=True)
