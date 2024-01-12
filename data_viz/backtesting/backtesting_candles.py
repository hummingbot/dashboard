from data_viz.candles_base import CandlesBase
import pandas as pd
from data_viz.dtypes import IndicatorsConfigBase, IndicatorConfig
from quants_lab.strategy.strategy_analysis import StrategyAnalysis


class PlotlyIndicatorsConfigBase(IndicatorsConfigBase):
    bollinger_bands: IndicatorConfig = IndicatorConfig(visible=True, title="Bollinger Bands", row=1, col=1, color="blue", length=20, std=2.0)
    ema: IndicatorConfig = IndicatorConfig(visible=False, title="EMA", row=1, col=1, color="yellow", length=20)
    macd: IndicatorConfig = IndicatorConfig(visible=True, title="MACD", row=2, col=1, color="red", fast=12, slow=26, signal=9)
    rsi: IndicatorConfig = IndicatorConfig(visible=True, title="RSI", row=3, col=1, color="green", length=14)


class BacktestingCandles(CandlesBase):
    def __init__(self,
                 strategy_analysis: StrategyAnalysis,
                 line_mode: bool = False,
                 show_volume: bool = False,
                 extra_rows: int = 0):
        self.candles_df = strategy_analysis.candles_df
        super().__init__(candles_df=self.candles_df,
                         indicators_config=PlotlyIndicatorsConfigBase(),
                         line_mode=line_mode,
                         show_volume=show_volume,
                         extra_rows=extra_rows)
        self.positions = strategy_analysis.positions
        self.add_buy_trades(data=self.buys)
        self.add_sell_trades(data=self.sells)
        self.add_positions()

    def force_datetime_format(self):
        datetime_columns = ["timestamp", "close_time", "tl", "stop_loss_time", "take_profit_time"]
        for col in datetime_columns:
            self.positions[col] = pd.to_datetime(self.positions[col], unit="ms")

    @property
    def buys(self):
        df = self.positions[["timestamp", "close", "close_price", "close_time", "side"]].copy()
        df["price"] = df.apply(lambda row: row["close"] if row["side"] == 1 else row["close_price"], axis=1)
        df["timestamp"] = df.apply(lambda row: row["timestamp"] if row["side"] == 1 else row["close_time"], axis=1)
        df.set_index("timestamp", inplace=True)
        return df["price"]

    @property
    def sells(self):
        df = self.positions[["timestamp", "close", "close_price", "close_time", "side"]].copy()
        df["price"] = df.apply(lambda row: row["close"] if row["side"] == -1 else row["close_price"], axis=1)
        df["timestamp"] = df.apply(lambda row: row["timestamp"] if row["side"] == -1 else row["close_time"], axis=1)
        df.set_index("timestamp", inplace=True)
        return df["price"]

    def add_positions(self):
        i = 1
        for index, rown in self.positions.iterrows():
            i += 1
            self.base_figure.add_trace(self.tracer.get_positions_traces(position_number=i, open_time=rown["timestamp"],
                                                                        close_time=rown["close_time"],
                                                                        open_price=rown["close"],
                                                                        close_price=rown["close_price"],
                                                                        side=rown["side"],
                                                                        close_type=rown["close_type"],
                                                                        stop_loss=rown["sl"], take_profit=rown["tp"],
                                                                        time_limit=rown["tl"],
                                                                        net_pnl_quote=rown["net_pnl_quote"]),
                                       row=1, col=1)

