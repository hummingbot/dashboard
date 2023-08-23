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
from ui_components.exited_bot_card import ExitedBotCard
from ui_components.launch_bot_card import LaunchBotCard
from ui_components.launch_broker_card import LaunchBrokerCard
from utils.st_utils import initialize_st_page

initialize_st_page(title="Bots Manager", icon="🦅", initial_sidebar_state="collapsed")

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

if "editor_tabs" not in st.session_state:
    st.session_state.editor_tabs = {}


def update_containers_info(docker_manager):
    active_containers = docker_manager.get_active_containers()
    st.session_state.is_broker_running = "hummingbot-broker" in active_containers
    if st.session_state.is_broker_running:
        try:
            active_hbot_containers = [container for container in active_containers if
                                      "hummingbot-" in container and "broker" not in container
                                      and "master_bot_conf" not in container]
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
CARD_WIDTH = 6
CARD_HEIGHT = 3
NUM_CARD_COLS = 2

if not docker_manager.is_docker_running():
    st.warning("Docker is not running. Please start Docker and refresh the page.")
    st.stop()
update_containers_info(docker_manager)
exited_containers = [container for container in docker_manager.get_exited_containers() if "broker" not in container]


def get_grid_positions(n_cards: int, cols: int = NUM_CARD_COLS, card_width: int = CARD_HEIGHT, card_height: int = CARD_WIDTH):
    rows = n_cards // cols + 1
    x_y = [(x * card_width, y * card_height) for x in range(cols) for y in range(rows)]
    return sorted(x_y, key=lambda x: (x[1], x[0]))


if "create_containers_board" not in st.session_state:
    board = Dashboard()
    create_containers_board = SimpleNamespace(
        dashboard=board,
        launch_bot=LaunchBotCard(board, 0, 0, 8, 1.5),
        launch_broker=LaunchBrokerCard(board, 8, 0, 4, 1.5)
    )
    st.session_state.create_containers_board = create_containers_board

else:
    create_containers_board = st.session_state.create_containers_board


with elements("create_bot"):
    with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
        with create_containers_board.dashboard():
            create_containers_board.launch_bot()
            create_containers_board.launch_broker()


with elements("active_instances_board"):
    with mui.Paper(sx={"padding": "2rem"}, variant="outlined"):
        mui.Typography("🦅 Active Instances", variant="h5")
        if st.session_state.is_broker_running:
            quantity_of_active_bots = len(st.session_state.active_bots)
            if quantity_of_active_bots > 0:
                # TODO: Make layout configurable
                grid_positions = get_grid_positions(n_cards=quantity_of_active_bots, cols=NUM_CARD_COLS,
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
            mui.Alert("Please start Hummingbot Broker to control your bots.", severity="warning", sx={"margin": "1rem"})
with elements("stopped_instances_board"):
    grid_positions = get_grid_positions(n_cards=len(exited_containers), cols=NUM_CARD_COLS, card_width=CARD_WIDTH, card_height=CARD_HEIGHT)
    exited_instances_board = Dashboard()
    for exited_instance, (x, y) in zip(exited_containers, grid_positions):
        st.session_state.exited_bots[exited_instance] = ExitedBotCard(exited_instances_board, x, y,
                                                                        CARD_WIDTH, 1)
    with mui.Paper(style={"padding": "2rem"}, variant="outlined"):
        mui.Typography("💤 Stopped Instances", variant="h5")
        with exited_instances_board():
            for bot, card in st.session_state.exited_bots.items():
                card(bot)
