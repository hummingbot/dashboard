import datetime
from dataclasses import dataclass
import pandas as pd


@dataclass
class StrategyData:
    orders: pd.DataFrame
    order_status: pd.DataFrame
    trade_fill: pd.DataFrame
    config_file_name: str

    def __post_init__(self):
        self.trade_fill["net_amount"] = self.trade_fill['amount'] * self.trade_fill['trade_type'].apply(lambda x: 1 if x == 'BUY' else -1)
        self.trade_fill["net_amount_quote"] = self.trade_fill['net_amount'] * self.trade_fill['price']
        self.trade_fill["cum_net_amount"] = self.trade_fill["net_amount"].cumsum()
        self.trade_fill["unrealized_trade_pnl"] = -1 * self.trade_fill["net_amount_quote"].cumsum()
        self.trade_fill["inventory_cost"] = self.trade_fill["cum_net_amount"] * self.trade_fill["price"]
        self.trade_fill["realized_trade_pnl"] = self.trade_fill["unrealized_trade_pnl"] + self.trade_fill["inventory_cost"]

    def get_filtered_strategy_data(self, start_time: datetime.datetime, end_time: datetime.datetime):
        trade_fill = self.trade_fill[(self.trade_fill["timestamp"] >= start_time) & (self.trade_fill["timestamp"] <= end_time)]
        order_status = self.order_status[self.order_status["order_id"].isin(trade_fill["order_id"])].copy()
        orders = self.orders[self.orders["id"].isin(trade_fill["order_id"])].copy()
        return StrategyData(
            orders=orders,
            order_status=order_status,
            trade_fill=trade_fill,
            config_file_name=self.config_file_name
        )

    @property
    def market(self):
        return self.trade_fill["market"].unique()[0].split("_")[0]

    @property
    def symbol(self):
        return self.trade_fill["symbol"].unique()[0]

    @property
    def start_time(self):
        return self.orders["creation_timestamp"].min()

    @property
    def end_time(self):
        return self.orders["last_update_timestamp"].max()

    @property
    def duration_minutes(self):
        return (self.end_time - self.start_time).seconds / 60

    @property
    def start_price(self):
        return self.trade_fill["price"].iat[0]

    @property
    def end_price(self):
        return self.trade_fill["price"].iat[-1]

    @property
    def buys(self):
        return self.trade_fill[self.trade_fill["trade_type"] == "BUY"]

    @property
    def sells(self):
        return self.trade_fill[self.trade_fill["trade_type"] == "SELL"]

    @property
    def total_buy_amount(self):
        return self.buys["amount"].sum()

    @property
    def total_sell_amount(self):
        return self.sells["amount"].sum()

    @property
    def total_buy_trades(self):
        return self.buys["amount"].count()

    @property
    def total_sell_trades(self):
        return self.sells["amount"].count()


    @property
    def trade_pnl_usd(self):
        # TODO: Review logic
        buy_volume = self.buys["amount"].sum() * self.average_buy_price
        sell_volume = self.sells["amount"].sum() * self.average_sell_price
        inventory_change_volume = self.inventory_change_base_asset * self.end_price
        return sell_volume - buy_volume + inventory_change_volume

    @property
    def inventory_change_base_asset(self):
        return self.total_buy_amount - self.total_sell_amount

    @property
    def total_orders(self):
        return self.total_buy_trades + self.total_sell_trades

    @property
    def average_buy_price(self):
        average_price = (self.buys["price"] * self.buys["amount"]).sum() / self.total_buy_amount
        return average_price

    @property
    def average_sell_price(self):
        average_price = (self.sells["price"] * self.sells["amount"]).sum() / self.total_sell_amount
        return average_price

    @property
    def price_change(self):
        return (self.end_price - self.start_price) / self.start_price


@dataclass
class BotData:
    orders: pd.DataFrame
    order_status: pd.DataFrame
    trade_fill: pd.DataFrame

    def get_strategy_data(self, config_file_name: str):
        orders_filtered = self.orders[self.orders["config_file_path"] == config_file_name].copy()
        order_status_filtered = self.order_status[
            self.order_status["order_id"].isin(orders_filtered["id"])].copy()
        trade_fill_filtered = self.trade_fill[self.trade_fill["config_file_path"] == config_file_name].copy()
        return StrategyData(orders_filtered, order_status_filtered, trade_fill_filtered, config_file_name)

    @property
    def start_time(self):
        return self.orders["creation_timestamp"].min()

    @property
    def end_time(self):
        return self.orders["last_update_timestamp"].max()

    @property
    def duration_minutes(self):
        return (self.end_time - self.start_time).seconds / 60