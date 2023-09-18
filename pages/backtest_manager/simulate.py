import time
import webbrowser
from types import SimpleNamespace
from decimal import Decimal

import streamlit as st
from hummingbot.core.data_type.common import TradeType, OrderType, PositionMode
from hummingbot.data_feed.candles_feed.candles_factory import CandlesConfig
from hummingbot.smart_components.strategy_frameworks.data_types import OrderLevel, TripleBarrierConf
from hummingbot.smart_components.strategy_frameworks.directional_trading import DirectionalTradingBacktestingEngine
from streamlit_elements import elements, mui

import constants
from quants_lab.strategy.strategy_analysis import StrategyAnalysis
from utils.enum_encoder import EnumEncoderDecoder
from utils.graphs import BacktestingGraphs
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
controllers = load_controllers(constants.CONTROLLERS_PATH)
controller_to_optimize = st.selectbox("Select strategy to backtest", controllers.keys())
controller = controllers[controller_to_optimize]
field_schema = controller["config"].schema()["properties"]
st.write("## Strategy parameters")
st.write("---")
columns = st.columns(4)
column_index = 0
for field_name, properties in field_schema.items():
    field_type = properties.get("type", "string")
    if field_name not in ["candles_config", "order_levels", "position_mode"]:
        field_value = properties.get("default", "")
        with columns[column_index]:
            if field_type in ["number", "integer"]:
                field_value = st.number_input(field_name,
                                              value=field_value,
                                              min_value=properties.get("minimum"),
                                              max_value=properties.get("maximum"),
                                              key=field_name)
            elif field_type == "string":
                field_value = st.text_input(field_name, value=field_value)
            elif field_type == "boolean":
                # TODO: Add support for boolean fields in optimize tab
                field_value = st.checkbox(field_name, value=field_value)
            else:
                raise ValueError(f"Field type {field_type} not supported")
    else:
        if field_name == "candles_config":
            st.write("### Candles Config:")
            c11, c12, c13, c14 = st.columns(4)
            with c11:
                connector = st.text_input("Connector", value="binance_perpetual")
            with c12:
                trading_pair = st.text_input("Trading pair", value="BTC-USDT")
            with c13:
                interval = st.text_input("Interval", value="3m")
            with c14:
                max_records = st.number_input("Max records", value=100000)
            field_value = [CandlesConfig(connector=connector, trading_pair=trading_pair, interval=interval,
                                         max_records=max_records)]
        elif field_name == "order_levels":
            st.write("### Triple Barrier config:")
            c21, c22, c23, c24, c25 = st.columns(5)
            with c21:
                take_profit = st.number_input("Take profit", value=0.02)
            with c22:
                stop_loss = st.number_input("Stop Loss", value=0.01)
            with c23:
                time_limit = st.number_input("Time Limit", value=60 * 60 * 2)
            with c24:
                ts_ap = st.number_input("Trailing Stop Activation Price", value=0.01)
            with c25:
                ts_td = st.number_input("Trailing Stop Trailing Delta", value=0.005)

            st.write("### Position config:")
            c31, c32 = st.columns(2)
            with c31:
                order_amount = st.number_input("Order amount USD", value=50)
            with c32:
                cooldown_time = st.number_input("Cooldown time", value=15)
            triple_barrier_conf = TripleBarrierConf(stop_loss=Decimal(stop_loss), take_profit=Decimal(take_profit),
                                                    time_limit=time_limit,
                                                    trailing_stop_activation_price_delta=Decimal(ts_ap),
                                                    trailing_stop_trailing_delta=Decimal(ts_td),
                                                    open_order_type=OrderType.MARKET)
            field_value = [
                OrderLevel(level=0, side=TradeType.BUY, order_amount_usd=order_amount, cooldown_time=cooldown_time,
                           triple_barrier_conf=triple_barrier_conf),
                OrderLevel(level=0, side=TradeType.SELL, order_amount_usd=order_amount, cooldown_time=cooldown_time,
                           triple_barrier_conf=triple_barrier_conf),
            ]
        elif field_name == "position_mode":
            field_value = PositionMode.HEDGE
    st.session_state["strategy_params"][field_name] = field_value

    column_index = (column_index + 1) % 4

st.write("### Backtesting period")
col1, col2, col3, col4 = st.columns([1, 1, 1, 0.5])
with col1:
    trade_cost = st.number_input("Trade cost",
                                 value=0.0006,
                                 min_value=0.0001, format="%.4f", )
with col2:
    initial_portfolio_usd = st.number_input("Initial portfolio usd",
                                            value=10000.00,
                                            min_value=1.00,
                                            max_value=999999999.99)
with col3:
    start = st.text_input("Start", value="2023-01-01")
    end = st.text_input("End", value="2023-08-01")
c1, c2 = st.columns([1, 1])
with col4:
    add_positions = st.checkbox("Add positions", value=True)
    add_volume = st.checkbox("Add volume", value=True)
    add_pnl = st.checkbox("Add PnL", value=True)
    save_config = st.button("💾Save controller config!")
    config = controller["config"](**st.session_state["strategy_params"])
    controller = controller["class"](config=config)
    if save_config:
        encoder_decoder = EnumEncoderDecoder(TradeType, OrderType, PositionMode)
        encoder_decoder.yaml_dump(config.dict(),
                                  f"hummingbot_files/controller_configs/{config.strategy_name}_{trial_selected}.yml")
    run_backtesting_button = st.button("⚙️Run Backtesting!")
if run_backtesting_button:
    try:
        engine = DirectionalTradingBacktestingEngine(controller=controller)
        engine.load_controller_data("./data/candles")
        backtesting_results = engine.run_backtesting(initial_portfolio_usd=initial_portfolio_usd,
                                                     trade_cost=trade_cost,
                                                     start=start, end=end)
        strategy_analysis = StrategyAnalysis(
            positions=backtesting_results["executors_df"],
            candles_df=backtesting_results["processed_data"],
        )
        metrics_container = BacktestingGraphs(backtesting_results["processed_data"]).get_trial_metrics(strategy_analysis,
                                                                  add_positions=add_positions,
                                                                  add_volume=add_volume)

    except FileNotFoundError:
        st.warning(f"The requested candles could not be found.")
