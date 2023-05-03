import datetime
from dataclasses import dataclass
import pandas as pd


@dataclass
class StrategyData:
    orders: pd.DataFrame
    order_status: pd.DataFrame
    trade_fill: pd.DataFrame

    def get_single_market_strategy_data(self, exchange: str, trading_pair: str):
        orders = self.orders[(self.orders["market"] == exchange) & (self.orders["symbol"] == trading_pair)].copy()
        trade_fill = self.trade_fill[self.trade_fill["order_id"].isin(orders["id"])].copy()
        order_status = self.order_status[self.order_status["order_id"].isin(orders["id"])].copy()
        return SingleMarketStrategyData(
            exchange=exchange,
            trading_pair=trading_pair,
            orders=orders,
            order_status=order_status,
            trade_fill=trade_fill,
        )

    @property
    def exchanges(self):
        return self.trade_fill["market"].unique()

    @property
    def trading_pairs(self):
        return self.trade_fill["symbol"].unique()

    @property
    def start_time(self):
        return self.orders["creation_timestamp"].min()

    @property
    def end_time(self):
        return self.orders["last_update_timestamp"].max()

    @property
    def duration_seconds(self):
        return (self.end_time - self.start_time).total_seconds()

    @property
    def buys(self):
        return self.trade_fill[self.trade_fill["trade_type"] == "BUY"]

    @property
    def sells(self):
        return self.trade_fill[self.trade_fill["trade_type"] == "SELL"]

    @property
    def total_buy_trades(self):
        return self.buys["amount"].count()

    @property
    def total_sell_trades(self):
        return self.sells["amount"].count()

    @property
    def total_orders(self):
        return self.total_buy_trades + self.total_sell_trades


@dataclass
class SingleMarketStrategyData:
    exchange: str
    trading_pair: str
    orders: pd.DataFrame
    order_status: pd.DataFrame
    trade_fill: pd.DataFrame

    def get_filtered_strategy_data(self, start_date: datetime.datetime, end_date: datetime.datetime):
        orders = self.orders[(self.orders["creation_timestamp"] >= start_date) & (self.orders["creation_timestamp"] <= end_date)].copy()
        trade_fill = self.trade_fill[self.trade_fill["order_id"].isin(orders["id"])].copy()
        order_status = self.order_status[self.order_status["order_id"].isin(orders["id"])].copy()
        return SingleMarketStrategyData(
            exchange=self.exchange,
            trading_pair=self.trading_pair,
            orders=orders,
            order_status=order_status,
            trade_fill=trade_fill,
        )

    @property
    def start_time(self):
        return self.orders["creation_timestamp"].min()

    @property
    def end_time(self):
        return self.orders["last_update_timestamp"].max()

    @property
    def duration_seconds(self):
        return (self.end_time - self.start_time).total_seconds()

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

    @property
    def trade_pnl_usd(self):
        buy_volume = self.buys["amount"].sum() * self.average_buy_price
        sell_volume = self.sells["amount"].sum() * self.average_sell_price
        inventory_change_volume = self.inventory_change_base_asset * self.end_price
        return sell_volume - buy_volume + inventory_change_volume

    @property
    def inventory_change_base_asset(self):
        return self.total_buy_amount - self.total_sell_amount
