from docker_manager import DockerManager
from streamlit_elements import mui, lazy
from ui_components.dashboard import Dashboard
import streamlit as st
import time
from utils.os_utils import get_python_files_from_directory, get_yml_files_from_directory

import pandas as pd

def parse_orders(input_str):
    # Check for "No active maker orders" in the string
    if "No active maker orders" in input_str:
        return "No active maker orders"
    
    # Split the string by lines
    lines = input_str.split("\n")

    # Identify the line where the 'Orders:' section starts
    for i, line in enumerate(lines):
        if "Orders:" in line:
            start_idx = i + 1
            break
    
    # Extract relevant lines after "Orders:"
    order_lines = lines[start_idx:]    

    # Determine the table type based on the header and extract order lines
    table_type = None
    for i, line in enumerate(order_lines):
        if all(keyword in line for keyword in ['Exchange', 'Market', 'Side']):
            table_type = 'simple_pmm'
            start_idx = i + 1
            order_lines_parsed = order_lines[start_idx:]
            break
        elif all(keyword in line for keyword in ['Level', 'Amount (Orig)']):
            table_type = 'pmm'
            start_idx = i + 1
            order_lines_parsed = order_lines[start_idx:]
            break
    
    # Parse each order line into a list of dictionaries
    orders = []
    for order_line in order_lines_parsed:
        parts = order_line.split()
        
        # Check table type and extract data accordingly
        if table_type == 'simple_pmm':
            if len(parts) < 5:
                continue
            order = {
                "id": parts[2] + parts[3] + parts[4] + (parts[5] if len(parts) > 5 else ""),
                "Exchange": parts[0],
                "Market": parts[1],
                "Side": parts[2],
                "Price": parts[3],
                "Amount": parts[4],
                "Age": " ".join(parts[5:]) if len(parts) > 5 else None            
            }
            orders.append(order)
        elif table_type == 'pmm':
            if len(parts) < 6:
                continue
            order = {
                "id": parts[0] + parts[1] + parts[2] + parts[3] + parts[4] + (parts[6] if len(parts) > 6 else ""),
                "Level": parts[0],
                "Type": parts[1],
                "Price": parts[2],
                "Spread": parts[3],
                "Amount (Adj)": parts[4],
                "Amount (Orig)": parts[5],
                "Age": " ".join(parts[6:]) if len(parts) > 6 else None 
            }
            orders.append(order)
            
    return orders

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
                    with mui.Paper(elevation=2, sx={"padding": 2, "marginBottom": 2}):
                        mui.Typography("Status")
                        orders = parse_orders(bot_config["status"])
                        # mui.Typography(str(orders), sx={"fontSize": "0.75rem"})
                        # mui.Divider()

                        # Convert list of dictionaries to DataFrame
                        if orders != "No active maker orders":
                            df_orders = pd.DataFrame(orders)
                            rows = df_orders.to_dict(orient='records')
                            columns = [{'field': col, 'headerName': col} for col in df_orders.columns]
                            # rows, columns = df_orders.shape
                            mui.Typography(str(rows), sx={"fontSize": "0.75rem"})
                            mui.Divider()
                            mui.Typography(str(columns), sx={"fontSize": "0.75rem"})
                            mui.Divider()
                            mui.DataGrid(rows=rows, columns=columns)
                        else:
                            mui.Typography(str(orders), sx={"fontSize": "0.75rem"})

                    with mui.Accordion(sx={"padding": 2, "marginBottom": 2}):
                        with mui.AccordionSummary(expandIcon="▼"):
                            mui.Typography("Trades" + "(" + str(len(bot_config["trades"])) + ")")
                        with mui.AccordionDetails():
                            mui.Typography(str(bot_config["trades"]), sx={"fontSize": "0.75rem"})
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
                        mui.TextField(disabled=True,
                                    label="Attach to bot instance",
                                    value="docker attach " + bot_name, 
                                    sx={"width": "100%"})
