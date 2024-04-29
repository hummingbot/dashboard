from sqlalchemy import create_engine, delete, insert, text, inspect, MetaData, Table, Column, VARCHAR, INT, FLOAT, TIMESTAMP,  Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import OperationalError

import pandas as pd


class ETLPerformance:
    def __init__(self,
                 host: str,
                 port: int,
                 database: str,
                 user: str,
                 password: str):
        self.engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
        self.session_maker = sessionmaker(bind=self.engine)

    @property
    def market_data_table(self):
        return Table(
            'market_data', MetaData(),
            Column('timestamp', TIMESTAMP),
            Column('trading_pair', VARCHAR),
            Column('exchange', VARCHAR),
            Column('mid_price', FLOAT),
            Column('best_bid', FLOAT),
            Column('best_ask', FLOAT),
            Column('order_book', JSONB),
            Column('instance', VARCHAR),
            Column('db_path', VARCHAR),
            Column('db_name', VARCHAR)
        )

    @property
    def executors_table(self):
        return Table('executors',
                     MetaData(),
               Column('id', Integer),
                     Column('type', String),
                     Column('close_type', String),
                     Column('level_id', Integer),
                     Column('close_timestamp', DateTime),
                     Column('status', String),
                     Column('config', String),
                     Column('net_pnl_pct', Float),
                     Column('net_pnl_quote', Float),
                     Column('cum_fees_quote', Float),
                     Column('filled_amount_quote', Float),
                     Column('is_active', Integer),
                     Column('is_trading', Integer),
                     Column('custom_info', String),
                     Column('controller_id', Integer),
                     Column('datetime', DateTime),
                     Column('close_datetime', DateTime),
                     Column('cum_net_pnl_quote', Float),
                     Column('cum_filled_amount_quote', Float),
                     Column('trading_pair', String),
                     Column('exchange', String),
                     Column('side', String),
                     Column('bep', Float),
                     Column('close_price', Float),
                     Column('sl', Float),
                     Column('tp', Float),
                     Column('tl', Float),
                     Column('instance', String),
                     Column('db_path', String),
                     Column('db_name', String))

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
            Column('trade_fee', FLOAT),
            Column('trade_fee_in_quote', FLOAT),
            Column('exchange_trade_id', VARCHAR(255)),
            Column('position', VARCHAR(255)),
            Column('cum_fees_in_quote', FLOAT),
            Column('net_amount', FLOAT),
            Column('net_amount_quote', FLOAT),
            Column('cum_net_amount', FLOAT),
            Column('unrealized_trade_pnl', FLOAT),
            Column('inventory_cost', FLOAT),
            Column('realized_trade_pnl', FLOAT),
            Column('net_realized_pnl', FLOAT),
            Column('realized_pnl', FLOAT),
            Column('gross_pnl', FLOAT),
            Column('quote_volume', FLOAT),
            Column('instance', VARCHAR(255)),
            Column('db_path', VARCHAR(255)),
            Column('db_name', VARCHAR(255)))

    @property
    def orders_table(self):
        return Table(
            'orders', MetaData(),
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
            Column('instance', VARCHAR(255)),
            Column('db_path', VARCHAR(255)),
            Column('db_name', VARCHAR(255))
        )

    def test_connection(self):
        try:
            with self.engine.connect():
                pass  # If the connection is successful, do nothing
        except OperationalError as e:
            raise e

    def list_tables(self):
        with self.session_maker() as session:
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            tables = pd.read_sql_query(text(query), session.connection())
            return [table[0] for table in tables]

    def clean_tables(self):
        self.clean_orders()
        self.clean_trade_fill()
        self.clean_market_data()
        self.clean_executors()

    def create_tables(self):
        self.create_orders_table()
        self.create_executors_table()
        self.create_market_data_table()
        self.create_trade_fill_table()

    def drop_tables(self):
        with self.engine.connect() as conn:
            conn.execute("DROP TABLE IF EXISTS executors")
            conn.execute("DROP TABLE IF EXISTS market_data")
            conn.execute("DROP TABLE IF EXISTS trades")
            conn.execute("DROP TABLE IF EXISTS orders")

    def insert_data(self, data):
        if "executors" in data:
            self.insert_executors(data["executors"])
        if "market_data" in data:
            self.insert_market_data(data["market_data"])
        if "trade_fill" in data:
            self.insert_trade_fill(data["trade_fill"])
        if "orders" in data:
            self.insert_orders(data["orders"])

    def create_executors_table(self):
        inspector = inspect(self.engine)
        if 'executors' not in inspector.get_table_names():
            with self.engine.connect() as conn:
                self.executors_table.create(conn)
                conn.commit()

    def insert_executors(self, executors):
        with self.engine.connect() as conn:
            for _, row in executors.iterrows():
                ins = self.executors_table.insert().values(
                    id=row["id"],
                    type=row["type"],
                    close_type=row["close_type"],
                    level_id=row["level_id"],
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
                    controller_id=row["controller_id"],
                    datetime=row["datetime"],
                    close_datetime=row["close_datetime"],
                    cum_net_pnl_quote=row["cum_net_pnl_quote"],
                    cum_filled_amount_quote=row["cum_filled_amount_quote"],
                    trading_pair=row["trading_pair"],
                    exchange=row["exchange"],
                    side=row["side"],
                    bep=row["bep"],
                    close_price=row["close_price"],
                    sl=row["sl"],
                    tp=row["tp"],
                    tl=row["tl"],
                    instance=row["instance"],
                    db_path=row["db_path"],
                    db_name=row["db_name"]
                )
                conn.execute(ins)
                conn.commit()

    def read_executors(self):
        with self.session_maker() as session:
            query = "SELECT * FROM executors"
            executors = pd.read_sql_query(text(query), session.connection())
            return executors

    def clean_executors(self):
        stmt = delete(self.executors_table)
        with self.engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()

    def create_market_data_table(self):
        inspector = inspect(self.engine)
        if 'executors' not in inspector.get_table_names():
            with self.engine.connect() as conn:
                self.market_data_table.create(conn)
                conn.commit()

    def insert_market_data(self, market_data):
        market_data.reset_index(inplace=True)
        with self.engine.connect() as conn:
            for _, row in market_data.iterrows():
                ins = insert(self.market_data_table).values(
                    timestamp=row["timestamp"],
                    trading_pair=row["trading_pair"],
                    exchange=row["exchange"],
                    mid_price=row["mid_price"],
                    best_bid=row["best_bid"],
                    best_ask=row["best_ask"],
                    order_book=row["order_book"],
                    instance=row["instance"],
                    db_path=row["db_path"],
                    db_name=row["db_name"]
                )
                conn.execute(ins)
                conn.commit()

    def read_market_data(self):
        with self.session_maker() as session:
            query = "SELECT * FROM market_data"
            market_data = pd.read_sql_query(text(query), session.connection())
            return market_data

    def clean_market_data(self):
        stmt = delete(self.market_data_table)
        with self.engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()

    def create_trade_fill_table(self):
        inspector = inspect(self.engine)
        if 'trades' not in inspector.get_table_names():
            with self.engine.connect() as conn:
                self.trade_fill_table.create(conn)
                conn.commit()

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
                    cum_fees_in_quote=row["cum_fees_in_quote"],
                    net_amount=row["net_amount"],
                    net_amount_quote=row["net_amount_quote"],
                    cum_net_amount=row["cum_net_amount"],
                    unrealized_trade_pnl=row["unrealized_trade_pnl"],
                    inventory_cost=row["inventory_cost"],
                    realized_trade_pnl=row["realized_trade_pnl"],
                    net_realized_pnl=row["net_realized_pnl"],
                    realized_pnl=row["realized_pnl"],
                    gross_pnl=row["gross_pnl"],
                    quote_volume=row["quote_volume"],
                    instance=row["instance"],
                    db_path=row["db_path"],
                    db_name=row["db_name"]
                )
                conn.execute(ins)
                conn.commit()

    def read_trade_fill(self):
        with self.session_maker() as session:
            query = "SELECT * FROM trades"
            trade_fill = pd.read_sql_query(text(query), session.connection())
            return trade_fill

    def clean_trade_fill(self):
        stmt = delete(self.trade_fill_table)
        with self.engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()

    def create_orders_table(self):
        inspector = inspect(self.engine)
        if 'executors' not in inspector.get_table_names():
            with self.engine.connect() as conn:
                self.orders_table.create(conn)
                conn.commit()

    def insert_orders(self, orders):
        with self.engine.connect() as conn:
            for _, row in orders.iterrows():
                ins = insert(self.orders_table).values(
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
                    instance=row["instance"],
                    db_path=row["db_path"],
                    db_name=row["db_name"]
                )
                conn.execute(ins)
                conn.commit()

    def read_orders(self):
        with self.session_maker() as session:
            query = "SELECT * FROM orders"
            orders = pd.read_sql_query(text(query), session.connection())
            return orders

    def clean_orders(self):
        stmt = delete(self.orders_table)
        with self.engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()
