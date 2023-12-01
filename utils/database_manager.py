import os
import streamlit as st

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from utils.data_manipulation import StrategyData


class DatabaseManager:
    def __init__(self, db_name: str, executors_path: str = "data"):
        self.db_name = db_name
        # TODO: Create db path for all types of db
        self.db_path = f'sqlite:///{os.path.join(db_name)}'
        self.engine = create_engine(self.db_path, connect_args={'check_same_thread': False})
        self.session_maker = sessionmaker(bind=self.engine)

    def get_strategy_data(self, config_file_path=None, start_date=None, end_date=None):
        def load_data(table_loader):
            try:
                return table_loader()
            except Exception as e:
                return None  # Return None to indicate failure

        # Use load_data to load tables
        orders = load_data(self.get_orders)
        trade_fills = load_data(self.get_trade_fills)
        order_status = load_data(self.get_order_status)
        market_data = load_data(self.get_market_data)
        position_executor = load_data(self.get_position_executor_data)

        strategy_data = StrategyData(orders, order_status, trade_fills, market_data, position_executor)
        return strategy_data

    @staticmethod
    def _get_table_status(table_loader):
        try:
            data = table_loader()
            return "Correct" if len(data) > 0 else f"Error - No records matched"
        except Exception as e:
            return f"Error - {str(e)}"

    @property
    def status(self):
        status = {"db_name": self.db_name,
                  "trade_fill": self._get_table_status(self.get_trade_fills),
                  "orders": self._get_table_status(self.get_orders),
                  "order_status": self._get_table_status(self.get_order_status),
                  "market_data": self._get_table_status(self.get_market_data),
                  "position_executor": self._get_table_status(self.get_position_executor_data),
                  }
        return status

    @property
    def config_files(self):
        return self.get_config_files()

    @property
    def configs(self):
        return {config_file: self.get_exchanges_trading_pairs_by_config_file(config_file) for config_file in self.config_files}

    def get_config_files(self):
        with self.session_maker() as session:
            query = 'SELECT DISTINCT config_file_path FROM TradeFill'
            config_files = pd.read_sql_query(text(query), session.connection())
        return config_files['config_file_path'].tolist()

    def get_exchanges_trading_pairs_by_config_file(self, config_file_path):
        with self.session_maker() as session:
            query = f"SELECT DISTINCT market, symbol FROM TradeFill WHERE config_file_path = '{config_file_path}'"
            exchanges_trading_pairs = pd.read_sql_query(text(query), session.connection())
            exchanges_trading_pairs["market"] = exchanges_trading_pairs["market"].apply(
                lambda x: x.lower().replace("_papertrade", ""))
            exchanges_trading_pairs = exchanges_trading_pairs.groupby("market")["symbol"].apply(list).to_dict()
        return exchanges_trading_pairs

    @staticmethod
    def _get_orders_query(config_file_path=None, start_date=None, end_date=None):
        query = "SELECT * FROM 'Order'"
        conditions = []
        if config_file_path:
            conditions.append(f"config_file_path = '{config_file_path}'")
        if start_date:
            conditions.append(f"created_at >= '{start_date}'")
        if end_date:
            conditions.append(f"created_at <= '{end_date}'")
        if conditions:
            query += f" WHERE {' AND '.join(conditions)}"
        return query

    @staticmethod
    def _get_order_status_query(order_ids=None, start_date=None, end_date=None):
        query = "SELECT * FROM OrderStatus"
        conditions = []
        if order_ids:
            order_ids_string = ",".join(f"'{order_id}'" for order_id in order_ids)
            conditions.append(f"order_id IN ({order_ids_string})")
        if start_date:
            conditions.append(f"created_at >= '{start_date}'")
        if end_date:
            conditions.append(f"created_at <= '{end_date}'")
        if conditions:
            query += f" WHERE {' AND '.join(conditions)}"
        return query

    @staticmethod
    def _get_trade_fills_query(config_file_path=None, start_date=None, end_date=None):
        query = "SELECT * FROM TradeFill"
        conditions = []
        if config_file_path:
            conditions.append(f"config_file_path = '{config_file_path}'")
        if start_date:
            conditions.append(f"created_at >= '{start_date}'")
        if end_date:
            conditions.append(f"created_at <= '{end_date}'")
        if conditions:
            query += f" WHERE {' AND '.join(conditions)}"
        return query

    @staticmethod
    def _get_market_data_query(start_date=None, end_date=None):
        query = "SELECT * FROM MarketData"
        conditions = []
        if start_date:
            conditions.append(f"timestamp >= '{start_date * 1e6}'")
        if end_date:
            conditions.append(f"timestamp <= '{end_date * 1e6}'")
        if conditions:
            query += f" WHERE {' AND '.join(conditions)}"
        return query

    @staticmethod
    def _get_position_executor_query(start_date=None, end_date=None):
        query = "SELECT * FROM PositionExecutors"
        conditions = []
        if start_date:
            conditions.append(f"timestamp >= '{start_date}'")
        if end_date:
            conditions.append(f"timestamp <= '{end_date}'")
        if conditions:
            query += f" WHERE {' AND '.join(conditions)}"
        return query

    def get_orders(self, config_file_path=None, start_date=None, end_date=None):
        with self.session_maker() as session:
            query = self._get_orders_query(config_file_path, start_date, end_date)
            orders = pd.read_sql_query(text(query), session.connection())
            orders["market"] = orders["market"]
            orders["amount"] = orders["amount"] / 1e6
            orders["price"] = orders["price"] / 1e6
            orders['creation_timestamp'] = pd.to_datetime(orders['creation_timestamp'], unit="ms")
            orders['last_update_timestamp'] = pd.to_datetime(orders['last_update_timestamp'], unit="ms")
        return orders

    def get_trade_fills(self, config_file_path=None, start_date=None, end_date=None):
        groupers = ["config_file_path", "market", "symbol"]
        float_cols = ["amount", "price", "trade_fee_in_quote"]
        with self.session_maker() as session:
            query = self._get_trade_fills_query(config_file_path, start_date, end_date)
            trade_fills = pd.read_sql_query(text(query), session.connection())
            trade_fills[float_cols] = trade_fills[float_cols] / 1e6
            trade_fills["cum_fees_in_quote"] = trade_fills.groupby(groupers)["trade_fee_in_quote"].cumsum()
            trade_fills["net_amount"] = trade_fills['amount'] * trade_fills['trade_type'].apply(lambda x: 1 if x == 'BUY' else -1)
            trade_fills["net_amount_quote"] = trade_fills['net_amount'] * trade_fills['price']
            trade_fills["cum_net_amount"] = trade_fills.groupby(groupers)["net_amount"].cumsum()
            trade_fills["unrealized_trade_pnl"] = -1 * trade_fills.groupby(groupers)["net_amount_quote"].cumsum()
            trade_fills["inventory_cost"] = trade_fills["cum_net_amount"] * trade_fills["price"]
            trade_fills["realized_trade_pnl"] = trade_fills["unrealized_trade_pnl"] + trade_fills["inventory_cost"]
            trade_fills["net_realized_pnl"] = trade_fills["realized_trade_pnl"] - trade_fills["cum_fees_in_quote"]
            trade_fills["realized_pnl"] = trade_fills.groupby(groupers)["net_realized_pnl"].diff()
            trade_fills["gross_pnl"] = trade_fills.groupby(groupers)["realized_trade_pnl"].diff()
            trade_fills["trade_fee"] = trade_fills.groupby(groupers)["cum_fees_in_quote"].diff()
            trade_fills["timestamp"] = pd.to_datetime(trade_fills["timestamp"], unit="ms")
            trade_fills["market"] = trade_fills["market"]
            trade_fills["quote_volume"] = trade_fills["price"] * trade_fills["amount"]
        return trade_fills

    def get_order_status(self, order_ids=None, start_date=None, end_date=None):
        with self.session_maker() as session:
            query = self._get_order_status_query(order_ids, start_date, end_date)
            order_status = pd.read_sql_query(text(query), session.connection())
        return order_status

    def get_market_data(self, start_date=None, end_date=None):
        with self.session_maker() as session:
            query = self._get_market_data_query(start_date, end_date)
            market_data = pd.read_sql_query(text(query), session.connection())
            market_data["timestamp"] = pd.to_datetime(market_data["timestamp"] / 1e6, unit="ms")
            market_data.set_index("timestamp", inplace=True)
            market_data["mid_price"] = market_data["mid_price"] / 1e6
            market_data["best_bid"] = market_data["best_bid"] / 1e6
            market_data["best_ask"] = market_data["best_ask"] / 1e6
        return market_data

    def get_position_executor_data(self, start_date=None, end_date=None) -> pd.DataFrame:
        with self.session_maker() as session:
            query = self._get_position_executor_query(start_date, end_date)
            position_executor = pd.read_sql_query(text(query), session.connection())
            position_executor.set_index("timestamp", inplace=True)
            position_executor["datetime"] = pd.to_datetime(position_executor.index, unit="s")
            position_executor["level"] = position_executor["order_level"].apply(lambda x: x.split("_")[1])
        return position_executor
