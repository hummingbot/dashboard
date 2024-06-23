import os
import json
import pandas as pd
from enum import Enum
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from hummingbot.strategy_v2.models.executors_info import CloseType


class HummingbotDatabase:
    def __init__(self, db_path: str, instance_name: str = None):
        self.db_name = os.path.basename(db_path)
        self.db_path = db_path
        self.instance_name = instance_name
        self.db_path = f'sqlite:///{os.path.join(db_path)}'
        self.engine = create_engine(self.db_path, connect_args={'check_same_thread': False})
        self.session_maker = sessionmaker(bind=self.engine)

    @staticmethod
    def load_data(table_loader):
        try:
            return table_loader()
        except Exception as e:
            return None  # Return None to indicate failure

    @staticmethod
    def _get_table_status(table_loader):
        try:
            data = table_loader()
            return "Correct" if len(data) > 0 else f"Error - No records matched"
        except Exception as e:
            return f"Error - {str(e)}"

    @property
    def status(self):
        trade_fill_status = self._get_table_status(self.get_trade_fills)
        orders_status = self._get_table_status(self.get_orders)
        order_status_status = self._get_table_status(self.get_order_status)
        executors_status = self._get_table_status(self.get_executors_data)
        general_status = all(status == "Correct" for status in
                             [trade_fill_status, orders_status, order_status_status, executors_status])
        status = {"db_name": self.db_name,
                  "db_path": self.db_path,
                  "instance_name": self.instance_name,
                  "trade_fill": trade_fill_status,
                  "orders": orders_status,
                  "order_status": order_status_status,
                  "executors": executors_status,
                  "general_status": general_status
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
    def _get_executors_query(start_date=None, end_date=None):
        query = "SELECT * FROM Executors"
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

    def get_executors_data(self, start_date=None, end_date=None) -> pd.DataFrame:
        with self.session_maker() as session:
            query = self._get_executors_query(start_date, end_date)
            executors = pd.read_sql_query(text(query), session.connection())
            executors["datetime"] = pd.to_datetime(executors.timestamp, unit="s")
            executors["close_datetime"] = pd.to_datetime(executors["close_timestamp"], unit="s")
            executors["trading_pair"] = executors["config"].apply(lambda x: json.loads(x)["trading_pair"])
            executors["exchange"] = executors["config"].apply(lambda x: json.loads(x)["connector_name"])
            executors["side"] = executors["config"].apply(lambda x: json.loads(x)["side"])
            executors["level_id"] = executors["config"].apply(lambda x: json.loads(x).get("level_id") if json.loads(x).get("level_id") is not None else 0)
            executors["bep"] = executors["custom_info"].apply(lambda x: json.loads(x)["current_position_average_price"])
            executors["close_price"] = executors["custom_info"].apply(lambda x: json.loads(x)["close_price"])
            executors["sl"] = executors["config"].apply(lambda x: json.loads(x)["stop_loss"]).fillna(0)
            executors["tp"] = executors["config"].apply(lambda x: json.loads(x)["take_profit"]).fillna(0)
            executors["tl"] = executors["config"].apply(lambda x: json.loads(x)["time_limit"]).fillna(0)
            executors = executors[~executors["close_timestamp"].isna()]
        return executors
