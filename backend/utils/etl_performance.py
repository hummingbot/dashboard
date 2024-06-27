import json
from typing import List

from hummingbot.core.data_type.common import TradeType
from hummingbot.strategy_v2.models.base import RunnableStatus
from hummingbot.strategy_v2.models.executors import CloseType
from sqlalchemy import create_engine, delete, insert, text, MetaData, Table, Column, VARCHAR, INT, FLOAT, TIMESTAMP,  Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker
import pandas as pd
import os


from hummingbot.strategy_v2.models.executors_info import ExecutorInfo


class ETLPerformance:
    def __init__(self,
                 db_path: str):
        self.db_path = f'sqlite:///{os.path.join(db_path)}'
        self.engine = create_engine(self.db_path, connect_args={'check_same_thread': False})
        self.session_maker = sessionmaker(bind=self.engine)
        self.metadata = MetaData()

    @property
    def executors_table(self):
        return Table('executors',
                     MetaData(),
                     Column('id', String),
                     Column('timestamp', Integer),
                     Column('type', String),
                     Column('close_type', Integer),
                     Column('close_timestamp', Integer),
                     Column('status', String),
                     Column('config', String),
                     Column('net_pnl_pct', Float),
                     Column('net_pnl_quote', Float),
                     Column('cum_fees_quote', Float),
                     Column('filled_amount_quote', Float),
                     Column('is_active', Integer),
                     Column('is_trading', Integer),
                     Column('custom_info', String),
                     Column('controller_id', String))

    @property
    def trade_fill_table(self):
        return Table(
            'trades', MetaData(),
            Column('config_file_path', VARCHAR(255)),
            Column('strategy', VARCHAR(255)),
            Column('market', VARCHAR(255)),
            Column('symbol', VARCHAR(255)),
            Column('base_asset', VARCHAR(255)),
            Column('quote_asset', VARCHAR(255)),
            Column('timestamp', TIMESTAMP),
            Column('order_id', VARCHAR(255)),
            Column('trade_type', VARCHAR(255)),
            Column('order_type', VARCHAR(255)),
            Column('price', FLOAT),
            Column('amount', FLOAT),
            Column('leverage', INT),
            Column('trade_fee', VARCHAR(255)),
            Column('trade_fee_in_quote', FLOAT),
            Column('exchange_trade_id', VARCHAR(255)),
            Column('position', VARCHAR(255)),
        )

    @property
    def orders_table(self):
        return Table(
            'orders', MetaData(),
            Column('client_order_id', VARCHAR(255)),
            Column('config_file_path', VARCHAR(255)),
            Column('strategy', VARCHAR(255)),
            Column('market', VARCHAR(255)),
            Column('symbol', VARCHAR(255)),
            Column('base_asset', VARCHAR(255)),
            Column('quote_asset', VARCHAR(255)),
            Column('creation_timestamp', TIMESTAMP),
            Column('order_type', VARCHAR(255)),
            Column('amount', FLOAT),
            Column('leverage', INT),
            Column('price', FLOAT),
            Column('last_status', VARCHAR(255)),
            Column('last_update_timestamp', TIMESTAMP),
            Column('exchange_order_id', VARCHAR(255)),
            Column('position', VARCHAR(255)),
        )

    @property
    def tables(self):
        return [self.executors_table, self.trade_fill_table, self.orders_table]

    def list_tables(self):
        with self.session_maker() as session:
            query = "SELECT name FROM sqlite_master WHERE type='table';"
            tables = pd.read_sql_query(text(query), session.connection())
            return [table[0] for table in tables]

    def clean_table(self, table):
        stmt = delete(table)
        with self.session_maker() as conn:
            conn.execute(stmt)
            conn.commit()

    def clean_tables(self):
        for table in self.tables:
            self.clean_table(table)

    def create_table(self, table):
        with self.engine.connect() as conn:
            if not self.engine.dialect.has_table(conn, table.name):  # If table doesn't exist, create it.
                table.create(self.engine)

    def create_tables(self):
        for table in self.tables:
            self.create_table(table)

    def drop_tables(self):
        with self.engine.connect() as conn:
            for table in self.tables:
                conn.execute("DROP TABLE IF EXISTS {}".format(table.name))

    def insert_data(self, data):
        if "executors" in data:
            self.insert_executors(data["executors"])
        if "trade_fill" in data:
            self.insert_trade_fill(data["trade_fill"])
        if "orders" in data:
            self.insert_orders(data["orders"])

    def insert_executors(self, executors):
        with self.engine.connect() as conn:
            for _, row in executors.iterrows():
                ins = self.executors_table.insert().values(
                    timestamp=row["timestamp"],
                    type=row["type"],
                    close_type=row["close_type"],
                    close_timestamp=row["close_timestamp"],
                    status=row["status"],
                    config=row["config"],
                    net_pnl_pct=row["net_pnl_pct"],
                    net_pnl_quote=row["net_pnl_quote"],
                    cum_fees_quote=row["cum_fees_quote"],
                    filled_amount_quote=row["filled_amount_quote"],
                    is_active=row["is_active"],
                    is_trading=row["is_trading"],
                    custom_info=row["custom_info"],
                    controller_id=row["controller_id"])
                conn.execute(ins)
                conn.commit()

    def load_executors(self):
        with self.session_maker() as session:
            query = "SELECT * FROM executors"
            executors = pd.read_sql_query(text(query), session.connection())
            executors["datetime"] = pd.to_datetime(executors.timestamp, unit="s")
            executors["close_datetime"] = pd.to_datetime(executors["close_timestamp"], unit="s")
            executors["status"] = executors["status"].apply(lambda x: self.get_enum_by_value(RunnableStatus, int(x)))
            executors["trading_pair"] = executors["config"].apply(lambda x: json.loads(x)["trading_pair"])
            executors["exchange"] = executors["config"].apply(lambda x: json.loads(x)["connector_name"])
            executors["side"] = executors["config"].apply(lambda x: self.get_enum_by_value(TradeType, int(json.loads(x)["side"])))
            executors["close_type"] = executors["close_type"].apply(lambda x: self.get_enum_by_value(CloseType, int(x)))
            executors["close_type_name"] = executors["close_type"].apply(lambda x: x.name)
            executors["level_id"] = executors["config"].apply(lambda x: json.loads(x).get("level_id") if json.loads(x).get("level_id") is not None else 0)
            executors["bep"] = executors["custom_info"].apply(lambda x: json.loads(x)["current_position_average_price"])
            executors["close_price"] = executors["custom_info"].apply(lambda x: json.loads(x)["close_price"])
            executors["sl"] = executors["config"].apply(lambda x: json.loads(x)["stop_loss"]).fillna(0)
            executors["tp"] = executors["config"].apply(lambda x: json.loads(x)["take_profit"]).fillna(0)
            executors["tl"] = executors["config"].apply(lambda x: json.loads(x)["time_limit"]).fillna(0)
            executors = executors[~executors["close_timestamp"].isna()]
            return executors

    @staticmethod
    def parse_executors(executors):
        executor_values = []
        for _, row in executors.iterrows():
            executor_values.append(ExecutorInfo(
                id=row["id"],
                timestamp=row["timestamp"],
                type=row["type"],
                close_timestamp=row["close_timestamp"],
                close_type=row["close_type"],
                status=row["status"],
                config=json.loads(row["config"]),
                net_pnl_pct=row["net_pnl_pct"],
                net_pnl_quote=row["net_pnl_quote"],
                cum_fees_quote=row["cum_fees_quote"],
                filled_amount_quote=row["filled_amount_quote"],
                is_active=row["is_active"],
                is_trading=row["is_trading"],
                custom_info=json.loads(row["custom_info"]),
                controller_id=row["controller_id"],
                side=row["side"],
            ))
        return executor_values

    def insert_trade_fill(self, trade_fill):
        with self.engine.connect() as conn:
            for _, row in trade_fill.iterrows():
                ins = insert(self.trade_fill_table).values(
                    config_file_path=row["config_file_path"],
                    strategy=row["strategy"],
                    market=row["market"],
                    symbol=row["symbol"],
                    base_asset=row["base_asset"],
                    quote_asset=row["quote_asset"],
                    timestamp=row["timestamp"],
                    order_id=row["order_id"],
                    trade_type=row["trade_type"],
                    order_type=row["order_type"],
                    price=row["price"],
                    amount=row["amount"],
                    leverage=row["leverage"],
                    trade_fee=row["trade_fee"],
                    trade_fee_in_quote=row["trade_fee_in_quote"],
                    exchange_trade_id=row["exchange_trade_id"],
                    position=row["position"],
                )
                conn.execute(ins)
                conn.commit()

    def load_trade_fill(self):
        with self.session_maker() as session:
            query = "SELECT * FROM trades"
            trade_fill = pd.read_sql_query(text(query), session.connection())
            return trade_fill

    def insert_orders(self, orders):
        with self.engine.connect() as conn:
            for _, row in orders.iterrows():
                ins = insert(self.orders_table).values(
                    client_order_id=row["id"],
                    config_file_path=row["config_file_path"],
                    strategy=row["strategy"],
                    market=row["market"],
                    symbol=row["symbol"],
                    base_asset=row["base_asset"],
                    quote_asset=row["quote_asset"],
                    creation_timestamp=row["creation_timestamp"],
                    order_type=row["order_type"],
                    amount=row["amount"],
                    leverage=row["leverage"],
                    price=row["price"],
                    last_status=row["last_status"],
                    last_update_timestamp=row["last_update_timestamp"],
                    exchange_order_id=row["exchange_order_id"],
                    position=row["position"],
                )
                conn.execute(ins)
                conn.commit()

    def load_orders(self):
        with self.session_maker() as session:
            query = "SELECT * FROM orders"
            orders = pd.read_sql_query(text(query), session.connection())
            return orders

    @staticmethod
    def get_enum_by_value(enum_class, value):
        for member in enum_class:
            if member.value == value:
                return member
        raise ValueError(f"No enum member with value {value}")
