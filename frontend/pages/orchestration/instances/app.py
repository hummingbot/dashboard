import time

import streamlit as st
from streamlit_elements import elements, mui
from types import SimpleNamespace

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from frontend.components.bot_performance_card import BotPerformanceCardV2
from frontend.components.dashboard import Dashboard
from backend.services.backend_api_client import BackendAPIClient
from frontend.st_utils import initialize_st_page, get_backend_api_client

# Constants for UI layout
CARD_WIDTH = 12
CARD_HEIGHT = 4
NUM_CARD_COLS = 1

def get_grid_positions(n_cards: int, cols: int = NUM_CARD_COLS, card_width: int = CARD_WIDTH, card_height: int = CARD_HEIGHT):
    rows = n_cards // cols + 1
    x_y = [(x * card_width, y * card_height) for x in range(cols) for y in range(rows)]
    return sorted(x_y, key=lambda x: (x[1], x[0]))


def update_active_bots(api_client):
    active_bots_response = api_client.get_active_bots_status()
    if active_bots_response.get("status") == "success":
        current_active_bots = active_bots_response.get("data")
        stored_bots = {card[1]: card for card in st.session_state.active_instances_board.bot_cards}

        new_bots = set(current_active_bots.keys()) - set(stored_bots.keys())
        removed_bots = set(stored_bots.keys()) - set(current_active_bots.keys())
        for bot in removed_bots:
            st.session_state.active_instances_board.bot_cards = [card for card in st.session_state.active_instances_board.bot_cards if card[1] != bot]
        positions = get_grid_positions(len(current_active_bots), NUM_CARD_COLS, CARD_WIDTH, CARD_HEIGHT)
        for bot, (x, y) in zip(new_bots, positions[:len(new_bots)]):
            card = BotPerformanceCardV2(st.session_state.active_instances_board.dashboard, x, y, CARD_WIDTH, CARD_HEIGHT)
            st.session_state.active_instances_board.bot_cards.append((card, bot))


initialize_st_page(title="Instances", icon="🦅")
api_client = get_backend_api_client()

if not api_client.is_docker_running():
    st.warning("Docker is not running. Please start Docker and refresh the page.")
    st.stop()

if "active_instances_board" not in st.session_state:
    active_bots_response = api_client.get_active_bots_status()
    bot_cards = []
    board = Dashboard()
    st.session_state.active_instances_board = SimpleNamespace(
        dashboard=board,
        bot_cards=bot_cards,
    )
    active_bots = active_bots_response.get("data")
    number_of_bots = len(active_bots)
    if number_of_bots > 0:
        positions = get_grid_positions(number_of_bots, NUM_CARD_COLS, CARD_WIDTH, CARD_HEIGHT)
        for (bot, bot_info), (x, y) in zip(active_bots.items(), positions):
            bot_status = api_client.get_bot_status(bot)
            card = BotPerformanceCardV2(board, x, y, CARD_WIDTH, CARD_HEIGHT)
            st.session_state.active_instances_board.bot_cards.append((card, bot))
else:
    update_active_bots(api_client)

with elements("active_instances_board"):
    with mui.Paper(sx={"padding": "2rem"}, variant="outlined"):
        mui.Typography("🏠 Local Instances", variant="h5")
        for card, bot in st.session_state.active_instances_board.bot_cards:
            with st.session_state.active_instances_board.dashboard():
                card(bot)

while True:
    time.sleep(5)
    st.rerun()