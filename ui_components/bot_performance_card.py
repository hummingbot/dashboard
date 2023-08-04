from docker_manager import DockerManager
from streamlit_elements import mui, lazy
from ui_components.dashboard import Dashboard
import streamlit as st
import time
from utils.os_utils import get_python_files_from_directory, get_yml_files_from_directory


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
                      sx={"display": "flex", "flexDirection": "column", "borderRadius": 2, "overflow": "hidden"},
                      elevation=2):
            color = "green" if bot_config["is_running"] else "red"
            subheader_message = "Running " + st.session_state.active_bots[bot_name]["selected_strategy"] if bot_config["is_running"] else "Stopped"
            mui.CardHeader(
                title=bot_config["bot_name"],
                subheader=subheader_message,
                avatar=mui.Avatar("🤖", sx={"bgcolor": color}),
                action=mui.IconButton(mui.icon.Stop, onClick=lambda: bot_config["broker_client"].stop()) if bot_config[
                    "is_running"] else mui.IconButton(mui.icon.BuildCircle),
                className=self._draggable_class,
            )
            if bot_config["is_running"]:
                with mui.CardContent(sx={"flex": 1}):
                    with mui.Paper(elevation=2, sx={"padding": 2, "marginBottom": 2}):
                        mui.Typography("Status", variant="h6")
                        mui.Typography(bot_config["status"])
                    with mui.Accordion(sx={"padding": 2, "marginBottom": 2}):
                        with mui.AccordionSummary(expandIcon="▼"):
                            mui.Typography("Trades" + "(" + str(len(bot_config["trades"])) + ")", variant="h6")
                        with mui.AccordionDetails():
                            mui.Typography(str(bot_config["trades"]))
                    mui.Typography("Run the following command in Bash/Terminal to attach to the bot instance:")
                    mui.TextField(disabled=True, value="docker attach " + bot_name, sx={"width": "100%"})

            else:
                with mui.CardContent(sx={"flex": 1}):
                    with mui.Grid(container=True, spacing=2):
                        with mui.Grid(item=True, xs=12):
                            mui.Typography("Select a strategy:")
                        with mui.Grid(item=True, xs=8):
                            with mui.Select(onChange=lazy(lambda x, y: self.set_strategy(x, y, bot_name)),
                                            sx={"width": "100%"}):
                                for script in scripts:
                                    mui.MenuItem(script, value=script)
                                for strategy in strategies:
                                    mui.MenuItem(strategy, value=strategy)
                        with mui.Grid(item=True, xs=4):
                            with mui.Button(onClick=lambda x: self.start_strategy(bot_name, bot_config["broker_client"]), variant="contained", color="success"):
                                mui.icon.PlayCircle()
                                mui.Typography("Start")
            with mui.CardActions():
                with mui.Button(onClick=lambda: DockerManager().stop_container(bot_name), variant="contained", color="error"):
                    mui.icon.DeleteForever()
                    mui.Typography("Stop Instance")
