import time

import streamlit as st
from streamlit_elements import mui, lazy

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from utils.backend_api_client import BackendAPIClient
from .dashboard import Dashboard


class LaunchStrategyV2(Dashboard.Item):
    DEFAULT_ROWS = []
    DEFAULT_COLUMNS = [
        {"field": 'id', "headerName": 'ID', "width": 230},
        {"field": 'controller_name', "headerName": 'Controller Name', "width": 150, "editable": False, },
        {"field": 'controller_type', "headerName": 'Controller Type', "width": 150, "editable": False, },
        {"field": 'connector_name', "headerName": 'Connector', "width": 150, "editable": False, },
        {"field": 'trading_pair', "headerName": 'Trading pair', "width": 140, "editable": False, },
        {"field": 'total_amount_quote', "headerName": 'Total amount ($)', "width": 140, "editable": False, },
        {"field": 'max_loss_quote', "headerName": 'Max loss ($)', "width": 120, "editable": False, },
        {"field": 'stop_loss', "headerName": 'SL (%)', "width": 100, "editable": False, },
        {"field": 'take_profit', "headerName": 'TP (%)', "width": 100, "editable": False, },
        {"field": 'trailing_stop', "headerName": 'TS (%)', "width": 120, "editable": False, },
        {"field": 'time_limit', "headerName": 'Time limit', "width": 100, "editable": False, },
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)
        self._controller_configs_available = self._backend_api_client.get_all_controllers_config()
        self._controller_config_selected = None
        self._bot_name = None
        self._image_name = "dardonacci/hummingbot:latest"
        self._credentials = "master_account"

    def _set_bot_name(self, event):
        self._bot_name = event.target.value

    def _set_image_name(self, _, childs):
        self._image_name = childs.props.value

    def _set_credentials(self, _, childs):
        self._credentials = childs.props.value

    def _set_controller(self, event):
        self._controller_selected = event.target.value

    def _handle_row_selection(self, params, _):
        self._controller_config_selected = [param + ".yml" for param in params]

    def launch_new_bot(self):
        if self._bot_name and self._image_name and len(self._controller_config_selected) > 0:
            start_time_str = time.strftime("%Y.%m.%d_%H.%M")
            bot_name = f"{self._bot_name}-{start_time_str}"
            script_config = {
                "name": bot_name,
                "content": {
                    "markets": {},
                    "candles_config": [],
                    "controllers_config": self._controller_config_selected,
                    "config_update_interval": 20,
                    "script_file_name": "v2_generic_with_cash_out.py",
                    "time_to_cash_out": None,
                }
            }

            self._backend_api_client.add_script_config(script_config)
            deploy_config = {
                "instance_name": bot_name,
                "script": "v2_generic_with_cash_out.py",
                "script_config": bot_name + ".yml",
                "image": self._image_name,
                "credentials_profile": self._credentials,
            }
            self._backend_api_client.create_hummingbot_instance(deploy_config)
            with st.spinner('Starting Bot... This process may take a few seconds'):
                time.sleep(3)
        else:
            st.warning("You need to define the bot name and select the controllers configs "
                       "that you want to deploy.")

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
                    available_credentials = self._backend_api_client.get_available_credentials()
                    with mui.FormControl(variant="standard", sx={"width": "100%"}):
                        mui.FormHelperText("Credentials")
                        with mui.Select(label="Credentials", defaultValue=available_credentials[0],
                                        variant="standard", onChange=lazy(self._set_credentials)):
                            for master_config in available_credentials:
                                mui.MenuItem(master_config, value=master_config)
                with mui.Grid(item=True, xs=4):
                    mui.TextField(label="Instance Name", variant="outlined", onChange=lazy(self._set_bot_name),
                                  sx={"width": "100%"})
                with mui.Grid(item=True, xs=4):
                    available_images = self._backend_api_client.get_available_images("hummingbot")
                    with mui.FormControl(variant="standard", sx={"width": "100%"}):
                        mui.FormHelperText("Available Images")
                        with mui.Select(label="Hummingbot Image", defaultValue="hummingbot/hummingbot:latest",
                                        variant="standard", onChange=lazy(self._set_image_name)):
                            for image in available_images:
                                mui.MenuItem(image, value=image)
                with mui.Grid(item=True, xs=4):
                    with mui.Button(onClick=self.launch_new_bot,
                                    variant="outlined",
                                    color="success",
                                    sx={"width": "100%", "height": "100%"}):
                        mui.icon.AddCircleOutline()
                        mui.Typography("Create")
                all_controllers_config = self._backend_api_client.get_all_controllers_config()
                data = []
                for config in all_controllers_config:
                    data.append({"id": config["id"], "controller_name": config["controller_name"],
                                 "controller_type": config["controller_type"],
                                 "connector_name": config["connector_name"],
                                 "trading_pair": config["trading_pair"],
                                 "total_amount_quote": config["total_amount_quote"],
                                 "max_loss_quote": config["total_amount_quote"] * config["stop_loss"],
                                 "stop_loss": config["stop_loss"],
                                 "take_profit": config["take_profit"],
                                 "trailing_stop": str(config["trailing_stop"]["activation_price"]) + " / " +
                                                  str(config["trailing_stop"]["trailing_delta"]),
                                 "time_limit": config["time_limit"]})

                with mui.Grid(item=True, xs=12):
                    mui.Alert("Select the controller configs to deploy", severity="info")
                    with mui.Paper(key=self._key,
                                   sx={"display": "flex", "flexDirection": "column", "borderRadius": 3,
                                       "overflow": "hidden", "height": 1000},
                                   elevation=1):
                        with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                            mui.icon.ViewCompact()
                            mui.Typography("Controllers Config")
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
                # with mui.Grid(item=True, xs=8):
                #     try:
                #         encoder_decoder = ConfigEncoderDecoder(TradeType, OrderType, PositionMode)
                #         data = []
                #         for config in self._controller_configs_available:
                #             decoded_config = encoder_decoder.yaml_load(config)
                #             data.append({"id": config.split("/")[-1], "strategy_name": decoded_config["strategy_name"],
                #                          "exchange": decoded_config["exchange"], "trading_pair": decoded_config["trading_pair"]})
                #     except json.JSONDecodeError:
                #         data = self.DEFAULT_ROWS

                # with mui.Paper(key=self._key,
                #                sx={"display": "flex", "flexDirection": "column", "borderRadius": 3,
                #                    "overflow": "hidden", "height": 1000},
                #                elevation=1):
                #     with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                #         mui.icon.ViewCompact()
                #         mui.Typography("Data grid")
                #
                #     with mui.Box(sx={"flex": 1, "minHeight": 3}):
                #         mui.DataGrid(
                #             columns=self.DEFAULT_COLUMNS,
                #             rows=data,
                #             pageSize=15,
                #             rowsPerPageOptions=[15],
                #             checkboxSelection=True,
                #             disableSelectionOnClick=True,
                #             onSelectionModelChange=self._handle_row_selection,
                #         )
                #
