from docker_manager import DockerManager
from streamlit_elements import mui, lazy
from ui_components.dashboard import Dashboard
import streamlit as st
import time
from utils.os_utils import get_python_files_from_directory, get_yml_files_from_directory
from utils.status_parser import StatusParser
import pandas as pd

class BotPerformanceCard(Dashboard.Item):

    def __init__(self, board, x, y, w, h, **item_props):
        super().__init__(board, x, y, w, h, **item_props)

    @staticmethod
    def set_strategy(_, childs, bot_name):
        st.session_state.active_bots[bot_name]["selected_strategy"] = childs.props.value

    @staticmethod
    def start_strategy(bot_name, broker_client):
        selected_strategy = st.session_state.active_bots[bot_name]["selected_strategy"]
        if selected_strategy.endswith(".py"):
            broker_client.start(script=selected_strategy)
        elif selected_strategy.endswith(".yml"):
            broker_client.import_strategy(strategy=selected_strategy.replace(".yml", ""))
            time.sleep(0.5)
            broker_client.start()

    def __call__(self, bot_config: dict):
        bot_name = bot_config["bot_name"]
        scripts_directory = f"./hummingbot_files/bot_configs/{bot_config['bot_name']}"
        strategies_directory = f"{scripts_directory}/conf/strategies"
        scripts = [file.split("/")[-1] for file in get_python_files_from_directory(scripts_directory)]
        strategies = [file.split("/")[-1] for file in get_yml_files_from_directory(strategies_directory)]
        if bot_config["selected_strategy"] is None:
            if len(scripts):
                st.session_state.active_bots[bot_name]["selected_strategy"] = scripts[0]
            elif len(strategies):
                st.session_state.active_bots[bot_name]["selected_strategy"] = strategies[0]

        with mui.Card(key=self._key,
                      sx={"display": "flex", "flexDirection": "column", "borderRadius": 2, "overflow": "auto"},
                      elevation=2):
            color = "green" if bot_config["is_running"] else "grey"
            subheader_message = "Running " + st.session_state.active_bots[bot_name]["selected_strategy"] if bot_config["is_running"] else "Not running"
            mui.CardHeader(
                title=bot_config["bot_name"],
                subheader=subheader_message,
                avatar=mui.Avatar("🤖", sx={"bgcolor": color}),
                # action=mui.IconButton(mui.icon.Stop, onClick=lambda: bot_config["broker_client"].stop()) if bot_config[
                #     "is_running"] else mui.IconButton(mui.icon.BuildCircle),
                className=self._draggable_class,
            )
            if bot_config["is_running"]:
                with mui.CardContent(sx={"flex": 1}):
                    
                    # Balances Table
                    mui.Typography("Balances", variant="h6")

                    # # Convert list of dictionaries to DataFrame
                    balances = StatusParser(bot_config["status"], type="balances").parse()
                    if balances != "No balances":
                        df_balances = pd.DataFrame(balances)
                        balances_rows = df_balances.to_dict(orient='records')
                        balances_cols = [{'field': col, 'headerName': col} for col in df_balances.columns]

                        for column in balances_cols:
                            # Hide the 'id' column
                            if column['field'] == 'id':
                                column['width'] = 0
                            else:
                                column['width'] = 200

                        mui.DataGrid(rows=balances_rows,
                                        columns=balances_cols,
                                        autoHeight=True,
                                        density="compact",
                                        disableColumnSelector=True,
                                        hideFooter=True,
                                        initialState={"columns": {"columnVisibilityModel": {"id": False}}})
                    else:
                        mui.Typography(str(balances), sx={"fontSize": "0.75rem"})
                    
                    mui.Divider(sx={"margin": 4})

                    # Active Orders Table
                    mui.Typography("Active Orders", variant="h6")

                    # Convert list of dictionaries to DataFrame
                    orders = StatusParser(bot_config["status"], type="orders").parse()
                    if orders != "No active maker orders" or "No matching string":
                        df_orders = pd.DataFrame(orders)
                        orders_rows = df_orders.to_dict(orient='records')
                        orders_cols = [{'field': col, 'headerName': col} for col in df_orders.columns]

                        for column in orders_cols:
                            # Hide the 'id' column
                            if column['field'] == 'id':
                                column['width'] = 0
                            # Expand the 'exchange' column
                            if column['field'] == 'Exchange':
                                column['width'] = 200
                            # Expand the 'price' column
                            if column['field'] == 'Price':
                                column['width'] = 150

                        mui.DataGrid(rows=orders_rows,
                                        columns=orders_cols,
                                        autoHeight=True,
                                        density="compact",
                                        disableColumnSelector=True,
                                        hideFooter=True,
                                        initialState={"columns": {"columnVisibilityModel": {"id": False}}})
                    else:
                        mui.Typography(str(orders), sx={"fontSize": "0.75rem"})

                    mui.Divider(sx={"margin": 4})

                    # Trades Table
                    mui.Typography("Trades", variant="h6")
                    df_trades = pd.DataFrame(bot_config["trades"])

                    # Add 'id' column to the dataframe by concatenating 'trade_id' and 'trade_timestamp'
                    df_trades['id'] = df_trades['trade_id'].astype(str) + df_trades['trade_timestamp'].astype(str)

                    trades_rows = df_trades.to_dict(orient='records')
                    trades_cols = [{'field': col, 'headerName': col} for col in df_trades.columns]

                    for column in trades_cols:
                        # Hide the 'id' and 'raw_json' columns
                        if column['field'] == 'id':
                            column['width'] = 0
                        # Expand the 'exchange' column
                        # if column['field'] == 'Exchange':
                        #     column['width'] = 200

                    mui.DataGrid(rows=trades_rows,
                                    columns=trades_cols,
                                    autoHeight=True,
                                    density="compact",
                                    disableColumnSelector=True,
                                    hideFooter=True,
                                    initialState={"columns": {"columnVisibilityModel": {"id": False}}})
            else:
                with mui.CardContent(sx={"flex": 1}):
                    with mui.Grid(container=True, spacing=2):
                        with mui.Grid(item=True, xs=12):
                            mui.Typography("Select a strategy config file (.yml) or script (.py) to run:")
                        with mui.Grid(item=True, xs=8):
                            with mui.Select(onChange=lazy(lambda x, y: self.set_strategy(x, y, bot_name)),
                                            sx={"width": "100%"}):
                                for strategy in strategies:
                                    mui.MenuItem(strategy, value=strategy, divider=True, sx={"fontWeight": "bold"})
                                for script in scripts:
                                    mui.MenuItem(script, value=script)
                        with mui.Grid(item=True, xs=4):
                            with mui.Button(onClick=lambda x: self.start_strategy(bot_name, bot_config["broker_client"]), 
                                            variant="outlined",
                                            color="success",
                                            sx={"width": "100%", "height": "100%"}):
                                mui.icon.PlayCircle()
                                mui.Typography("Start")
            with mui.CardActions():
                with mui.Grid(container=True, spacing=2):
                    with mui.Grid(item=True, xs=6):
                        with mui.Button(onClick=lambda: DockerManager().stop_container(bot_name), 
                                        variant="outlined", 
                                        color="error",
                                        sx={"width": "100%", "height": "100%"}):
                            mui.icon.DeleteForever()
                            mui.Typography("Stop Instance")
                    with mui.Grid(item=True, xs=6):
                        mui.TextField(InputProps={"readOnly": True},
                                    label="Attach to instance",
                                    value="docker attach " + bot_name, 
                                    sx={"width": "100%"})
