import os

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from utils.data_manipulation import StrategyData


class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        # TODO: Create db path for all types of db
        self.db_path = f'sqlite:///{os.path.join("data", db_name)}'
        self.engine = create_engine(self.db_path, connect_args={'check_same_thread': False})
        self.session_maker = sessionmaker(bind=self.engine)

    def get_config_files(self):
        with self.session_maker() as session:
            query = 'SELECT DISTINCT config_file_path FROM TradeFill'
            config_files = pd.read_sql_query(query, session.connection())
        return config_files['config_file_path'].tolist()

    def get_exchanges_trading_pairs_by_config_file(self, config_file_path):
        with self.session_maker() as session:
            query = f"SELECT DISTINCT market, symbol FROM TradeFill WHERE config_file_path = '{config_file_path}'"
            exchanges_trading_pairs = pd.read_sql_query(query, session.connection())
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

    def get_orders(self, config_file_path=None, start_date=None, end_date=None):
        with self.session_maker() as session:
            query = self._get_orders_query(config_file_path, start_date, end_date)
            orders = pd.read_sql_query(query, session.connection())
            orders["market"] = orders["market"].apply(lambda x: x.lower().replace("_papertrade", ""))
            orders["amount"] = orders["amount"] / 1e6
            orders["price"] = orders["price"] / 1e6
        return orders

    def get_trade_fills(self, config_file_path=None, start_date=None, end_date=None):
        with self.session_maker() as session:
            query = self._get_trade_fills_query(config_file_path, start_date, end_date)
            trade_fills = pd.read_sql_query(query, session.connection())
            trade_fills["amount"] = trade_fills["amount"] / 1e6
            trade_fills["price"] = trade_fills["price"] / 1e6
            trade_fills["trade_fee_in_quote"] = trade_fills["trade_fee_in_quote"] / 1e6
            trade_fills["cum_fees_in_quote"] = trade_fills["trade_fee_in_quote"].cumsum()
            trade_fills.loc[:, "net_amount"] = trade_fills['amount'] * trade_fills['trade_type'].apply(
                lambda x: 1 if x == 'BUY' else -1)
            trade_fills.loc[:, "net_amount_quote"] = trade_fills['net_amount'] * trade_fills['price']
            trade_fills.loc[:, "cum_net_amount"] = trade_fills["net_amount"].cumsum()
            trade_fills.loc[:, "unrealized_trade_pnl"] = -1 * trade_fills["net_amount_quote"].cumsum()
            trade_fills.loc[:, "inventory_cost"] = trade_fills["cum_net_amount"] * trade_fills["price"]
            trade_fills.loc[:, "realized_trade_pnl"] = trade_fills["unrealized_trade_pnl"] + trade_fills["inventory_cost"]
            trade_fills.loc[:, "net_realized_pnl"] = trade_fills["realized_trade_pnl"] - trade_fills["cum_fees_in_quote"]
            trade_fills["market"] = trade_fills["market"].apply(lambda x: x.lower().replace("_papertrade", ""))

        return trade_fills

    def get_order_status(self, order_ids=None, start_date=None, end_date=None):
        with self.session_maker() as session:
            query = self._get_order_status_query(order_ids, start_date, end_date)
            order_status = pd.read_sql_query(query, session.connection())
        return order_status

    def get_strategy_data(self, config_file_path=None, start_date=None, end_date=None):
        orders = self.get_orders(config_file_path, start_date, end_date)
        trade_fills = self.get_trade_fills(config_file_path, start_date, end_date)
        order_status = self.get_order_status(orders['id'].tolist(), start_date, end_date)
        orders['creation_timestamp'] = pd.to_datetime(orders['creation_timestamp'], unit="ms")
        orders['last_update_timestamp'] = pd.to_datetime(orders['last_update_timestamp'], unit="ms")
        trade_fills["timestamp"] = pd.to_datetime(trade_fills["timestamp"], unit="ms")
        strategy_data = StrategyData(orders, order_status, trade_fills)
        return strategy_data
