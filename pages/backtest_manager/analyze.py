import constants
from utils.st_utils import initialize_st_page
from utils.optuna_database_manager import OptunaDBManager
import pandas as pd
import os
import json
import streamlit as st
from quants_lab.strategy.strategy_analysis import StrategyAnalysis
import plotly.graph_objs as go

from utils.os_utils import load_directional_strategies

initialize_st_page(title="Analyze", icon="🔬", initial_sidebar_state="collapsed")


def load_params(df: pd.DataFrame):
    trial_id_col = 'trial_id'
    param_name_col = 'param_name'
    param_value_col = 'param_value'
    distribution_json_col = 'distribution_json'
    nested_dict = {}
    for _, row in df.iterrows():
        trial_id = row[trial_id_col]
        param_name = row[param_name_col]
        param_value = row[param_value_col]
        distribution_json = row[distribution_json_col]

        if trial_id not in nested_dict:
            nested_dict[trial_id] = {}

        dist_json = json.loads(distribution_json)
        nested_dict[trial_id][param_name] = {
            'param_name': param_name,
            'param_value': param_value,
            'step': dist_json["attributes"]["step"],
            'low': dist_json["attributes"]["low"],
            'high': dist_json["attributes"]["high"],
            'log': dist_json["attributes"]["log"],
        }
    return nested_dict


def load_studies(df: pd.DataFrame):
    study_id_col = 'study_id'
    trial_id_col = 'trial_id'
    nested_dict = {}
    for _, row in df.iterrows():
        study_id = row[study_id_col]
        trial_id = row[trial_id_col]
        data_dict = row.drop([study_id_col, trial_id_col]).to_dict()
        if study_id not in nested_dict:
            nested_dict[study_id] = {}
        nested_dict[study_id][trial_id] = data_dict
    return nested_dict


@st.cache_resource
def get_databases():
    sqlite_files = [db_name for db_name in os.listdir("data/backtesting") if db_name.endswith(".db")]
    databases_list = [OptunaDBManager(db) for db in sqlite_files]
    return {database.db_name: database for database in databases_list}


def pnl_vs_maxdrawdown(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(name="Pnl vs Max Drawdown",
                             x=-100 * df["max_drawdown_pct"],
                             y=100 * df["net_profit_pct"],
                             mode="markers",
                             text=None,
                             hovertext=df["hover_text"]))
    fig.update_layout(
        title="PnL vs Max Drawdown",
        xaxis_title="Max Drawdown [%]",
        yaxis_title="Net Profit [%]",
        height=800
    )
    fig.data[0].text = []
    return fig


def initialize_session_state_vars():
    if "strategy_params" not in st.session_state:
        st.session_state.strategy_params = {}


initialize_session_state_vars()
dbs = get_databases()
db_names = [x.db_name for x in dbs.values() if x.status == 'OK']
if not db_names:
    st.warning("No trades have been recorded in the selected database")
    selected_db_name = None
    selected_db = None
else:
    selected_db = st.selectbox("Select your database:", db_names)
    opt_db = OptunaDBManager(selected_db)
    st.plotly_chart(pnl_vs_maxdrawdown(opt_db.merged_df), use_container_width=True)

    strategies = load_directional_strategies(constants.DIRECTIONAL_STRATEGIES_PATH)
    studies = load_studies(opt_db.merged_df)
    study_selected = st.selectbox("Select a study:", studies.keys())
    trials = studies[study_selected]
    trial_selected = st.selectbox("Select a trial to backtest", list(trials.keys()))
    trial = trials[trial_selected]
    trial_config = json.loads(trial["config"])
    strategy = strategies[trial_config["name"]]
    strategy_config = strategy["config"]
    field_schema = strategy_config.schema()["properties"]
    st.write("## Strategy parameters")
    c1, c2 = st.columns([5, 1])
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

    st.subheader("Position config")
    position_configs = load_params(opt_db.trial_params)
    position_params = position_configs[trial_selected]
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_order_amount = st.number_input("Order amount", value=50.0, min_value=0.1, max_value=999999999.99)
        selected_leverage = st.number_input("Leverage", value=10, min_value=1, max_value=200)
    with col2:
        selected_initial_portfolio = st.number_input("Initial portfolio", value=10000.00, min_value=1.00,
                                                     max_value=999999999.99)
        selected_time_limit = st.number_input("Time Limit",
                                              value=60 * 60 * position_params["time_limit"]["param_value"],
                                              min_value=60 * 60 * float(position_params["time_limit"]["low"]),
                                              max_value=60 * 60 * float(position_params["time_limit"]["high"]))
    with col3:
        selected_tp_multiplier = st.number_input("Take Profit Multiplier",
                                                 value=position_params["take_profit_multiplier"]["param_value"],
                                                 min_value=position_params["take_profit_multiplier"]["low"],
                                                 max_value=position_params["take_profit_multiplier"]["high"])
        selected_sl_multiplier = st.number_input("Stop Loss Multiplier",
                                                 value=position_params["stop_loss_multiplier"]["param_value"],
                                                 min_value=position_params["stop_loss_multiplier"]["low"],
                                                 max_value=position_params["stop_loss_multiplier"]["high"])
    run_backtesting_button = st.button("Run Backtesting!")
    if run_backtesting_button:
        config = strategy["config"](**st.session_state["strategy_params"])
        strategy = strategy["class"](config=config)
        try:
            market_data, positions = strategy.run_backtesting(
                start='2021-04-01',
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
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🏦 Market")
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
                st.metric("% Profitable",
                          f"{(len(strategy_analysis.win_signals()) / strategy_analysis.total_positions()):.2f}",
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
                          delta=f"{strategy_analysis.max_drawdown_pct():.2f}%",
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
            st.plotly_chart(strategy_analysis.pnl_over_time(), use_container_width=True)
            strategy_analysis.create_base_figure(volume=add_volume, positions=add_positions, trade_pnl=add_pnl)
            st.plotly_chart(strategy_analysis.figure(), use_container_width=True)
        except FileNotFoundError:
            st.warning(f"The requested candles could not be found.")
