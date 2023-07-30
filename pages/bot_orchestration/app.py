from commlib.exceptions import RPCClientTimeoutError

import constants
import streamlit as st
from streamlit_elements import elements, mui, lazy, sync
import time

from docker_manager import DockerManager
from hbotrc import BotCommands

from ui_components.bot_performance_card import BotPerformanceCard
from ui_components.dashboard import Dashboard
from utils.st_utils import initialize_st_page

initialize_st_page(title="Bot Orchestration", icon="🐙")

if "is_broker_running" not in st.session_state:
    st.session_state.is_broker_running = False

if "active_bots" not in st.session_state:
    st.session_state.active_bots = {}

if "new_bot_name" not in st.session_state:
    st.session_state.new_bot_name = ""


def manage_broker_container():
    if st.session_state.is_broker_running:
        docker_manager.stop_container("hummingbot-broker")
        with st.spinner('Stopping hummingbot broker... You are not going to be able to manage bots anymore.'):
            time.sleep(5)
    else:
        docker_manager.start_container("hummingbot-broker")
        with st.spinner('Starting hummingbot broker... This process may take a few seconds'):
            time.sleep(30)


def launch_new_bot():
    bot_name = f"hummingbot-{st.session_state.new_bot_name.target.value}"
    docker_manager.create_hummingbot_instance(instance_name=bot_name,
                                              base_conf_folder=f"{constants.BOTS_FOLDER}/master_bot_conf/",
                                              target_conf_folder=f"{constants.BOTS_FOLDER}/{bot_name}")


def update_containers_info(docker_manager):
    active_containers = docker_manager.get_active_containers()
    st.session_state.is_broker_running = "hummingbot-broker" in active_containers
    if st.session_state.is_broker_running:
        try:
            active_hbot_containers = [container for container in active_containers if "hummingbot-" in container and "broker" not in container]
            previous_active_bots = st.session_state.active_bots.keys()

            # Remove bots that are no longer active
            for bot in previous_active_bots:
                if bot not in active_hbot_containers:
                    del st.session_state.active_bots[bot]

            # Add new bots
            for bot in active_hbot_containers:
                if bot not in previous_active_bots:
                    st.session_state.active_bots[bot] = {
                        "bot_name": bot,
                        "broker_client": BotCommands(host='localhost', port=1883, username='admin', password='password',
                                                     bot_id=bot)
                    }

            # Update bot info
            for bot in st.session_state.active_bots.keys():
                try:
                    broker_client = st.session_state.active_bots[bot]["broker_client"]
                    status = broker_client.status()
                    history = broker_client.history()
                    is_running = "No strategy is currently running" not in status.msg
                    st.session_state.active_bots[bot]["is_running"] = is_running
                    st.session_state.active_bots[bot]["status"] = status.msg
                    st.session_state.active_bots[bot]["trades"] = history.trades
                    st.session_state.active_bots[bot]["selected_strategy"] = None
                except RPCClientTimeoutError:
                    st.error(f"RPCClientTimeoutError: Could not connect to {bot}. Please review the connection.")
                    del st.session_state.active_bots[bot]
        except RuntimeError:
            st.experimental_rerun()
        st.session_state.active_bots = dict(sorted(st.session_state.active_bots.items(), key=lambda x: x[1]['is_running'], reverse=True))
    else:
        st.session_state.active_bots = {}

docker_manager = DockerManager()

orchestrate, manage = st.tabs(["Orchestrate", "Manage Files"])
update_containers_info(docker_manager)


def get_grid_positions(n_cards: int, cols: int = 3, card_width: int = 4, card_height: int = 3):
    rows = n_cards // cols + 1
    x_y = [(x * card_width, y * card_height) for x in range(cols) for y in range(rows)]
    return sorted(x_y, key=lambda x: (x[1], x[0]))


with orchestrate:
    with elements("create_bot"):
        with mui.Grid(container=True, spacing=4):
            with mui.Grid(item=True, xs=6):
                with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
                    with mui.Grid(container=True, spacing=4):
                        with mui.Grid(item=True, xs=12):
                            mui.Typography("🚀 Set up a new bot", variant="h3")
                        with mui.Grid(item=True, xs=8):
                            mui.TextField(label="Bot Name", variant="outlined", onChange=lazy(sync("new_bot_name")),
                                          sx={"width": "100%"})
                        with mui.Grid(item=True, xs=4):
                            with mui.Button(onClick=launch_new_bot):
                                mui.icon.AddCircleOutline()
                                mui.Typography("Create new bot!")
            with mui.Grid(item=True, xs=6):
                with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
                    with mui.Grid(container=True, spacing=4):
                        with mui.Grid(item=True, xs=12):
                            mui.Typography("🐙 Hummingbot Broker", variant="h3")
                        with mui.Grid(item=True, xs=8):
                            mui.Typography("To control and monitor your bots you need to launch the Hummingbot Broker."
                                           "This component will send the commands to the running bots.")
                        with mui.Grid(item=True, xs=4):
                            button_text = "Stop Broker" if st.session_state.is_broker_running else "Start Broker"
                            color = "error" if st.session_state.is_broker_running else "success"
                            icon = mui.icon.Stop if st.session_state.is_broker_running else mui.icon.PlayCircle
                            with mui.Button(onClick=manage_broker_container, color=color):
                                icon()
                                mui.Typography(button_text)


    if st.session_state.is_broker_running:
        quantity_of_active_bots = len(st.session_state.active_bots)
        if quantity_of_active_bots > 0:
            # TODO: Make layout configurable
            grid_positions = get_grid_positions(n_cards=quantity_of_active_bots, cols=3, card_width=4, card_height=3)
            active_instances_board = Dashboard()
            for (bot, config), (x, y) in zip(st.session_state.active_bots.items(), grid_positions):
                st.session_state.active_bots[bot]["bot_performance_card"] = BotPerformanceCard(active_instances_board,
                                                                                               x, y,
                                                                                               card_width, card_height)

            with elements("active_instances_board"):
                with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
                    mui.Typography("🦅 Hummingbot Instances", variant="h3")
                    with active_instances_board():
                        for bot, config in st.session_state.active_bots.items():
                            st.session_state.active_bots[bot]["bot_performance_card"](config)
            with elements("stopped_instances_board"):
                with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
                    mui.Typography("🦅 Stopped Instances", variant="h3")
                    # with mui.Grid()




with manage:
    with elements("monaco_editors"):
        # Streamlit Elements embeds Monaco code and diff editor that powers Visual Studio Code.
        # You can configure editor's behavior and features with the 'options' parameter.
        #
        # Streamlit Elements uses an unofficial React implementation (GitHub links below for
        # documentation).

        from streamlit_elements import editor

        if "content" not in st.session_state:
            st.session_state.content = "Default value"

        mui.Typography("Content: ", st.session_state.content)


        def update_content(value):
            st.session_state.content = value


        editor.Monaco(
            height=1200,
            defaultValue=st.session_state.content,
            onChange=lazy(update_content),
            defaultLanguage="python"
        )

        mui.Button("Update content", onClick=sync())
