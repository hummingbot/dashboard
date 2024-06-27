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

    def get_orders(self, config_file_path=None, start_date=None, end_date=None):
        with self.session_maker() as session:
            query = "SELECT * FROM 'Order'"
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
            query = "SELECT * FROM TradeFill"
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
            query = "SELECT * FROM OrderStatus"
            order_status = pd.read_sql_query(text(query), session.connection())
        return order_status

    def get_executors_data(self, start_date=None, end_date=None) -> pd.DataFrame:
        with self.session_maker() as session:
            query = "SELECT * FROM Executors"
            executors = pd.read_sql_query(text(query), session.connection())
        return executors
