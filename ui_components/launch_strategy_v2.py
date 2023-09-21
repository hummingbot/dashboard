import json
import os
import time

from docker_manager import DockerManager
import streamlit as st
from hummingbot.core.data_type.common import PositionMode, OrderType, TradeType
from hummingbot.smart_components.utils import ConfigEncoderDecoder
from streamlit_elements import mui, lazy

import constants
from utils.os_utils import get_directories_from_directory, get_python_files_from_directory, \
    get_yml_files_from_directory
from .dashboard import Dashboard


class LaunchStrategyV2(Dashboard.Item):
    DEFAULT_ROWS = []
    DEFAULT_COLUMNS = DEFAULT_COLUMNS = [
        {"field": 'id', "headerName": 'ID', "width": 180},
        {"field": 'strategy_name', "headerName": 'Strategy Name', "width": 180, "editable": False, },
        {"field": 'exchange', "headerName": 'Exchange', "width": 180, "editable": True, },
        {"field": 'trading_pair', "headerName": 'Trading_pair', "width": 180, "editable": True, },
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._controllers_available = get_python_files_from_directory(constants.CONTROLLERS_PATH)
        self._controller_selected = self._controllers_available[0]
        self._controller_configs_available = get_yml_files_from_directory("hummingbot_files/controller_configs")
        self._controller_config_selected = None
        self._bot_name = None
        self._image_name = "hummingbot/hummingbot:latest"
        self._base_bot_config = "master_bot_conf"

    def _set_bot_name(self, event):
        self._bot_name = event.target.value

    def _set_image_name(self, event):
        self._image_name = event.target.value

    def _set_base_bot_config(self, event):
        self._base_bot_config = event.target.value

    def _set_controller(self, event):
        self._controller_selected = event.target.value

    def _handle_row_selection(self, params, _):
        self._controller_config_selected = params

    def launch_new_bot(self):
        if self._bot_name and self._image_name:
            bot_name = f"hummingbot-{self._bot_name}"
            extra_environment_variables = ["-e", "CONFIG_FILE_NAME=strategy_v2_launcher.py",
                                           "-e", f"controller_configs={','.join(self._controller_config_selected)}"]
            DockerManager().create_hummingbot_instance(instance_name=bot_name,
                                                       base_conf_folder=f"{constants.HUMMINGBOT_TEMPLATES}/{self._base_bot_config}/.",
                                                       target_conf_folder=f"{constants.BOTS_FOLDER}/{bot_name}/.",
                                                       controllers_folder=constants.CONTROLLERS_PATH,
                                                       controllers_config_folder=constants.CONTROLLERS_CONFIG_PATH,
                                                       extra_environment_variables=extra_environment_variables,
                                                       image=self._image_name,
                                                       )
            with st.spinner('Starting Master Configs instance... This process may take a few seconds'):
                time.sleep(3)
        else:
            st.warning("You need to define the bot name and image in order to create one.")

    def __call__(self):
        with mui.Paper(key=self._key,
                       sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"},
                       elevation=1):
            with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                mui.Typography("🚀 Select the controller configs to launch", variant="h5")

            with mui.Grid(container=True, spacing=2, sx={"padding": "10px 15px 10px 15px"}):
                with mui.Grid(item=True, xs=8):
                    mui.Alert(
                        "The new instance will contain the credentials configured in the following base instance:",
                        severity="info")
                with mui.Grid(item=True, xs=4):
                    master_configs = [conf.split("/")[-2] for conf in
                                      get_directories_from_directory(constants.HUMMINGBOT_TEMPLATES) if
                                      "bot_conf" in conf]
                    with mui.FormControl(variant="standard", sx={"width": "100%"}):
                        mui.FormHelperText("Base Configs")
                        with mui.Select(label="Base Configs", defaultValue=master_configs[0],
                                        variant="standard", onChange=lazy(self._set_base_bot_config)):
                            for master_config in master_configs:
                                mui.MenuItem(master_config, value=master_config)
                with mui.Grid(item=True, xs=4):
                    mui.TextField(label="Instance Name", variant="outlined", onChange=lazy(self._set_bot_name),
                                  sx={"width": "100%"})
                with mui.Grid(item=True, xs=4):
                    mui.TextField(label="Hummingbot Image",
                                  defaultValue="hummingbot/hummingbot:latest",
                                  variant="outlined",
                                  placeholder="hummingbot-[name]",
                                  onChange=lazy(self._set_image_name),
                                  sx={"width": "100%"})
                with mui.Grid(item=True, xs=4):
                    with mui.Button(onClick=self.launch_new_bot,
                                variant="outlined",
                                color="success",
                                sx={"width": "100%", "height": "100%"}):
                        mui.icon.AddCircleOutline()
                        mui.Typography("Create")

                with mui.Grid(item=True, xs=8):
                    try:
                        encoder_decoder = ConfigEncoderDecoder(TradeType, OrderType, PositionMode)
                        data = []
                        for config in self._controller_configs_available:
                            decoded_config = encoder_decoder.yaml_load(config)
                            data.append({"id": config.split("/")[-1], "strategy_name": decoded_config["strategy_name"],
                                         "exchange": decoded_config["exchange"], "trading_pair": decoded_config["trading_pair"]})
                    except json.JSONDecodeError:
                        data = self.DEFAULT_ROWS

                    with mui.Paper(key=self._key,
                                   sx={"display": "flex", "flexDirection": "column", "borderRadius": 3,
                                       "overflow": "hidden", "height": 1000},
                                   elevation=1):
                        with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                            mui.icon.ViewCompact()
                            mui.Typography("Data grid")

                        with mui.Box(sx={"flex": 1, "minHeight": 3}):
                            mui.DataGrid(
                                columns=self.DEFAULT_COLUMNS,
                                rows=data,
                                pageSize=15,
                                rowsPerPageOptions=[15],
                                checkboxSelection=True,
                                disableSelectionOnClick=True,
                                onSelectionModelChange=self._handle_row_selection,
                            )

