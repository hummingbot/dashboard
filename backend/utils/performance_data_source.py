import json
from typing import Any, Dict, List

import pandas as pd
from hummingbot.core.data_type.common import TradeType
from hummingbot.strategy_v2.models.base import RunnableStatus
from hummingbot.strategy_v2.models.executors import CloseType
from hummingbot.strategy_v2.models.executors_info import ExecutorInfo


class PerformanceDataSource:
    def __init__(self,
                 checkpoint_data: Dict[str, Any]):
        self.checkpoint_data = checkpoint_data
        self.executors_dict = self.checkpoint_data["executors"].copy()
        self.orders = self.load_orders()
        self.controllers_df = self.load_controllers()
        self.executors_with_orders = self.get_executors_with_orders(self.get_executors_df(), self.orders)

    def load_orders(self):
        """
        Load the orders data from the checkpoint.
        """
        orders = self.checkpoint_data["orders"].copy()
        orders = pd.DataFrame(orders)
        return orders

    def load_trade_fill(self):
        trade_fill = self.checkpoint_data["trade_fill"].copy()
        trade_fill = pd.DataFrame(trade_fill)
        trade_fill["timestamp"] = trade_fill["timestamp"].apply(lambda x: self.ensure_timestamp_in_seconds(x))
        trade_fill["datetime"] = pd.to_datetime(trade_fill.timestamp, unit="s")
        return trade_fill

    def load_controllers(self):
        controllers = self.checkpoint_data["controllers"].copy()
        controllers = pd.DataFrame(controllers)
        controllers["config"] = controllers["config"].apply(lambda x: json.loads(x))
        controllers["datetime"] = pd.to_datetime(controllers.timestamp, unit="s")
        return controllers

    @property
    def controllers_dict(self):
        return {controller["id"]: controller["config"] for controller in self.controllers_df.to_dict(orient="records")}

    def get_executors_df(self, executors_filter: Dict[str, Any] = None, apply_executor_data_types: bool = False):
        executors_df = pd.DataFrame(self.executors_dict)
        executors_df["custom_info"] = executors_df["custom_info"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else x
        )
        executors_df["config"] = executors_df["config"].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
        executors_df["timestamp"] = executors_df["timestamp"].apply(lambda x: self.ensure_timestamp_in_seconds(x))
        executors_df["close_timestamp"] = executors_df["close_timestamp"].apply(
            lambda x: self.ensure_timestamp_in_seconds(x)
        )
        executors_df.sort_values("close_timestamp", inplace=True)
        executors_df["trading_pair"] = executors_df["config"].apply(lambda x: x["trading_pair"])
        executors_df["exchange"] = executors_df["config"].apply(lambda x: x["connector_name"])
        executors_df["status"] = executors_df["status"].astype(int)
        executors_df["level_id"] = executors_df["config"].apply(
            lambda x: x.get("level_id") if x.get("level_id") is not None else 0)
        executors_df["bep"] = executors_df["custom_info"].apply(lambda x: x["current_position_average_price"])
        executors_df["order_ids"] = executors_df["custom_info"].apply(lambda x: x.get("order_ids"))
        executors_df["close_price"] = executors_df["custom_info"].apply(lambda x: x["close_price"])
        executors_df["sl"] = executors_df["config"].apply(lambda x: x["stop_loss"]).fillna(0)
        executors_df["tp"] = executors_df["config"].apply(lambda x: x["take_profit"]).fillna(0)
        executors_df["tl"] = executors_df["config"].apply(lambda x: x["time_limit"]).fillna(0)
        executors_df["close_type_name"] = executors_df["close_type"].apply(lambda x: self.get_enum_by_value(CloseType, x).name)

        controllers = self.controllers_df.copy()
        controllers.drop(columns=["controller_id"], inplace=True)
        controllers.rename(columns={
            "config": "controller_config",
            "type": "controller_type",
            "id": "controller_id"
        }, inplace=True)

        executors_df = executors_df.merge(controllers[["controller_id", "controller_type", "controller_config"]],
                                          on="controller_id", how="left")
        if apply_executor_data_types:
            executors_df = self.apply_executor_data_types(executors_df)
        if executors_filter is not None:
            executors_df = self.filter_executors(executors_df, executors_filter)
        return executors_df

    def apply_executor_data_types(self, executors):
        executors["status"] = executors["status"].apply(lambda x: self.get_enum_by_value(RunnableStatus, int(x)))
        executors["side"] = executors["config"].apply(lambda x: self.get_enum_by_value(TradeType, int(x["side"])))
        executors["close_type"] = executors["close_type"].apply(lambda x: self.get_enum_by_value(CloseType, int(x)))
        executors["datetime"] = pd.to_datetime(executors.timestamp, unit="s")
        executors["close_datetime"] = pd.to_datetime(executors["close_timestamp"], unit="s")
        return executors

    @staticmethod
    def remove_executor_data_types(executors):
        executors["status"] = executors["status"].apply(lambda x: x.value)
        executors["side"] = executors["side"].apply(lambda x: x.value)
        executors["close_type"] = executors["close_type"].apply(lambda x: x.value)
        executors.drop(columns=["datetime", "close_datetime"], inplace=True)
        return executors

    @staticmethod
    def get_executors_with_orders(executors_df: pd.DataFrame, orders: pd.DataFrame):
        df = (executors_df[["id", "order_ids"]]
              .rename(columns={"id": "executor_id", "order_ids": "order_id"})
              .explode("order_id"))
        exec_with_orders = df.merge(orders, left_on="order_id", right_on="client_order_id", how="inner")
        exec_with_orders = exec_with_orders[exec_with_orders["last_status"].isin(["SellOrderCompleted",
                                                                                  "BuyOrderCompleted"])]
        return exec_with_orders[["executor_id", "order_id", "last_status", "last_update_timestamp",
                                 "price", "amount", "position"]]

    def get_executor_info_list(self,
                               executors_filter: Dict[str, Any] = None) -> List[ExecutorInfo]:
        required_columns = [
            "id", "timestamp", "type", "close_timestamp", "close_type", "status", "controller_type",
            "net_pnl_pct", "net_pnl_quote", "cum_fees_quote", "filled_amount_quote",
            "is_active", "is_trading", "controller_id", "side", "config", "custom_info", "exchange", "trading_pair"
        ]
        executors_df = self.get_executors_df(executors_filter=executors_filter,
                                             apply_executor_data_types=True
                                             )[required_columns].copy()
        executors_df = executors_df[executors_df["net_pnl_quote"] != 0]
        executor_info_list = executors_df.apply(lambda row: ExecutorInfo(**row.to_dict()), axis=1).tolist()
        return executor_info_list

    def get_executor_dict(self,
                          executors_filter: Dict[str, Any] = None,
                          apply_executor_data_types: bool = False,
                          remove_special_fields: bool = False) -> List[dict]:
        executors_df = self.get_executors_df(executors_filter,
                                             apply_executor_data_types=apply_executor_data_types).copy()
        if remove_special_fields:
            executors_df = self.remove_executor_data_types(executors_df)
        return executors_df.to_dict(orient="records")

    def get_executors_by_controller_type(self,
                                         executors_filter: Dict[str, Any] = None) -> Dict[str, pd.DataFrame]:
        executors_by_controller_type = {}
        executors_df = self.get_executors_df(executors_filter).copy()
        for controller_type in executors_df["controller_type"].unique():
            executors_by_controller_type[controller_type] = executors_df[
                executors_df["controller_type"] == controller_type
            ]
        return executors_by_controller_type

    @staticmethod
    def filter_executors(executors_df: pd.DataFrame,
                         filters: Dict[str, List[Any]]):
        filter_condition = [True] * len(executors_df)
        for key, value in filters.items():
            if isinstance(value, list) and len(value) > 0:
                filter_condition &= (executors_df[key].isin(value))
            elif key == "start_time":
                filter_condition &= pd.Series((executors_df["timestamp"] >= value - 60))
            elif key == "close_type_name":
                filter_condition &= pd.Series((executors_df["close_type_name"] == value))
            elif key == "end_time":
                filter_condition &= pd.Series((executors_df["close_timestamp"] <= value + 60))
        return executors_df[filter_condition]

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
                "Timestamp is not in a recognized format. Must be in seconds, milliseconds, microseconds or "
                "nanoseconds.")
