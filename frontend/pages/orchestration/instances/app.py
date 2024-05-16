import streamlit as st
from streamlit_elements import elements, mui

from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from frontend.components.bot_performance_card import BotPerformanceCardV2
from frontend.components.dashboard import Dashboard
from backend.services.backend_api_client import BackendAPIClient
from frontend.st_utils import initialize_st_page

# Constants for UI layout
CARD_WIDTH = 12
CARD_HEIGHT = 3
NUM_CARD_COLS = 1


def get_grid_positions(n_cards: int, cols: int = NUM_CARD_COLS, card_width: int = CARD_HEIGHT, card_height: int = CARD_WIDTH):
    rows = n_cards // cols + 1
    x_y = [(x * card_width, y * card_height) for x in range(cols) for y in range(rows)]
    return sorted(x_y, key=lambda x: (x[1], x[0]))


initialize_st_page(title="Instances", icon="🦅")
api_client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)


if not api_client.is_docker_running():
    st.warning("Docker is not running. Please start Docker and refresh the page.")
    st.stop()


active_bots_response = api_client.get_active_bots_status()
if active_bots_response.get("status") == "success":
    with elements("active_instances_board"):
        with mui.Paper(sx={"padding": "2rem"}, variant="outlined"):
            mui.Typography("🦅 Active Instances", variant="h5")
            active_bots = active_bots_response.get("data")
            if active_bots:
                positions = get_grid_positions(len(active_bots), NUM_CARD_COLS, CARD_WIDTH, CARD_HEIGHT)
                active_instances_board = Dashboard()
                for (bot, bot_info), (x, y) in zip(active_bots.items(), positions):
                    card = BotPerformanceCardV2(active_instances_board, x, y, CARD_WIDTH, CARD_HEIGHT)
                    with active_instances_board():
                        card(bot_info)
            else:
                mui.Alert("No active bots found. Please create a new bot.", severity="info", sx={"margin": "1rem"})





