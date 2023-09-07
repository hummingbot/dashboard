from hummingbot.core.data_type.common import PositionMode, TradeType, OrderType
from hummingbot.data_feed.candles_feed.candles_factory import CandlesConfig
from hummingbot.smart_components.strategy_frameworks.data_types import OrderLevel
from hummingbot.smart_components.strategy_frameworks.directional_trading import DirectionalTradingBacktestingEngine

import constants
import os
import json
import streamlit as st
from docker_manager import DockerManager

from quants_lab.strategy.strategy_analysis import StrategyAnalysis
from utils.enum_encoder import EnumEncoderDecoder
from utils.graphs import BacktestingGraphs
from utils.optuna_database_manager import OptunaDBManager
from utils.os_utils import load_controllers, dump_dict_to_yaml
from utils.st_utils import initialize_st_page

initialize_st_page(title="Analyze", icon="🔬", initial_sidebar_state="collapsed")


@st.cache_resource
def get_databases():
    sqlite_files = [db_name for db_name in os.listdir("data/backtesting") if db_name.endswith(".db")]
    databases_list = [OptunaDBManager(db) for db in sqlite_files]
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
    opt_db = OptunaDBManager(selected_db)
    # Load studies
    studies = opt_db.load_studies()
    # Choose study
    study_selected = st.selectbox("Select a study:", studies.keys())
    # Filter trials from selected study
    merged_df = opt_db.merged_df[opt_db.merged_df["study_name"] == study_selected]
    bt_graphs = BacktestingGraphs(merged_df)
    # Show and compare all of the study trials
    st.plotly_chart(bt_graphs.pnl_vs_maxdrawdown(), use_container_width=True)
    # Get study trials
    trials = studies[study_selected]
    # Choose trial
    trial_selected = st.selectbox("Select a trial to backtest", list(trials.keys()))
    trial = trials[trial_selected]
    # Transform trial config in a dictionary
    encoder_decoder = EnumEncoderDecoder(TradeType, OrderType, PositionMode)
    trial_config = encoder_decoder.decode(json.loads(trial["config"]))

    # Strategy parameters section
    st.write("## Strategy parameters")
    # Load strategies (class, config, module)
    controllers = load_controllers(constants.DIRECTIONAL_STRATEGIES_PATH)
    # Select strategy
    controller = controllers[trial_config["strategy_name"]]
    # Get field schema
    field_schema = controller["config"].schema()["properties"]

    c1, c2 = st.columns([5, 1])
    # Render every field according to schema
    with c1:
        columns = st.columns(4)
        column_index = 0
        for field_name, properties in field_schema.items():
            field_type = properties.get("type", "string")
            field_value = trial_config[field_name]
            with columns[column_index]:
                if field_type == "array" or field_name == "position_mode":
                    pass
                elif field_type in ["number", "integer"]:
                    field_value = st.number_input(field_name,
                                                  value=field_value,
                                                  min_value=properties.get("minimum"),
                                                  max_value=properties.get("maximum"),
                                                  key=field_name)
                elif field_type in ["string"]:
                    field_value = st.text_input(field_name, value=field_value)
                elif field_type == "boolean":
                    # TODO: Add support for boolean fields in optimize tab
                    field_value = st.checkbox(field_name, value=field_value)
                else:
                    raise ValueError(f"Field type {field_type} not supported")
                try:
                    # TODO: figure out how to make this configurable
                    if field_name == "candles_config":
                        candles_config = [CandlesConfig(**value) for value in field_value]
                        st.session_state["strategy_params"][field_name] = candles_config
                    elif field_name == "order_levels":
                        order_levels = [OrderLevel(**value) for value in field_value]
                        st.session_state["strategy_params"][field_name] = order_levels
                    st.session_state["strategy_params"][field_name] = field_value
                except KeyError as e:
                    pass
            column_index = (column_index + 1) % 4
    with c2:
        add_positions = st.checkbox("Add positions", value=True)
        add_volume = st.checkbox("Add volume", value=True)
        add_pnl = st.checkbox("Add PnL", value=True)

    # Backtesting parameters section
    st.write("## Backtesting parameters")
    # # Get every trial params
    # # TODO: Filter only from selected study
    backtesting_configs = opt_db.load_params()
    # # Get trial backtesting params
    backtesting_params = backtesting_configs[trial_selected]
    col1, col2, col3 = st.columns(3)
    with col1:
        trade_cost = st.number_input("Trade cost",
                                     value=0.0006,
                                     min_value=0.0001, format="%.4f",)
    with col2:
        initial_portfolio_usd = st.number_input("Initial portfolio usd",
                                                value=10000.00,
                                                min_value=1.00,
                                                max_value=999999999.99)
    with col3:
        start = st.text_input("Start", value="2023-01-01")
        end = st.text_input("End", value="2023-08-01")
    deploy_button = st.button("🚀Deploy!")
    config = controller["config"](**st.session_state["strategy_params"])
    controller = controller["class"](config=config)
    if deploy_button:
        dump_dict_to_yaml(config.dict(),
                          f"hummingbot_files/controller_configs/{config.strategy_name}_{trial_selected}.yml")
        DockerManager().create_hummingbot_instance(instance_name=config.strategy_name,
                                                   base_conf_folder=f"{constants.HUMMINGBOT_TEMPLATES}/master_bot_conf/.",
                                                   target_conf_folder=f"{constants.BOTS_FOLDER}/{config.strategy_name}/.",
                                                   controllers_folder="quants_lab/controllers",
                                                   controllers_config_folder="hummingbot_files/controller_configs",
                                                   image="dardonacci/hummingbot")
    if st.button("Run Backtesting!"):
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
            metrics_container = bt_graphs.get_trial_metrics(strategy_analysis,
                                                            add_positions=add_positions,
                                                            add_volume=add_volume)

        except FileNotFoundError:
            st.warning(f"The requested candles could not be found.")
