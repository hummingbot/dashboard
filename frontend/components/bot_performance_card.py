from streamlit_elements import mui

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from frontend.components.dashboard import Dashboard

from backend.services.backend_api_client import BackendAPIClient

TRADES_TO_SHOW = 5
WIDE_COL_WIDTH = 250
MEDIUM_COL_WIDTH = 170
SMALL_COL_WIDTH = 100
backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)


def stop_bot(bot_name):
    backend_api_client.stop_bot(bot_name)


def archive_bot(bot_name):
    backend_api_client.stop_container(bot_name)
    backend_api_client.remove_container(bot_name)



class BotPerformanceCardV2(Dashboard.Item):
    DEFAULT_COLUMNS = [
        {"field": 'id', "headerName": 'ID', "width": WIDE_COL_WIDTH},
        {"field": 'realized_pnl_quote', "headerName": 'Realized PNL ($)', "width": MEDIUM_COL_WIDTH, "editable": False},
        {"field": 'unrealized_pnl_quote', "headerName": 'Unrealized PNL ($)', "width": MEDIUM_COL_WIDTH, "editable": False},
        {"field": 'global_pnl_quote', "headerName": 'NET PNL ($)', "width": MEDIUM_COL_WIDTH, "editable": False},
        {"field": 'volume_traded', "headerName": 'Volume ($)', "width": MEDIUM_COL_WIDTH, "editable": False},
        {"field": 'open_order_volume', "headerName": 'Open Order Volume ($)', "width": MEDIUM_COL_WIDTH, "editable": False},
        {"field": 'imbalance', "headerName": 'Imbalance ($)', "width": MEDIUM_COL_WIDTH, "editable": False},
    ]
    _active_controller_config_selected = []
    _stopped_controller_config_selected = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._backend_api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)

    def _handle_stopped_row_selection(self, params, _):
        self._stopped_controller_config_selected = params

    def _handle_active_row_selection(self, params, _):
        self._active_controller_config_selected = params

    def stop_controllers(self, bot_name):
        for controller in self._active_controller_config_selected:
            self._backend_api_client.stop_controller_from_bot(bot_name, controller)

    def start_controllers(self, bot_name):
        for controller in self._stopped_controller_config_selected:
            self._backend_api_client.start_controller_from_bot(bot_name, controller)

    def __call__(self, bot_name: str):
        try:
            controller_configs = backend_api_client.get_all_configs_from_bot(bot_name)
            bot_status = backend_api_client.get_bot_status(bot_name)
            is_running = False
            if len(bot_status) > 0:
                # Controllers Table
                active_controllers_list = []
                stopped_controllers_list = []
                total_global_pnl_quote = 0
                total_volume_traded = 0
                total_open_order_volume = 0
                total_imbalance = 0
                total_unrealized_pnl_quote = 0
                for controller, inner_dict in bot_status.items():
                    controller_config = next((config for config in controller_configs if config.get("id") == controller),
                                             {})
                    kill_switch_status = True if controller_config.get("manual_kill_switch") is True else False
                    realized_pnl_quote = inner_dict.get("realized_pnl_quote", 0)
                    unrealized_pnl_quote = inner_dict.get("unrealized_pnl_quote", 0)
                    global_pnl_quote = inner_dict.get("global_pnl_quote", 0)
                    volume_traded = inner_dict.get("volume_traded", 0)
                    open_order_volume = inner_dict.get("open_order_volume", 0)
                    imbalance = inner_dict.get("imbalance", 0)
                    controller_info = {
                        "id": controller,
                        "realized_pnl_quote": realized_pnl_quote,
                        "unrealized_pnl_quote": unrealized_pnl_quote,
                        "global_pnl_quote": global_pnl_quote,
                        "volume_traded": volume_traded,
                        "open_order_volume": open_order_volume,
                        "imbalance": imbalance,
                    }
                    if any([value != 0 for value in controller_info.values() if value != controller_info["id"]]):
                        is_running = True
                    if kill_switch_status:
                        stopped_controllers_list.append(controller_info)
                    else:
                        active_controllers_list.append(controller_info)
                    total_global_pnl_quote += global_pnl_quote
                    total_volume_traded += volume_traded
                    total_open_order_volume += open_order_volume
                    total_imbalance += imbalance
                    total_unrealized_pnl_quote += unrealized_pnl_quote
                total_global_pnl_pct = total_global_pnl_quote / total_volume_traded if total_volume_traded > 0 else 0

            if is_running:
                status = "Running"
                color = "green"
            else:
                status = "Stopped"
                color = "red"

            with mui.Card(key=self._key,
                          sx={"display": "flex", "flexDirection": "column", "borderRadius": 2, "overflow": "auto"},
                          elevation=2):
                mui.CardHeader(
                    title=bot_name,
                    subheader=status,
                    avatar=mui.Avatar("🤖", sx={"bgcolor": color}),
                    action=mui.IconButton(mui.icon.Stop, onClick=lambda: stop_bot(bot_name)) if is_running else mui.IconButton(mui.icon.Archive, onClick=lambda: archive_bot(bot_name)),
                    className=self._draggable_class)
                if is_running:
                    with mui.CardContent(sx={"flex": 1}):
                        with mui.Grid(container=True, spacing=2, sx={"padding": "10px 15px 10px 15px"}):
                            with mui.Grid(item=True, xs=2):
                                with mui.Paper(key=self._key,
                                               sx={"display": "flex", "flexDirection": "column", "borderRadius": 3,
                                                   "overflow": "hidden"},
                                               elevation=1):
                                    with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                                        mui.Typography("🏦 NET PNL", variant="h6")
                                    mui.Typography(f"$ {total_global_pnl_quote:.2f}", variant="h6", sx={"padding": "10px 15px 10px 15px"})
                            with mui.Grid(item=True, xs=2):
                                with mui.Paper(key=self._key,
                                               sx={"display": "flex", "flexDirection": "column", "borderRadius": 3,
                                                   "overflow": "hidden"},
                                               elevation=1):
                                    with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                                        mui.Typography("📊 NET PNL (%)", variant="h6")
                                    mui.Typography(f"{total_global_pnl_pct:.2%}", variant="h6", sx={"padding": "10px 15px 10px 15px"})
                            with mui.Grid(item=True, xs=2):
                                with mui.Paper(key=self._key,
                                               sx={"display": "flex", "flexDirection": "column", "borderRadius": 3,
                                                   "overflow": "hidden"},
                                               elevation=1):
                                    with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                                        mui.Typography("💸 Volume Traded", variant="h6")
                                    mui.Typography(f"$ {total_volume_traded:.2f}", variant="h6", sx={"padding": "10px 15px 10px 15px"})
                            with mui.Grid(item=True, xs=2):
                                with mui.Paper(key=self._key,
                                               sx={"display": "flex", "flexDirection": "column", "borderRadius": 3,
                                                   "overflow": "hidden"},
                                               elevation=1):
                                    with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                                        mui.Typography("📖 Liquidity Placed", variant="h6")
                                    mui.Typography(f"$ {total_open_order_volume:.2f}", variant="h6", sx={"padding": "10px 15px 10px 15px"})
                            with mui.Grid(item=True, xs=2):
                                with mui.Paper(key=self._key,
                                               sx={"display": "flex", "flexDirection": "column", "borderRadius": 3,
                                                   "overflow": "hidden"},
                                               elevation=1):
                                    with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                                        mui.Typography("💹 Unrealized PNL", variant="h6")
                                    mui.Typography(f"$ {total_unrealized_pnl_quote:.2f}", variant="h6", sx={"padding": "10px 15px 10px 15px"})
                            with mui.Grid(item=True, xs=2):
                                with mui.Paper(key=self._key,
                                               sx={"display": "flex", "flexDirection": "column", "borderRadius": 3,
                                                   "overflow": "hidden"},
                                               elevation=1):
                                    with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                                        mui.Typography("📊 Imbalance", variant="h6")
                                    mui.Typography(f"$ {total_imbalance:.2f}", variant="h6", sx={"padding": "10px 15px 10px 15px"})

                        with mui.Grid(container=True, spacing=1, sx={"padding": "10px 15px 10px 15px"}):
                            with mui.Grid(item=True, xs=11):
                                with mui.Paper(key=self._key,
                                               sx={"display": "flex", "flexDirection": "column", "borderRadius": 3,
                                                   "overflow": "hidden"},
                                               elevation=1):
                                    with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                                        mui.Typography("🚀 Active Controllers", variant="h6")
                                    mui.DataGrid(
                                        rows=active_controllers_list,
                                        columns=self.DEFAULT_COLUMNS,
                                        autoHeight=True,
                                        density="compact",
                                        checkboxSelection=True,
                                        disableSelectionOnClick=True,
                                        onSelectionModelChange=self._handle_active_row_selection,
                                        hideFooter=True
                                    )
                            with mui.Grid(item=True, xs=1):
                                with mui.Button(onClick=lambda x: self.stop_controllers(bot_name),
                                                variant="outlined",
                                                color="warning",
                                                sx={"width": "100%", "height": "100%"}):
                                    mui.icon.AddCircleOutline()
                                    mui.Typography("Stop")
                        with mui.Grid(container=True, spacing=1, sx={"padding": "10px 15px 10px 15px"}):
                            with mui.Grid(item=True, xs=11):
                                with mui.Paper(key=self._key,
                                               sx={"display": "flex", "flexDirection": "column", "borderRadius": 3,
                                                   "overflow": "hidden"},
                                               elevation=1):
                                    with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                                        mui.Typography("💤 Stopped Controllers", variant="h6")
                                    mui.DataGrid(
                                        rows=stopped_controllers_list,
                                        columns=self.DEFAULT_COLUMNS,
                                        autoHeight=True,
                                        density="compact",
                                        checkboxSelection=True,
                                        disableSelectionOnClick=True,
                                        onSelectionModelChange=self._handle_stopped_row_selection,
                                        hideFooter=True
                                    )
                            with mui.Grid(item=True, xs=1):
                                with mui.Button(onClick=lambda x: self.start_controllers(bot_name),
                                                variant="outlined",
                                                color="success",
                                                sx={"width": "100%", "height": "100%"}):
                                    mui.icon.AddCircleOutline()
                                    mui.Typography("Start")
        except Exception as e:
            print(e)
            with mui.Card(key=self._key,
                          sx={"display": "flex", "flexDirection": "column", "borderRadius": 2, "overflow": "auto"},
                          elevation=2):
                mui.CardHeader(
                    title=bot_name,
                    subheader="Error",
                    avatar=mui.Avatar("🤖", sx={"bgcolor": "red"}),
                    action=mui.IconButton(mui.icon.Stop, onClick=lambda: stop_bot(bot_name)),
                    className=self._draggable_class)
                with mui.CardContent(sx={"flex": 1}):
                    mui.Typography("An error occurred while fetching bot status.", sx={"padding": "10px 15px 10px 15px"})
                    mui.Typography(str(e), sx={"padding": "10px 15px 10px 15px"})
