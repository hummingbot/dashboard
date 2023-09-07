import time
import webbrowser
from types import SimpleNamespace

import streamlit as st
from streamlit_elements import elements, mui

import constants
from quants_lab.strategy.strategy_analysis import StrategyAnalysis
from utils.os_utils import load_controllers

from utils.st_utils import initialize_st_page


initialize_st_page(title="Simulate", icon="📈", initial_sidebar_state="collapsed")

# Start content here
if "strategy_params" not in st.session_state:
    st.session_state.strategy_params = {}


# TODO:
#    * Add videos explaining how to the triple barrier method works and how the backtesting is designed,
#  link to video of how to create a strategy, etc in a toggle.
#    * Add performance analysis graphs of the backtesting run
strategies = load_controllers(constants.DIRECTIONAL_STRATEGIES_PATH)
strategy_to_optimize = st.selectbox("Select strategy to backtest", strategies.keys())
strategy = strategies[strategy_to_optimize]
strategy_config = strategy["config"]
field_schema = strategy_config.schema()["properties"]
st.write("## Strategy parameters")
c1, c2 = st.columns([5, 1])
with c1:
    columns = st.columns(4)
    column_index = 0
    for field_name, properties in field_schema.items():
        field_type = properties["type"]
        with columns[column_index]:
            if field_type in ["number", "integer"]:
                field_value = st.number_input(field_name,
                                              value=properties["default"],
                                              min_value=properties.get("minimum"),
                                              max_value=properties.get("maximum"),
                                              key=field_name)
            elif field_type == "string":
                field_value = st.text_input(field_name, value=properties["default"])
            elif field_type == "boolean":
                # TODO: Add support for boolean fields in optimize tab
                field_value = st.checkbox(field_name, value=properties["default"])
            else:
                raise ValueError(f"Field type {field_type} not supported")
            st.session_state["strategy_params"][field_name] = field_value
        column_index = (column_index + 1) % 4
with c2:
    add_positions = st.checkbox("Add positions", value=True)
    add_volume = st.checkbox("Add volume", value=True)
    add_pnl = st.checkbox("Add PnL", value=True)

    run_backtesting_button = st.button("Run Backtesting!")
if run_backtesting_button:
    config = strategy["config"](**st.session_state["strategy_params"])
    strategy = strategy["class"](config=config)
    # TODO: add form for order amount, leverage, tp, sl, etc.

    market_data, positions = strategy.run_backtesting(
        start='2021-04-01',
        order_amount=50,
        leverage=20,
        initial_portfolio=100,
        take_profit_multiplier=2.3,
        stop_loss_multiplier=1.2,
        time_limit=60 * 60 * 3,
        std_span=None,
    )
    strategy_analysis = StrategyAnalysis(
        positions=positions,
        candles_df=market_data,
    )
    st.text(strategy_analysis.text_report())
    # TODO: check why the pnl is not being plotted
    strategy_analysis.create_base_figure(volume=add_volume, positions=add_positions, trade_pnl=add_pnl)
    st.plotly_chart(strategy_analysis.figure(), use_container_width=True)
