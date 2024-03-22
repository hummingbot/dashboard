from hummingbot.core.data_type.common import PositionMode, TradeType, OrderType
from hummingbot.data_feed.candles_feed.candles_factory import CandlesConfig
from hummingbot.smart_components.strategy_frameworks.data_types import OrderLevel, TripleBarrierConf
from hummingbot.smart_components.strategy_frameworks.directional_trading import DirectionalTradingBacktestingEngine
from hummingbot.smart_components.utils.config_encoder_decoder import ConfigEncoderDecoder

import constants
import os
import json
import streamlit as st
from decimal import Decimal

from quants_lab.strategy.strategy_analysis import StrategyAnalysis
from data_viz.backtesting.backtesting_charts import BacktestingCharts
from data_viz.backtesting.backtesting_candles import BacktestingCandles
import data_viz.utils as utils
from utils.optuna_database_manager import OptunaDBManager
from utils.os_utils import load_controllers
from utils.st_utils import initialize_st_page


initialize_st_page(title="Analyze", icon="🔬", initial_sidebar_state="collapsed")

BASE_DATA_DIR = "data/backtesting"


@st.cache_resource
def get_databases():
    sqlite_files = [db_name for db_name in os.listdir(BASE_DATA_DIR) if db_name.endswith(".db")]
    databases_list = [OptunaDBManager(db, db_root_path=BASE_DATA_DIR) for db in sqlite_files]
    databases_dict = {database.db_name: database for database in databases_list}
    return [x.db_name for x in databases_dict.values() if x.status == 'OK']


def initialize_session_state_vars():
    if "strategy_params" not in st.session_state:
        st.session_state.strategy_params = {}
    if "backtesting_params" not in st.session_state:
        st.session_state.backtesting_params = {}


initialize_session_state_vars()
dbs = get_databases()
if not dbs:
    st.warning("We couldn't find any Optuna database.")
    selected_db_name = None
    selected_db = None
