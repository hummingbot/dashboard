import pandas as pd
from typing import List
import os

from utils.sqlite_manager import SQLiteManager
from utils.os_utils import get_bots_data_paths


class DatabaseOrchestrator:
    def __init__(self):
        pass

    @property
    def dbs_map(self):
        return self.get_dbs_map()

    @property
    def status_report(self):
        return self.get_status_report()

    @property
    def dbs(self) -> List[SQLiteManager]:
        return self.get_databases()

    @property
    def healthy_dbs(self) -> List[SQLiteManager]:
        return [db for db in self.dbs if db.status["general_status"]]

    @property
    def db_names(self):
        return [os.path.basename(db.db_path) for db in self.healthy_dbs]

    @staticmethod
    def get_dbs_map():
        databases = {}
        bots_data_paths = get_bots_data_paths()
        for source_name, source_path in bots_data_paths.items():
            sqlite_files = {}
            for db_name in os.listdir(source_path):
                if db_name.endswith(".sqlite"):
                    sqlite_files[db_name] = os.path.join(source_path, db_name)
            databases[source_name] = sqlite_files
        if len(databases) > 0:
            return {key: value for key, value in databases.items() if value}
        else:
            return None

    def get_databases(self):
        dbs_map = self.get_dbs_map() or {}
        dbs = []
        for source, db_files in dbs_map.items():
            for db_name, db_path in db_files.items():
                dbs.append(SQLiteManager(db_path=db_path, instance_name=source))
        return dbs

    def get_status_report(self):
        dbs_status = [db.status for db in self.get_databases()]
        if len(dbs_status) == 0:
            return pd.DataFrame()
        return pd.DataFrame(dbs_status).sort_values(by="general_status", ascending=False)

    def get_tables(self, selected_dbs=List[str]):
        healthy_dbs = [db for db in self.dbs if db.db_path in selected_dbs]
        trade_fill = pd.DataFrame()
        orders = pd.DataFrame()
        order_status = pd.DataFrame()
        market_data = pd.DataFrame()
        executors = pd.DataFrame()
        for db in healthy_dbs:
            new_trade_fill = db.get_trade_fills()
            new_trade_fill["instance"] = db.instance_name
            new_trade_fill["db_path"] = db.db_path
            new_trade_fill["db_name"] = db.db_name

            new_orders = db.get_orders()
            new_orders["instance"] = db.instance_name
            new_orders["db_path"] = db.db_path
            new_orders["db_name"] = db.db_name

            new_order_status = db.get_order_status()
            new_order_status["instance"] = db.instance_name
            new_order_status["db_path"] = db.db_path
            new_order_status["db_name"] = db.db_name

            new_market_data = db.get_market_data()
            new_market_data["instance"] = db.instance_name
            new_market_data["db_path"] = db.db_path
            new_market_data["db_name"] = db.db_name

            new_executors = db.get_executors_data()
            new_executors["instance"] = db.instance_name
            new_executors["db_path"] = db.db_path
            new_executors["db_name"] = db.db_name

            trade_fill = pd.concat([trade_fill, new_trade_fill])
            orders = pd.concat([orders, new_orders])
            order_status = pd.concat([order_status, new_order_status])
            market_data = pd.concat([market_data, new_market_data])
            executors = pd.concat([executors, new_executors])
        return {"trade_fill": trade_fill, "orders": orders, "order_status": order_status, "market_data": market_data, "executors": executors}
