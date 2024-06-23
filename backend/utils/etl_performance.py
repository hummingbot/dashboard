import json

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
    def market_data_table(self):
        return Table(
            'market_data', MetaData(),
            Column('timestamp', TIMESTAMP),
            Column('trading_pair', VARCHAR),
            Column('exchange', VARCHAR),
            Column('mid_price', FLOAT),
            Column('best_bid', FLOAT),
            Column('best_ask', FLOAT),
            Column('order_book', VARCHAR),
            Column('instance', VARCHAR),
            Column('db_path', VARCHAR),
            Column('db_name', VARCHAR)
        )

    @property
    def executors_table(self):
        return Table('executors',
                     MetaData(),
                     Column('id', String),
                     Column('type', String),
                     Column('close_type', Integer),
                     Column('level_id', String),
                     Column('timestamp', Integer),
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
                     Column('controller_id', String),
                     Column('datetime', DateTime),
                     Column('close_datetime', DateTime),
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
            Column('instance', VARCHAR(255)),
            Column('db_path', VARCHAR(255)),
            Column('db_name', VARCHAR(255))
        )

    @property
    def tables(self):
        return [self.executors_table, self.market_data_table, self.trade_fill_table, self.orders_table]

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
        if "market_data" in data:
            self.insert_market_data(data["market_data"])
        if "trade_fill" in data:
            self.insert_trade_fill(data["trade_fill"])
        if "orders" in data:
            self.insert_orders(data["orders"])

    def insert_executors(self, executors):
        with self.engine.connect() as conn:
            for _, row in executors.iterrows():
                ins = self.executors_table.insert().values(
                    id=row["id"],
                    type=row["type"],
                    close_type=row["close_type"],
                    level_id=row["level_id"],
                    timestamp=row["timestamp"],
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

    def read_executors(self):
        with self.session_maker() as session:
            query = "SELECT * FROM executors"
            executors = pd.read_sql_query(text(query), session.connection())
            executors["close_datetime"] = pd.to_datetime(executors["close_datetime"])
            executors["datetime"] = pd.to_datetime(executors["timestamp"], unit="s")
            executors["close_type"] = executors["close_type"].apply(lambda x: self.get_enum_by_value(CloseType, int(x)))
            executors["close_type_name"] = executors["close_type"].apply(lambda x: x.name)
            executors["status"] = executors["status"].apply(lambda x: self.get_enum_by_value(RunnableStatus, int(x)))
            return executors

    @staticmethod
    def get_enum_by_value(enum_class, value):
        for member in enum_class:
            if member.value == value:
                return member
        raise ValueError(f"No enum member with value {value}")

    @staticmethod
    def _parse_executors(executors):
        """
        ExecutorInfo(id='2Qd1k5ALefhJ9kfeHYEE4THCG2HpX9ETvogg6rebpYfB', timestamp=1717763580.0, type='position_executor', close_timestamp=1717767240.0, close_type=<CloseType.TAKE_PROFIT: 3>, status=<RunnableStatus.TERMINATED: 4>, config=PositionExecutorConfig(id='2Qd1k5ALefhJ9kfeHYEE4THCG2HpX9ETvogg6rebpYfB', type='position_executor', timestamp=1717763580.0, controller_id='main', trading_pair='WLD-USDT', connector_name='kucoin', side=<TradeType.BUY: 1>, entry_price=Decimal('4.8345'), amount=Decimal('41.36932464577516'), triple_barrier_config=TripleBarrierConfig(stop_loss=Decimal('0.05'), take_profit=Decimal('0.02'), time_limit=43200, trailing_stop=TrailingStop(activation_price=Decimal('0.018'), trailing_delta=Decimal('0.002')), open_order_type=<OrderType.MARKET: 1>, take_profit_order_type=<OrderType.LIMIT: 2>, stop_loss_order_type=<OrderType.MARKET: 1>, time_limit_order_type=<OrderType.MARKET: 1>), leverage=20, activation_bounds=None, level_id=None), net_pnl_pct=Decimal('0.02072603164753395'), net_pnl_quote=Decimal('4.14520632950679'), cum_fees_quote=Decimal('0.1'), filled_amount_quote=Decimal('200'), is_active=False, is_trading=False, custom_info={'close_price': 4.9347, 'level_id': None, 'side': 1, 'current_position_average_price': 4.8345}, controller_id=None)
        """
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
                controller_id=row["controller_id"]
            ))
        return executor_values



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

    def read_market_data(self):
        with self.session_maker() as session:
            query = "SELECT * FROM market_data"
            market_data = pd.read_sql_query(text(query), session.connection())
            market_data["timestamp"] = pd.to_datetime(market_data["timestamp"])
            return market_data

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

    def read_trade_fill(self):
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
                    instance=row["instance"],
                    db_path=row["db_path"],
                    db_name=row["db_name"]
                )
                conn.execute(ins)

    def read_orders(self):
        with self.session_maker() as session:
            query = "SELECT * FROM orders"
            orders = pd.read_sql_query(text(query), session.connection())
            return orders