else:
    # Select database from selectbox
    selected_db = st.selectbox("Select your database:", dbs)
    # Instantiate database manager
    opt_db = OptunaDBManager(selected_db, db_root_path=BASE_DATA_DIR)
    # Load studies
    studies = opt_db.load_studies()
    # Choose study
    study_selected = st.selectbox("Select a study:", studies.keys())
    # Filter trials from selected study
    merged_df = opt_db.merged_df[opt_db.merged_df["study_name"] == study_selected]
    filters_column, scatter_column = st.columns([1, 6])
    with filters_column:
        accuracy = st.slider("Accuracy", min_value=0.0, max_value=1.0, value=[0.4, 1.0], step=0.01)
        net_profit = st.slider("Net PNL (%)", min_value=merged_df["net_pnl_pct"].min(), max_value=merged_df["net_pnl_pct"].max(),
                               value=[merged_df["net_pnl_pct"].min(), merged_df["net_pnl_pct"].max()], step=0.01)
        max_drawdown = st.slider("Max Drawdown (%)", min_value=merged_df["max_drawdown_pct"].min(), max_value=merged_df["max_drawdown_pct"].max(),
                                 value=[merged_df["max_drawdown_pct"].min(), merged_df["max_drawdown_pct"].max()], step=0.01)
        total_positions = st.slider("Total Positions", min_value=merged_df["total_positions"].min(), max_value=merged_df["total_positions"].max(),
                                    value=[merged_df["total_positions"].min(), merged_df["total_positions"].max()], step=1)
        net_profit_filter = (merged_df["net_pnl_pct"] >= net_profit[0]) & (merged_df["net_pnl_pct"] <= net_profit[1])
        accuracy_filter = (merged_df["accuracy"] >= accuracy[0]) & (merged_df["accuracy"] <= accuracy[1])
        max_drawdown_filter = (merged_df["max_drawdown_pct"] >= max_drawdown[0]) & (merged_df["max_drawdown_pct"] <= max_drawdown[1])
        total_positions_filter = (merged_df["total_positions"] >= total_positions[0]) & (merged_df["total_positions"] <= total_positions[1])
    with scatter_column:
        # Show and compare all the study trials
        bt_main_charts = BacktestingCharts()
        st.plotly_chart(bt_main_charts.pnl_vs_max_drawdown_fig(data=merged_df[net_profit_filter & accuracy_filter & max_drawdown_filter & total_positions_filter]), use_container_width=True)
    # Get study trials
    trials = studies[study_selected]
    # Choose trial
    trial_selected = st.selectbox("Select a trial to backtest", list(trials.keys()))
    trial = trials[trial_selected]
    # Transform trial config in a dictionary
    encoder_decoder = ConfigEncoderDecoder(TradeType, OrderType, PositionMode)
    trial_config = encoder_decoder.decode(json.loads(trial["config"]))

    # Strategy parameters section
    st.write("## Strategy parameters")
    # Load strategies (class, config, module)
    controllers = load_controllers(constants.CONTROLLERS_PATH)
    # Select strategy
    controller = controllers[trial_config["strategy_name"]]
    # Get field schema
    field_schema = controller["config"].schema()["properties"]

    columns = st.columns(4)
    column_index = 0
    for field_name, properties in field_schema.items():
        field_type = properties.get("type", "string")
        field_value = trial_config[field_name]
        if field_name not in ["candles_config", "order_levels", "position_mode"]:
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
                st.write("---")
                st.write(f"## Candles Config:")
                candles = []
                for i, candles_config in enumerate(field_value):
                    st.write(f"#### Candle {i}:")
                    c11, c12, c13, c14 = st.columns(4)
                    with c11:
                        connector = st.text_input("Connector", value=candles_config["connector"])
                    with c12:
                        trading_pair = st.text_input("Trading pair", value=candles_config["trading_pair"])
                    with c13:
                        interval = st.text_input("Interval", value=candles_config["interval"])
                    with c14:
                        max_records = st.number_input("Max records", value=candles_config["max_records"])
                    st.write("---")
                    candles.append(CandlesConfig(connector=connector, trading_pair=trading_pair, interval=interval,
                                                 max_records=max_records))
                field_value = candles
            elif field_name == "order_levels":
                new_levels = []
                st.write(f"## Order Levels:")
                for order_level in field_value:
                    st.write(f"### Level {order_level['level']} {order_level['side'].name}")
                    ol_c1, ol_c2 = st.columns([5, 1])
                    with ol_c1:
                        st.write("#### Triple Barrier config:")
                        c21, c22, c23, c24, c25 = st.columns(5)
                        triple_barrier_conf_level = order_level["triple_barrier_conf"]
                        with c21:
                            take_profit = st.number_input("Take profit", value=float(triple_barrier_conf_level["take_profit"]),
                                                          key=f"{order_level['level']}_{order_level['side'].name}_tp")
                        with c22:
                            stop_loss = st.number_input("Stop Loss", value=float(triple_barrier_conf_level["stop_loss"]),
                                                        key=f"{order_level['level']}_{order_level['side'].name}_sl")
                        with c23:
                            time_limit = st.number_input("Time Limit", value=triple_barrier_conf_level["time_limit"],
                                                         key=f"{order_level['level']}_{order_level['side'].name}_tl")
                        with c24:
                            ts_ap = st.number_input("Trailing Stop Activation Price", value=float(triple_barrier_conf_level["trailing_stop_activation_price_delta"]),
                                                    key=f"{order_level['level']}_{order_level['side'].name}_tsap", format="%.4f")
                        with c25:
                            ts_td = st.number_input("Trailing Stop Trailing Delta", value=float(triple_barrier_conf_level["trailing_stop_trailing_delta"]),
                                                    key=f"{order_level['level']}_{order_level['side'].name}_tstd", format="%.4f")
                    with ol_c2:
                        st.write("#### Position config:")
                        c31, c32 = st.columns(2)
                        with c31:
                            order_amount = st.number_input("Order amount USD", value=float(order_level["order_amount_usd"]),
                                                           key=f"{order_level['level']}_{order_level['side'].name}_oa")
                        with c32:
                            cooldown_time = st.number_input("Cooldown time", value=order_level["cooldown_time"],
                                                            key=f"{order_level['level']}_{order_level['side'].name}_cd")
                        triple_barrier_conf = TripleBarrierConf(stop_loss=Decimal(stop_loss), take_profit=Decimal(take_profit),
                                                                time_limit=time_limit,
                                                                trailing_stop_activation_price_delta=Decimal(ts_ap),
                                                                trailing_stop_trailing_delta=Decimal(ts_td),
                                                                open_order_type=OrderType.MARKET)
                        new_levels.append(OrderLevel(level=order_level["level"], side=order_level["side"],
                                                     order_amount_usd=order_amount, cooldown_time=cooldown_time,
                                                     triple_barrier_conf=triple_barrier_conf))
                    st.write("---")

                field_value = new_levels
            elif field_name == "position_mode":
                field_value = PositionMode.HEDGE
            else:
                field_value = None
        st.session_state["strategy_params"][field_name] = field_value

        column_index = (column_index + 1) % 4

    st.write("### Backtesting period")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 0.5])
    with col1:
        trade_cost = st.number_input("Trade cost",
                                     value=0.0006,
                                     min_value=0.0001, format="%.4f", )
        initial_portfolio_usd = st.number_input("Initial portfolio usd",
                                                value=10000.00,
                                                min_value=1.00,
                                                max_value=999999999.99)
    with col2:
        start = st.text_input("Start", value="2023-01-01")
        indicators_config_path = st.selectbox("Indicators config path", utils.get_indicators_config_paths())
    with col3:
        end = st.text_input("End", value="2024-01-01")
    with col4:
        show_buys = st.checkbox("Buys", value=False)
        show_sells = st.checkbox("Sells", value=False)
        show_positions = st.checkbox("Positions", value=False)
        show_indicators = st.checkbox("Indicators", value=False)
        save_config = st.button("💾Save controller config!")
        config = controller["config"](**st.session_state["strategy_params"])
        controller = controller["class"](config=config)
        if save_config:
            encoder_decoder = ConfigEncoderDecoder(TradeType, OrderType, PositionMode)
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

            backtesting_charts = BacktestingCharts(strategy_analysis)
            backtesting_candles = BacktestingCandles(strategy_analysis,
                                                     indicators_config=utils.load_indicators_config(indicators_config_path),
                                                     line_mode=False,
                                                     show_buys=show_buys,
                                                     show_sells=show_sells,
                                                     show_indicators=show_indicators,
                                                     show_positions=show_positions)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🏦 General")
            with col2:
                st.subheader("📋 General stats")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Exchange", st.session_state["strategy_params"]["exchange"])
            with col2:
                st.metric("Trading Pair", st.session_state["strategy_params"]["trading_pair"])
            with col3:
                st.metric("Start date", strategy_analysis.start_date().strftime("%Y-%m-%d %H:%M"))
                st.metric("End date", strategy_analysis.end_date().strftime("%Y-%m-%d %H:%M"))
            with col4:
                st.metric("Duration (hours)", f"{strategy_analysis.duration_in_minutes() / 60:.2f}")
                st.metric("Price change", st.session_state["strategy_params"]["trading_pair"])
            st.subheader("📈 Performance")
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
            with col1:
                st.metric("Net PnL USD",
                          f"{strategy_analysis.net_profit_usd():.2f}",
                          delta=f"{100 * strategy_analysis.net_profit_pct():.2f}%",
                          help="The overall profit or loss achieved.")
            with col2:
                st.metric("Total positions",
                          f"{strategy_analysis.total_positions()}",
                          help="The total number of closed trades, winning and losing.")
            with col3:
                st.metric("Accuracy",
                          f"{100 * (len(strategy_analysis.win_signals()) / strategy_analysis.total_positions()):.2f} %",
                          help="The percentage of winning trades, the number of winning trades divided by the"
                               " total number of closed trades")
            with col4:
                st.metric("Profit factor",
                          f"{strategy_analysis.profit_factor():.2f}",
                          help="The amount of money the strategy made for every unit of money it lost, "
                               "gross profits divided by gross losses.")
            with col5:
                st.metric("Max Drawdown",
                          f"{strategy_analysis.max_drawdown_usd():.2f}",
                          delta=f"{100 * strategy_analysis.max_drawdown_pct():.2f}%",
                          help="The greatest loss drawdown, i.e., the greatest possible loss the strategy had compared "
                               "to its highest profits")
            with col6:
                st.metric("Avg Profit",
                          f"{strategy_analysis.avg_profit():.2f}",
                          help="The sum of money gained or lost by the average trade, Net Profit divided by "
                               "the overall number of closed trades.")
            with col7:
                st.metric("Avg Minutes",
                          f"{strategy_analysis.avg_trading_time_in_minutes():.2f}",
                          help="The average number of minutes that elapsed during trades for all closed trades.")
            with col8:
                st.metric("Sharpe Ratio",
                          f"{strategy_analysis.sharpe_ratio():.2f}",
                          help="The Sharpe ratio is a measure that quantifies the risk-adjusted return of an investment"
                               " or portfolio. It compares the excess return earned above a risk-free rate per unit of"
                               " risk taken.")
            st.plotly_chart(backtesting_charts.realized_pnl_over_time_fig, use_container_width=True)
            st.subheader("💱 Market activity")
            st.plotly_chart(backtesting_candles.figure(), use_container_width=True)

        except FileNotFoundError:
            st.warning(f"The requested candles could not be found.")
