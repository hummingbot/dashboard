import os
from datetime import datetime
from typing import Optional
import pandas as pd

from quants_lab.labeling.triple_barrier_method import triple_barrier_method


class DirectionalStrategyBase:

    def get_data(self, start: Optional[str] = None, end: Optional[str] = None):
        df = self.get_raw_data()
        return self.filter_df_by_time(df, start, end)

    def get_raw_data(self):
        raise NotImplemented

    def add_indicators(self, df):
        raise NotImplemented

    def add_signals(self, df):
        raise NotImplemented

    @staticmethod
    def get_candles(exchange: str, trading_pair: str, interval: str) -> pd.DataFrame:
        """
        Get a dataframe of market data from the database.
        :param exchange: Exchange name
        :param trading_pair: Trading pair
        :param interval: Interval of the data
        :return: Dataframe of market data
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, "../../data/candles")
        filename = f"candles_{exchange}_{trading_pair.upper()}_{interval}.csv"
        file_path = os.path.join(data_dir, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File '{file_path}' does not exist.")
        df = pd.read_csv(file_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

    @staticmethod
    def filter_df_by_time(df, start: Optional[str] = None, end: Optional[str] = None):
        if start is not None:
            start_condition = df["timestamp"] >= datetime.strptime(start, "%Y-%m-%d")
        else:
            start_condition = pd.Series([True]*len(df))
        if end is not None:
            end_condition = df["timestamp"] <= datetime.strptime(end, "%Y-%m-%d")
        else:
            end_condition = pd.Series([True]*len(df))
        return df[start_condition & end_condition]

    def run_backtesting(self,
                        take_profit_multiplier, stop_loss_multiplier, time_limit,
                        std_span, order_amount=100, leverage=20, initial_portfolio=1000,
                        taker_fee=0.0003, maker_fee=0.00012,
                        start: Optional[str] = None, end: Optional[str] = None):
        df = self.get_data(start=start, end=end)
        df = self.add_indicators(df)
        df = self.add_signals(df)
        df = triple_barrier_method(
            df=df,
            std_span=std_span,
            tp=take_profit_multiplier,
            sl=stop_loss_multiplier,
            tl=time_limit,
            trade_cost=taker_fee * 2,
            max_executors=1,
        )

        first_row = df.iloc[0].tolist()
        first_row.extend([0, 0, 0, 0, 0, initial_portfolio])
        active_signals = df[df["active_signal"] == 1].copy()
        active_signals.loc[:, "amount"] = order_amount
        active_signals.loc[:, "margin_used"] = order_amount / leverage
        active_signals.loc[:, "fee_pct"] = active_signals["close_type"].apply(
            lambda x: maker_fee + taker_fee if x == "tp" else taker_fee * 2)
        active_signals.loc[:, "fee_usd"] = active_signals["fee_pct"] * active_signals["amount"]
        active_signals.loc[:, "ret_usd"] = active_signals.apply(lambda x: (x["ret"] - x["fee_pct"]) * x["amount"],
                                                                axis=1)
        active_signals.loc[:, "current_portfolio"] = initial_portfolio + active_signals["ret_usd"].cumsum()
        active_signals.loc[:, "current_portfolio"].fillna(method='ffill', inplace=True)
        positions = pd.concat([pd.DataFrame([first_row], columns=active_signals.columns), active_signals])
        return df, positions.reset_index(drop=True)
