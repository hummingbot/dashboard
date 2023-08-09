import constants
import os
import json
import streamlit as st

from quants_lab.strategy.strategy_analysis import StrategyAnalysis
from utils.graphs import BacktestingGraphs
from utils.optuna_database_manager import OptunaDBManager
from utils.os_utils import load_directional_strategies
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
    trial_config = json.loads(trial["config"])

    # Strategy parameters section
    st.write("## Strategy parameters")
    # Load strategies (class, config, module)
    strategies = load_directional_strategies(constants.DIRECTIONAL_STRATEGIES_PATH)
    # Select strategy
    strategy = strategies[trial_config["name"]]
    # Get field schema
    field_schema = strategy["config"].schema()["properties"]
    c1, c2 = st.columns([5, 1])
    # Render every field according to schema
    with c1:
        columns = st.columns(4)
        column_index = 0
        for field_name, properties in field_schema.items():
            field_type = properties["type"]
            field_value = trial_config[field_name]
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
                try:
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
    # Get every trial params
    # TODO: Filter only from selected study
    backtesting_configs = opt_db.load_params()
    # Get trial backtesting params
    backtesting_params = backtesting_configs[trial_selected]
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_order_amount = st.number_input("Order amount",
                                                value=50.0,
                                                min_value=0.1,
                                                max_value=999999999.99)
        selected_leverage = st.number_input("Leverage",
                                            value=10,
                                            min_value=1,
                                            max_value=200)
    with col2:
        selected_initial_portfolio = st.number_input("Initial portfolio",
                                                     value=10000.00,
                                                     min_value=1.00,
                                                     max_value=999999999.99)
        selected_time_limit = st.number_input("Time Limit",
                                              value=60 * 60 * backtesting_params["time_limit"]["param_value"],
                                              min_value=60 * 60 * float(backtesting_params["time_limit"]["low"]),
                                              max_value=60 * 60 * float(backtesting_params["time_limit"]["high"]))
    with col3:
        selected_tp_multiplier = st.number_input("Take Profit Multiplier",
                                                 value=backtesting_params["take_profit_multiplier"]["param_value"],
                                                 min_value=backtesting_params["take_profit_multiplier"]["low"],
                                                 max_value=backtesting_params["take_profit_multiplier"]["high"])
        selected_sl_multiplier = st.number_input("Stop Loss Multiplier",
                                                 value=backtesting_params["stop_loss_multiplier"]["param_value"],
                                                 min_value=backtesting_params["stop_loss_multiplier"]["low"],
                                                 max_value=backtesting_params["stop_loss_multiplier"]["high"])

    if st.button("Run Backtesting!"):
        config = strategy["config"](**st.session_state["strategy_params"])
        strategy = strategy["class"](config=config)
        try:
            market_data, positions = strategy.run_backtesting(
                order_amount=selected_order_amount,
                leverage=selected_order_amount,
                initial_portfolio=selected_initial_portfolio,
                take_profit_multiplier=selected_tp_multiplier,
                stop_loss_multiplier=selected_sl_multiplier,
                time_limit=selected_time_limit,
                std_span=None,
            )
            strategy_analysis = StrategyAnalysis(
                positions=positions,
                candles_df=market_data,
            )
            metrics_container = bt_graphs.get_trial_metrics(strategy_analysis,
                                                            add_positions=add_positions,
                                                            add_volume=add_volume,
                                                            add_pnl=add_pnl)
        except FileNotFoundError:
            st.warning(f"The requested candles could not be found.")
