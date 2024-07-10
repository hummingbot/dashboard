import json
from typing import List, Dict, Any

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
                 checkpoint_data: Dict[str, Any]):
        self.checkpoint_data = checkpoint_data
        self.executors = self.load_executors()
        self.orders = self.load_orders()
        self.executors_with_orders = self.get_executors_with_orders(self.executors, self.orders)

    def load_executors(self):
        executors = self.checkpoint_data["executor"].copy()
        executors = pd.DataFrame(executors)
        executors["timestamp"] = executors["timestamp"].apply(lambda x: self.ensure_timestamp_in_seconds(x))
        executors["close_timestamp"] = executors["close_timestamp"].apply(lambda x: self.ensure_timestamp_in_seconds(x))
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
    def parse_executors(executors: pd.DataFrame) -> List[ExecutorInfo]:
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

    @staticmethod
    def dump_executors(executors: List[ExecutorInfo]) -> List[dict]:
        executor_values = []
        for executor in executors:
            executor_to_append = {
                "id": executor.id,
                "timestamp": executor.timestamp,
                "type": executor.type,
                "close_timestamp": executor.close_timestamp,
                "close_type": executor.close_type.value,
                "status": executor.status.value,
                "config": executor.config.dict(),
                "net_pnl_pct": executor.net_pnl_pct,
                "net_pnl_quote": executor.net_pnl_quote,
                "cum_fees_quote": executor.cum_fees_quote,
                "filled_amount_quote": executor.filled_amount_quote,
                "is_active": executor.is_active,
                "is_trading": executor.is_trading,
                "custom_info": json.dumps(executor.custom_info),
                "controller_id": executor.controller_id,
                "side": executor.side,
            }
            executor_to_append["config"]["mode"] = executor_to_append["config"]["mode"].value
            executor_to_append["config"]["side"] = executor_to_append["config"]["side"].value
            executor_values.append(executor_to_append)
        return executor_values

    def load_trade_fill(self):
        trade_fill = self.checkpoint_data["trade_fill"].copy()
        trade_fill = pd.DataFrame(trade_fill)
        trade_fill["timestamp"] = trade_fill["timestamp"].apply(lambda x: self.ensure_timestamp_in_seconds(x))
        trade_fill["datetime"] = pd.to_datetime(trade_fill.timestamp, unit="s")
        return trade_fill

    def load_orders(self):
        orders = self.checkpoint_data["order"].copy()
        orders = pd.DataFrame(orders)
        return orders

    @staticmethod
    def get_executors_with_orders(executors, orders):
        df = pd.DataFrame(executors['custom_info'].tolist(), index=executors['id'],
                          columns=["custom_info"]).reset_index()
        df["custom_info"] = df["custom_info"].apply(lambda x: json.loads(x))
        df["orders"] = df["custom_info"].apply(lambda x: x["order_ids"])
        df.rename(columns={"id": "executor_id"}, inplace=True)
        exploded_df = df.explode("orders").rename(columns={"orders": "order_id"})
        exec_with_orders = exploded_df.merge(orders, left_on="order_id", right_on="client_order_id", how="inner")
        exec_with_orders = exec_with_orders[exec_with_orders["last_status"].isin(["SellOrderCompleted", "BuyOrderCompleted"])]
        return exec_with_orders[["executor_id", "order_id", "last_status", "last_update_timestamp", "price", "amount", "position"]]

    @staticmethod
    def get_enum_by_value(enum_class, value):
        for member in enum_class:
            if member.value == value:
                return member
        raise ValueError(f"No enum member with value {value}")

    @staticmethod
    def ensure_timestamp_in_seconds(timestamp: float) -> float:
        """
        Ensure the given timestamp is in seconds.

        Args:
        - timestamp (int): The input timestamp which could be in seconds, milliseconds, or microseconds.

        Returns:
        - int: The timestamp in seconds.

        Raises:
        - ValueError: If the timestamp is not in a recognized format.
        """
        timestamp_int = int(float(timestamp))
        if timestamp_int >= 1e18:  # Nanoseconds
            return timestamp_int / 1e9
        elif timestamp_int >= 1e15:  # Microseconds
            return timestamp_int / 1e6
        elif timestamp_int >= 1e12:  # Milliseconds
            return timestamp_int / 1e3
        elif timestamp_int >= 1e9:  # Seconds
            return timestamp_int
        else:
            raise ValueError(
                "Timestamp is not in a recognized format. Must be in seconds, milliseconds, microseconds or nanoseconds.")
