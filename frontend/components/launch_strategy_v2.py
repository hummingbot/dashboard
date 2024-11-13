import time

import streamlit as st
from streamlit_elements import lazy, mui

from ..st_utils import get_backend_api_client
from .dashboard import Dashboard


class LaunchStrategyV2(Dashboard.Item):
    DEFAULT_ROWS = []
    DEFAULT_COLUMNS = [
        {"field": 'config_base', "headerName": 'Config Base', "minWidth": 160, "editable": False, },
        {"field": 'version', "headerName": 'Version', "minWidth": 100, "editable": False, },
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
        self._backend_api_client = get_backend_api_client()
        self._controller_configs_available = self._backend_api_client.get_all_controllers_config()
        self._controller_config_selected = None
        self._bot_name = None
        self._image_name = "hummingbot/hummingbot:latest"
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
        if not self._bot_name:
            st.warning("You need to define the bot name.")
            return
        if not self._image_name:
            st.warning("You need to select the hummingbot image.")
            return
        if not self._controller_config_selected or len(self._controller_config_selected) == 0:
            st.warning("You need to select the controllers configs. Please select at least one controller "
                       "config by clicking on the checkbox.")
            return
        start_time_str = time.strftime("%Y.%m.%d_%H.%M")
        bot_name = f"{self._bot_name}-{start_time_str}"
        script_config = {
            "name": bot_name,
            "content": {
                "markets": {},
                "candles_config": [],
                "controllers_config": self._controller_config_selected,
                "config_update_interval": 10,
                "script_file_name": "v2_with_controllers.py",
                "time_to_cash_out": None,
            }
        }

        self._backend_api_client.add_script_config(script_config)
        deploy_config = {
            "instance_name": bot_name,
            "script": "v2_with_controllers.py",
            "script_config": bot_name + ".yml",
            "image": self._image_name,
            "credentials_profile": self._credentials,
        }
        self._backend_api_client.create_hummingbot_instance(deploy_config)
        with st.spinner('Starting Bot... This process may take a few seconds'):
            time.sleep(3)

    def delete_selected_configs(self):
        if self._controller_config_selected:
            for config in self._controller_config_selected:
                response = self._backend_api_client.delete_controller_config(config)
                st.success(response)
            self._controller_configs_available = self._backend_api_client.get_all_controllers_config()
        else:
            st.warning("You need to select the controllers configs that you want to delete.")

    def __call__(self):
        with mui.Paper(key=self._key,
                       sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"},
                       elevation=1):
            with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                mui.Typography("🎛️ Bot Configuration", variant="h5")

            with mui.Grid(container=True, spacing=2, sx={"padding": "10px 15px 10px 15px"}):
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
                    available_credentials = self._backend_api_client.get_accounts()
                    with mui.FormControl(variant="standard", sx={"width": "100%"}):
                        mui.FormHelperText("Credentials")
                        with mui.Select(label="Credentials", defaultValue="master_account",
                                        variant="standard", onChange=lazy(self._set_credentials)):
                            for master_config in available_credentials:
                                mui.MenuItem(master_config, value=master_config)
                all_controllers_config = self._backend_api_client.get_all_controllers_config()
                data = []
                for config in all_controllers_config:
                    connector_name = config.get("connector_name", "Unknown")
                    trading_pair = config.get("trading_pair", "Unknown")
                    total_amount_quote = config.get("total_amount_quote", 0)
                    stop_loss = config.get("stop_loss", 0)
                    take_profit = config.get("take_profit", 0)
                    trailing_stop = config.get("trailing_stop", {"activation_price": 0, "trailing_delta": 0})
                    time_limit = config.get("time_limit", 0)
                    config_version = config["id"].split("_")
                    if len(config_version) > 1:
                        config_base = config_version[0]
                        version = config_version[1]
                    else:
                        config_base = config["id"]
                        version = "NaN"
                    ts_text = str(trailing_stop["activation_price"]) + " / " + str(trailing_stop["trailing_delta"])
                    data.append({
                        "id": config["id"], "config_base": config_base, "version": version,
                        "controller_name": config["controller_name"], "controller_type": config["controller_type"],
                        "connector_name": connector_name, "trading_pair": trading_pair,
                        "total_amount_quote": total_amount_quote, "max_loss_quote": total_amount_quote * stop_loss / 2,
                        "stop_loss": stop_loss, "take_profit": take_profit,
                        "trailing_stop": ts_text,
                        "time_limit": time_limit})

                with mui.Grid(item=True, xs=12):
                    with mui.Paper(key=self._key,
                                   sx={"display": "flex", "flexDirection": "column", "borderRadius": 3,
                                       "overflow": "hidden", "height": 1000},
                                   elevation=2):
                        with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                            with mui.Grid(container=True, spacing=2):
                                with mui.Grid(item=True, xs=8):
                                    mui.Typography("🗄️ Available Configurations", variant="h6")
                                with mui.Grid(item=True, xs=2):
                                    with mui.Button(onClick=self.delete_selected_configs,
                                                    variant="outlined",
                                                    color="error",
                                                    sx={"width": "100%", "height": "100%"}):
                                        mui.icon.Delete()
                                        mui.Typography("Delete")
                                with mui.Grid(item=True, xs=2):
                                    with mui.Button(onClick=self.launch_new_bot,
                                                    variant="outlined",
                                                    color="success",
                                                    sx={"width": "100%", "height": "100%"}):
                                        mui.icon.AddCircleOutline()
                                        mui.Typography("Launch Bot")
                        with mui.Box(sx={"flex": 1, "minHeight": 3, "width": "100%"}):
                            mui.DataGrid(
                                columns=self.DEFAULT_COLUMNS,
                                rows=data,
                                pageSize=15,
                                rowsPerPageOptions=[15],
                                checkboxSelection=True,
                                disableSelectionOnClick=True,
                                disableColumnResize=False,
                                onSelectionModelChange=self._handle_row_selection,
                            )
