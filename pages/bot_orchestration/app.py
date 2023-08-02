from glob import glob
from types import SimpleNamespace

from commlib.exceptions import RPCClientTimeoutError

import constants
import streamlit as st
from streamlit_elements import elements, mui, lazy, sync, event
import time

from docker_manager import DockerManager
from hbotrc import BotCommands

from ui_components.bot_performance_card import BotPerformanceCard
from ui_components.dashboard import Dashboard
from ui_components.editor import Editor
from ui_components.exited_bot_card import ExitedBotCard
from ui_components.file_explorer import FileExplorer
from utils.st_utils import initialize_st_page

initialize_st_page(title="Bot Orchestration", icon="🐙", initial_sidebar_state="collapsed")

if "is_broker_running" not in st.session_state:
    st.session_state.is_broker_running = False

if "active_bots" not in st.session_state:
    st.session_state.active_bots = {}

if "exited_bots" not in st.session_state:
    st.session_state.exited_bots = {}

if "new_bot_name" not in st.session_state:
    st.session_state.new_bot_name = ""

if "selected_strategy" not in st.session_state:
    st.session_state.selected_strategy = None

if "selected_file" not in st.session_state:
    st.session_state.selected_file = ""

if "editor_tabs" not in st.session_state:
    st.session_state.editor_tabs = {}


def manage_broker_container():
    if st.session_state.is_broker_running:
        docker_manager.stop_container("hummingbot-broker")
        with st.spinner('Stopping hummingbot broker... You are not going to be able to manage bots anymore.'):
            time.sleep(5)
    else:
        docker_manager.create_broker()
        with st.spinner('Starting hummingbot broker... This process may take a few seconds'):
            time.sleep(20)


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
            active_hbot_containers = [container for container in active_containers if
                                      "hummingbot-" in container and "broker" not in container]
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
        st.session_state.active_bots = dict(
            sorted(st.session_state.active_bots.items(), key=lambda x: x[1]['is_running'], reverse=True))
    else:
        st.session_state.active_bots = {}


docker_manager = DockerManager()
CARD_WIDTH = 4
CARD_HEIGHT = 3

if not docker_manager.is_docker_running():
    st.warning("Docker is not running. Please start Docker and refresh the page.")
    st.stop()
orchestrate, manage = st.tabs(["Orchestrate", "Manage Files"])
update_containers_info(docker_manager)
exited_containers = [container for container in docker_manager.get_exited_containers() if "broker" not in container]


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

    with elements("active_instances_board"):
        with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
            mui.Typography("🦅 Active Instances", variant="h3")
            if st.session_state.is_broker_running:
                quantity_of_active_bots = len(st.session_state.active_bots)
                if quantity_of_active_bots > 0:
                    # TODO: Make layout configurable
                    grid_positions = get_grid_positions(n_cards=quantity_of_active_bots, cols=3,
                                                        card_width=CARD_WIDTH, card_height=CARD_HEIGHT)
                    active_instances_board = Dashboard()
                    for (bot, config), (x, y) in zip(st.session_state.active_bots.items(), grid_positions):
                        st.session_state.active_bots[bot]["bot_performance_card"] = BotPerformanceCard(active_instances_board,
                                                                                                       x, y,
                                                                                                       CARD_WIDTH, CARD_HEIGHT)
                    with active_instances_board():
                        for bot, config in st.session_state.active_bots.items():
                            st.session_state.active_bots[bot]["bot_performance_card"](config)
                else:
                    mui.Alert("No active bots found. Please create a new bot.", severity="info", sx={"margin": "1rem"})
            else:
                mui.Alert("Please start the Hummingbot Broker to control your bots.", severity="warning", sx={"margin": "1rem"})
    with elements("stopped_instances_board"):
        grid_positions = get_grid_positions(n_cards=len(exited_containers), cols=3, card_width=4, card_height=3)
        exited_instances_board = Dashboard()
        for exited_instance, (x, y) in zip(exited_containers, grid_positions):
            st.session_state.exited_bots[exited_instance] = ExitedBotCard(exited_instances_board, x, y,
                                                                          CARD_WIDTH, 1)
        with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
            mui.Typography("💤 Stopped Instances", variant="h3")
            with exited_instances_board():
                for bot, card in st.session_state.exited_bots.items():
                    card(bot)


with manage:
    if "w" not in st.session_state:
        board = Dashboard()
        w = SimpleNamespace(
            dashboard=board,
            file_explorer=FileExplorer(board, 0, 0, 3, 7),
            editor=Editor(board, 4, 0, 9, 7),
        )
        st.session_state.w = w

    else:
        w = st.session_state.w

    for tab_name, content in st.session_state.editor_tabs.items():
        if tab_name not in w.editor._tabs:
            w.editor.add_tab(tab_name, content["content"], content["language"], content["file_path"])

    with elements("bot_config"):
        with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
            mui.Typography("🗂Files Management", variant="h3", sx={"margin-bottom": "2rem"})
            event.Hotkey("ctrl+s", sync(), bindInputs=True, overrideDefault=True)
            with w.dashboard():
                w.file_explorer()
                w.editor()
