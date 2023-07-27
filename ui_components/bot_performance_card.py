from docker_manager import DockerManager
from streamlit_elements import mui, sync, html, lazy, elements
from ui_components.dashboard import Dashboard
import streamlit as st
from utils.os_utils import get_python_files_from_directory, get_yml_files_from_directory


class BotPerformanceCard(Dashboard.Item):

    def __init__(self, board, x, y, w, h, **item_props):
        super().__init__(board, x, y, w, h, **item_props)

    @staticmethod
    def set_strategy(event, bot_name):
        st.session_state.active_bots[bot_name]["selected_strategy"] = event.target.value

    def __call__(self, bot_config: dict):
        if "selected_strategy" not in st.session_state:
            st.session_state.selected_strategy = None
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
                      sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"},
                      elevation=2):
            color = "green" if bot_config["is_running"] else "red"
            start_date = bot_config.get("start_date", "Not Available")
            mui.CardHeader(
                title=bot_config["bot_name"],
                subheader=f"Running since {start_date}",
                avatar=mui.Avatar("🤖", sx={"bgcolor": color}),
                action=mui.IconButton(mui.icon.Stop, onClick=lambda: bot_config["broker_client"].stop()) if bot_config[
                    "is_running"] else mui.IconButton(mui.icon.BuildCircle),
                className=self._draggable_class,
            )
            if bot_config["is_running"]:
                with mui.CardContent(sx={"flex": 1}):
                    mui.Typography("Status:")
                    mui.Typography(bot_config["status"])
                    mui.Typography("Trades:")
                    mui.Typography(str(bot_config["trades"]))

            else:
                with mui.CardContent(sx={"flex": 1}):
                    with mui.Grid(container=True, spacing=2):
                        with mui.Grid(item=True, xs=12):
                            mui.Typography("Select a script or strategy to start the bot with:")
                        with mui.Grid(item=True, xs=8):
                            mui.TextField(label="Script name or config file name",
                                          onChange=lazy(lambda x: self.set_strategy(x, bot_name)))

                        with mui.Grid(item=True, xs=4):
                            with mui.Button(onClick=lambda: bot_config["broker_client"].start(
                                    script=st.session_state.active_bots[bot_name]["selected_strategy"])):
                                mui.icon.PlayCircle()
                                mui.Typography("Start")
                        with mui.Grid(item=True, xs=12):
                            with elements("autocomplete"):
                                mui.Autocomplete(
                                    options=scripts + strategies,
                                    value=st.session_state.active_bots[bot_name]["selected_strategy"],
                                    onChange=lazy(lambda x: self.set_strategy(x, bot_name)),
                                    renderInput=lambda params: mui.TextField(params, label="disableClearable", variant="standard")
                                )

                    # with mui.Select(label="Scripts", onChange=lazy(lambda x: self.set_strategy(x, bot_name))):
                    #     for script in scripts:
                    #         mui.MenuItem(script, value=script)
                with mui.CardActions(disableSpacing=True):
                    with mui.Button(onClick=lambda: DockerManager().stop_container(bot_name)):
                        mui.icon.DeleteForever()
                        mui.Typography("Stop Container")
