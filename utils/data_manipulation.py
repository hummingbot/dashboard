import datetime
from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class StrategyData:
    orders: pd.DataFrame
    order_status: pd.DataFrame
    trade_fill: pd.DataFrame
    market_data: pd.DataFrame = None
    position_executor: pd.DataFrame = None

    @property
    def strategy_summary(self):
        if self.trade_fill is not None:
            return self.get_strategy_summary()
        else:
            return None

    def get_strategy_summary(self):
        columns_dict = {"strategy": "Strategy",
                        "market": "Exchange",
                        "symbol": "Trading Pair",
                        "order_id_count": "# Trades",
                        "total_positions": "# Positions",
                        "volume_sum": "Volume",
                        "TAKE_PROFIT": "# TP",
                        "STOP_LOSS": "# SL",
                        "TRAILING_STOP": "# TSL",
                        "TIME_LIMIT": "# TL",
                        "net_realized_pnl_full_series": "PnL Over Time",
                        "net_realized_pnl_last": "Realized PnL"}

        def full_series(series):
            return list(series)

        # Get trade fill data
        trade_fill_data = self.trade_fill.copy()
        trade_fill_data["volume"] = trade_fill_data["amount"] * trade_fill_data["price"]
        grouped_trade_fill = trade_fill_data.groupby(["strategy", "market", "symbol"]
                                                     ).agg({"order_id": "count",
                                                            "volume": "sum",
                                                            "net_realized_pnl": [full_series,
                                                                                 "last"]}).reset_index()
        grouped_trade_fill.columns = [f"{col[0]}_{col[1]}" if len(col[1]) > 0 else col[0] for col in grouped_trade_fill.columns]

        # Get position executor data
        if self.position_executor is not None:
            position_executor_data = self.position_executor.copy()
            grouped_executors = position_executor_data.groupby(["exchange", "trading_pair", "controller_name", "close_type"]).agg(metric_count=("close_type", "count")).reset_index()
            index_cols = ["exchange", "trading_pair", "controller_name"]
            pivot_executors = pd.pivot_table(grouped_executors, values="metric_count", index=index_cols, columns="close_type").reset_index()
            result_cols = ["TAKE_PROFIT", "STOP_LOSS", "TRAILING_STOP", "TIME_LIMIT"]
            pivot_executors = pivot_executors.reindex(columns=index_cols + result_cols, fill_value=0)
            pivot_executors["total_positions"] = pivot_executors[result_cols].sum(axis=1)
            strategy_summary = grouped_trade_fill.merge(pivot_executors, left_on=["market", "symbol"],
                                                        right_on=["exchange", "trading_pair"],
                                                        how="left")
            strategy_summary.drop(columns=["exchange", "trading_pair"], inplace=True)
        else:
            strategy_summary = grouped_trade_fill.copy()
            strategy_summary["TAKE_PROFIT"] = np.nan
            strategy_summary["STOP_LOSS"] = np.nan
            strategy_summary["TRAILING_STOP"] = np.nan
            strategy_summary["TIME_LIMIT"] = np.nan
            strategy_summary["total_positions"] = np.nan

        strategy_summary.rename(columns=columns_dict, inplace=True)
        strategy_summary.sort_values(["Realized PnL"], ascending=True, inplace=True)
        strategy_summary["Explore"] = False
        sorted_cols = ["Explore", "Strategy", "Exchange", "Trading Pair", "# Trades", "Volume", "# Positions",
                       "# TP", "# SL", "# TSL", "# TL", "PnL Over Time", "Realized PnL"]
        strategy_summary = strategy_summary.reindex(columns=sorted_cols, fill_value=0)
        return strategy_summary

    def get_single_market_strategy_data(self, exchange: str, trading_pair: str):
        orders = self.orders[(self.orders["market"] == exchange) & (self.orders["symbol"] == trading_pair)].copy()
        trade_fill = self.trade_fill[self.trade_fill["order_id"].isin(orders["id"])].copy()
        order_status = self.order_status[self.order_status["order_id"].isin(orders["id"])].copy()
        if self.market_data is not None:
            market_data = self.market_data[(self.market_data["exchange"] == exchange) &
                                           (self.market_data["trading_pair"] == trading_pair)].copy()
        else:
            market_data = None
        if self.position_executor is not None:
            position_executor = self.position_executor[(self.position_executor["exchange"] == exchange) &
                                                       (self.position_executor["trading_pair"] == trading_pair)].copy()
        else:
            position_executor = None
        return SingleMarketStrategyData(
            exchange=exchange,
            trading_pair=trading_pair,
            orders=orders,
            order_status=order_status,
            trade_fill=trade_fill,
            market_data=market_data,
            position_executor=position_executor
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
    market_data: pd.DataFrame = None
    position_executor: pd.DataFrame = None

    def get_filtered_strategy_data(self, start_date: datetime.datetime, end_date: datetime.datetime):
        orders = self.orders[
            (self.orders["creation_timestamp"] >= start_date) & (self.orders["creation_timestamp"] <= end_date)].copy()
        trade_fill = self.trade_fill[self.trade_fill["order_id"].isin(orders["id"])].copy()
        order_status = self.order_status[self.order_status["order_id"].isin(orders["id"])].copy()
        if self.market_data is not None:
            market_data = self.market_data[
                (self.market_data.index >= start_date) & (self.market_data.index <= end_date)].copy()
        else:
            market_data = None
        if self.position_executor is not None:
            position_executor = self.position_executor[(self.position_executor.datetime >= start_date) &
                                                       (self.position_executor.datetime <= end_date)].copy()
        else:
            position_executor = None
        return SingleMarketStrategyData(
            exchange=self.exchange,
            trading_pair=self.trading_pair,
            orders=orders,
            order_status=order_status,
            trade_fill=trade_fill,
            market_data=market_data,
            position_executor=position_executor
        )

    def get_market_data_resampled(self, interval):
        data_resampled = self.market_data.resample(interval).agg({
            "mid_price": "ohlc",
            "best_bid": "last",
            "best_ask": "last",
        })
        data_resampled.columns = data_resampled.columns.droplevel(0)
        return data_resampled

    @property
    def base_asset(self):
        return self.trading_pair.split("-")[0]

    @property
    def quote_asset(self):
        return self.trading_pair.split("-")[1]

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
        return np.nan_to_num(average_price, nan=0)

    @property
    def average_sell_price(self):
        average_price = (self.sells["price"] * self.sells["amount"]).sum() / self.total_sell_amount
        return np.nan_to_num(average_price, nan=0)

    @property
    def price_change(self):
        return (self.end_price - self.start_price) / self.start_price

    @property
    def trade_pnl_quote(self):
        buy_volume = self.buys["amount"].sum() * self.average_buy_price
        sell_volume = self.sells["amount"].sum() * self.average_sell_price
        inventory_change_volume = self.inventory_change_base_asset * self.end_price
        return sell_volume - buy_volume + inventory_change_volume

    @property
    def cum_fees_in_quote(self):
        return self.trade_fill["trade_fee_in_quote"].sum()

    @property
    def net_pnl_quote(self):
        return self.trade_pnl_quote - self.cum_fees_in_quote

    @property
    def inventory_change_base_asset(self):
        return self.total_buy_amount - self.total_sell_amount

    @property
    def accuracy(self):
        total_wins = (self.trade_fill["net_realized_pnl"] >= 0).sum()
        total_losses = (self.trade_fill["net_realized_pnl"] < 0).sum()
        return total_wins / (total_wins + total_losses)

    @property
    def profit_factor(self):
        total_profit = self.trade_fill.loc[self.trade_fill["realized_pnl"] >= 0, "realized_pnl"].sum()
        total_loss = self.trade_fill.loc[self.trade_fill["realized_pnl"] < 0, "realized_pnl"].sum()
        return total_profit / -total_loss

    @property
    def properties_table(self):
        properties_dict = {"Base Asset": self.base_asset,
                           "Quote Asset": self.quote_asset,
                           # "Start Time": self.start_time,
                           # "End Time": self.end_time,
                           "Exchange": self.exchange,
                           "Trading pair": self.trading_pair,
                           "Duration (seconds)": self.duration_seconds,
                           "Start Price": self.start_price,
                           "End Price": self.end_price,
                           "Total Buy Amount": self.total_buy_amount,
                           "Total Sell Amount": self.total_sell_amount,
                           "Total Buy Trades": self.total_buy_trades,
                           "Total Sell Trades": self.total_sell_trades,
                           "Total Orders": self.total_orders,
                           "Average Buy Price": self.average_buy_price,
                           "Average Sell Price": self.average_sell_price,
                           "Price Change": self.price_change,
                           "Trade PnL Quote": self.trade_pnl_quote,
                           "Cum Fees in Quote": self.cum_fees_in_quote,
                           "Net PnL Quote": self.net_pnl_quote,
                           "Inventory Change (base asset)": self.inventory_change_base_asset}
        properties_table = pd.DataFrame([properties_dict]).transpose().reset_index()
        properties_table.columns = ["Metric", "Value"]
        return properties_table
