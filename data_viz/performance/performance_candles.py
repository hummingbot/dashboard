import pandas as pd
from typing import Union

from data_viz.candles_base import CandlesBase
from utils.data_manipulation import StrategyData, SingleMarketStrategyData


class PerformanceCandles(CandlesBase):
    def __init__(self,
                 source: Union[StrategyData, SingleMarketStrategyData],
                 candles_df: pd.DataFrame = None,
                 line_mode: bool = False,
                 show_volume: bool = False,
                 extra_rows: int = 2):
        self.candles_df = candles_df
        super().__init__(candles_df=self.candles_df,
                         indicators_config=None,
                         line_mode=line_mode,
                         show_volume=show_volume,
                         extra_rows=extra_rows)
        self.positions = source.position_executor
        self.add_buy_trades(data=self.buys)
        self.add_sell_trades(data=self.sells)
        self.add_positions()

    @property
    def buys(self):
        df = self.positions[["datetime", "entry_price", "close_price", "close_datetime", "side"]].copy()
        df["price"] = df.apply(lambda row: row["entry_price"] if row["side"] == 1 else row["close_price"], axis=1)
        df["timestamp"] = df.apply(lambda row: row["datetime"] if row["side"] == 1 else row["close_datetime"], axis=1)
        df.set_index("timestamp", inplace=True)
        return df["price"]

    @property
    def sells(self):
        df = self.positions[["datetime", "entry_price", "close_price", "close_datetime", "side"]].copy()
        df["price"] = df.apply(lambda row: row["entry_price"] if row["side"] == -1 else row["close_price"], axis=1)
        df["timestamp"] = df.apply(lambda row: row["datetime"] if row["side"] == -1 else row["close_datetime"], axis=1)
        df.set_index("timestamp", inplace=True)
        return df["price"]

    def add_positions(self):
        for index, rown in self.positions.iterrows():
            self.base_figure.add_trace(self.tracer.get_positions_traces(position_number=rown["id"],
                                                                        open_time=rown["datetime"],
                                                                        close_time=rown["close_datetime"],
                                                                        open_price=rown["entry_price"],
                                                                        close_price=rown["close_price"],
                                                                        side=rown["side"],
                                                                        close_type=rown["close_type"],
                                                                        stop_loss=rown["sl"], take_profit=rown["tp"],
                                                                        time_limit=rown["tl"],
                                                                        net_pnl_quote=rown["net_pnl_quote"]),
                                       row=1, col=1)

