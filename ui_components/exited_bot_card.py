from docker_manager import DockerManager
from streamlit_elements import mui, lazy
from ui_components.dashboard import Dashboard
import streamlit as st
import time

from utils import os_utils
from utils.os_utils import get_python_files_from_directory, get_yml_files_from_directory


class ExitedBotCard(Dashboard.Item):

    def __init__(self, board, x, y, w, h, **item_props):
        super().__init__(board, x, y, w, h, **item_props)

    @staticmethod
    def remove_container(bot_name):
        DockerManager().remove_container(bot_name)
        os_utils.remove_directory(f"./hummingbot_files/bot_configs/{bot_name}")

    def __call__(self, bot_name: str):
        with mui.Card(key=self._key,
                      sx={"display": "flex", "flexDirection": "column", "borderRadius": 2, "overflow": "auto"},
                      elevation=2):
            mui.CardHeader(
                title=bot_name,
                subheader="Stopped",
                avatar=mui.Avatar("💀", sx={"bgcolor": "black"}),
                className=self._draggable_class,
            )

            with mui.CardActions():
                with mui.Grid(container=True, spacing=2):
                    with mui.Grid(item=True, xs=6):
                        with mui.Button(onClick=lambda: DockerManager().start_container(bot_name),
                                        variant="outlined",
                                        color="success",
                                        sx={"width": "100%"}):
                            mui.icon.PlayCircle()
                            mui.Typography("Start Instance")
                    with mui.Grid(item=True, xs=6):
                        with mui.Button(onClick=lambda: self.remove_container(bot_name),
                                        variant="outlined",
                                        color="error",
                                        sx={"width": "100%"}):
                            mui.icon.DeleteForever()
                            mui.Typography("Delete Instance")
