import psycopg2
import pandas as pd


class PostgresConnector:
    def __init__(self,
                 host: str,
                 port: int,
                 database: str,
                 user: str,
                 password: str):
        self.conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )

    def list_tables(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = cursor.fetchall()
            return [table[0] for table in tables]

    def clean_tables(self):
        self.clean_orders()
        self.clean_trade_fill()
        self.clean_market_data()
        self.clean_executors()

    def create_tables(self):
        self.create_executors_table()
        self.create_market_data_table()
        self.create_trade_fill_table()
        self.create_orders_table()

    def drop_tables(self):
        with self.conn.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS executors")
            cursor.execute("DROP TABLE IF EXISTS market_data")
            cursor.execute("DROP TABLE IF EXISTS trades")
            cursor.execute("DROP TABLE IF EXISTS orders")
            self.conn.commit()

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
        with self.conn.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS executors (
                    id VARCHAR(255),
                    type VARCHAR(255),
                    close_type VARCHAR(255),
                    close_timestamp INT,
                    status INT,
                    level_id VARCHAR(255),
                    config JSONB,
                    net_pnl_pct FLOAT,
                    net_pnl_quote FLOAT,
                    cum_fees_quote FLOAT,
                    filled_amount_quote FLOAT,
                    is_active INT,
                    is_trading INT,
                    custom_info JSONB,
                    controller_id VARCHAR(255),
                    datetime TIMESTAMP,
                    close_datetime TIMESTAMP,
                    cum_net_pnl_quote FLOAT,
                    cum_filled_amount_quote FLOAT,
                    trading_pair VARCHAR(255),
                    exchange VARCHAR(255),
                    side INT,
                    bep FLOAT,
                    close_price FLOAT,
                    sl FLOAT,
                    tp INT,
                    tl INT,
                    instance VARCHAR(255),
                    db_path VARCHAR(255),
                    db_name VARCHAR(255)
                );
            """)
            self.conn.commit()

    def insert_executors(self, executors):
        with self.conn.cursor() as cursor:
            for _, row in executors.iterrows():
                cursor.execute("""
                    INSERT INTO executors (id, type, close_type, level_id, close_timestamp, status, config, net_pnl_pct, net_pnl_quote, cum_fees_quote, filled_amount_quote, is_active, is_trading, custom_info, controller_id, datetime, close_datetime, cum_net_pnl_quote, cum_filled_amount_quote, trading_pair, exchange, side, bep, close_price, sl, tp, tl, instance, db_path, db_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (row["id"], row["type"], row["close_type"], row["level_id"], row["close_timestamp"], row["status"], row["config"], row["net_pnl_pct"], row["net_pnl_quote"], row["cum_fees_quote"], row["filled_amount_quote"], row["is_active"], row["is_trading"], row["custom_info"], row["controller_id"], row["datetime"], row["close_datetime"], row["cum_net_pnl_quote"], row["cum_filled_amount_quote"], row["trading_pair"], row["exchange"], row["side"], row["bep"], row["close_price"], row["sl"], row["tp"], row["tl"], row["instance"], row["db_path"], row["db_name"]))
            self.conn.commit()

    def read_executors(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM executors")
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)

    def clean_executors(self):
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM executors")
            self.conn.commit()

    def create_market_data_table(self):
        with self.conn.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS market_data (
                    timestamp TIMESTAMP,
                    trading_pair VARCHAR,
                    exchange VARCHAR,
                    mid_price FLOAT,
                    best_bid FLOAT,
                    best_ask FLOAT,
                    order_book JSONB,
                    instance VARCHAR,
                    db_path VARCHAR,
                    db_name VARCHAR
                );
            """)
            self.conn.commit()

    def insert_market_data(self, market_data):
        market_data.reset_index(inplace=True)
        with self.conn.cursor() as cursor:
            for _, row in market_data.iterrows():
                cursor.execute("""
                    INSERT INTO market_data (timestamp, trading_pair, exchange, mid_price, best_bid, best_ask, order_book, instance, db_path, db_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (row["timestamp"], row["trading_pair"], row["exchange"], row["mid_price"], row["best_bid"], row["best_ask"], row["order_book"], row["instance"], row["db_path"], row["db_name"]))
            self.conn.commit()

    def read_market_data(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM market_data")
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)

    def clean_market_data(self):
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM market_data")
            self.conn.commit()

    def create_trade_fill_table(self):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    config_file_path VARCHAR(255),
                    strategy VARCHAR(255),
                    market VARCHAR(255),
                    symbol VARCHAR(255),
                    base_asset VARCHAR(255),
                    quote_asset VARCHAR(255),
                    timestamp TIMESTAMP,
                    order_id VARCHAR(255),
                    trade_type VARCHAR(255),
                    order_type VARCHAR(255),
                    price FLOAT,
                    amount FLOAT,
                    leverage INT,
                    trade_fee FLOAT,
                    trade_fee_in_quote FLOAT,
                    exchange_trade_id VARCHAR(255),
                    position VARCHAR(255),
                    cum_fees_in_quote FLOAT,
                    net_amount FLOAT,
                    net_amount_quote FLOAT,
                    cum_net_amount FLOAT,
                    unrealized_trade_pnl FLOAT,
                    inventory_cost FLOAT,
                    realized_trade_pnl FLOAT,
                    net_realized_pnl FLOAT,
                    realized_pnl FLOAT,
                    gross_pnl FLOAT,
                    quote_volume FLOAT,
                    instance VARCHAR(255),
                    db_path VARCHAR(255),
                    db_name VARCHAR(255)
                )
            """)

    def insert_trade_fill(self, trade_fill):
        with self.conn.cursor() as cursor:
            for _, row in trade_fill.iterrows():
                cursor.execute("""
                    INSERT INTO trades (config_file_path, strategy, market, symbol, base_asset, quote_asset, timestamp, order_id, trade_type, order_type, price, amount, leverage, trade_fee, trade_fee_in_quote, exchange_trade_id, position, cum_fees_in_quote, net_amount, net_amount_quote, cum_net_amount, unrealized_trade_pnl, inventory_cost, realized_trade_pnl, net_realized_pnl, realized_pnl, gross_pnl, quote_volume, instance, db_path, db_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (row["config_file_path"], row["strategy"], row["market"], row["symbol"], row["base_asset"], row["quote_asset"], row["timestamp"], row["order_id"], row["trade_type"], row["order_type"], row["price"], row["amount"], row["leverage"], row["trade_fee"], row["trade_fee_in_quote"], row["exchange_trade_id"], row["position"], row["cum_fees_in_quote"], row["net_amount"], row["net_amount_quote"], row["cum_net_amount"], row["unrealized_trade_pnl"], row["inventory_cost"], row["realized_trade_pnl"], row["net_realized_pnl"], row["realized_pnl"], row["gross_pnl"], row["quote_volume"], row["instance"], row["db_path"], row["db_name"]))
            self.conn.commit()

    def read_trade_fill(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM trades")
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)

    def clean_trade_fill(self):
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM trades")
            self.conn.commit()

    def create_orders_table(self):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    config_file_path VARCHAR(255),
                    strategy VARCHAR(255),
                    market VARCHAR(255),
                    symbol VARCHAR(255),
                    base_asset VARCHAR(255),
                    quote_asset VARCHAR(255),
                    creation_timestamp TIMESTAMP,
                    order_type VARCHAR(255),
                    amount FLOAT,
                    leverage INT,
                    price FLOAT,
                    last_status VARCHAR(255),
                    last_update_timestamp TIMESTAMP,
                    exchange_order_id VARCHAR(255),
                    position VARCHAR(255),
                    instance VARCHAR(255),
                    db_path VARCHAR(255),
                    db_name VARCHAR(255)
                )
            """)
            self.conn.commit()

    def insert_orders(self, orders):
        with self.conn.cursor() as cursor:
            for _, row in orders.iterrows():
                cursor.execute("""
                    INSERT INTO orders (config_file_path, strategy, market, symbol, base_asset, quote_asset, creation_timestamp, order_type, amount, leverage, price, last_status, last_update_timestamp, exchange_order_id, position, instance, db_path, db_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (row["config_file_path"], row["strategy"], row["market"], row["symbol"], row["base_asset"],
                          row["quote_asset"], row["creation_timestamp"], row["order_type"], row["amount"],
                          row["leverage"], row["price"], row["last_status"], row["last_update_timestamp"],
                          row["exchange_order_id"], row["position"], row["instance"], row["db_path"], row["db_name"]))
            self.conn.commit()

    def read_orders(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM orders")
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            return pd.DataFrame(data, columns=columns)

    def clean_orders(self):
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM orders")
            self.conn.commit()
