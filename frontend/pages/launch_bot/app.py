from types import SimpleNamespace

import streamlit as st
from streamlit_elements import elements, mui

from frontend.components.dashboard import Dashboard
from frontend.components.launch_strategy_v2 import LaunchStrategyV2
from utils.st_utils import initialize_st_page

CARD_WIDTH = 6
CARD_HEIGHT = 3
NUM_CARD_COLS = 2

initialize_st_page(title="Launch Bot", icon="🙌", initial_sidebar_state="collapsed")


def get_grid_positions(n_cards: int, cols: int = NUM_CARD_COLS, card_width: int = CARD_HEIGHT, card_height: int = CARD_WIDTH):
    rows = n_cards // cols + 1
    x_y = [(x * card_width, y * card_height) for x in range(cols) for y in range(rows)]
    return sorted(x_y, key=lambda x: (x[1], x[0]))


if "launch_bots_board" not in st.session_state:
    board = Dashboard()
    launch_bots_board = SimpleNamespace(
        dashboard=board,
        launch_bot=LaunchStrategyV2(board, 0, 0, 12, 10),
    )
    st.session_state.launch_bots_board = launch_bots_board

else:
    launch_bots_board = st.session_state.launch_bots_board


with elements("create_bot"):
    with mui.Paper(elevation=3, style={"padding": "2rem"}, spacing=[2, 2], container=True):
        with launch_bots_board.dashboard():
            launch_bots_board.launch_bot()
