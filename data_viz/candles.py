import json

import pandas as pd
from plotly.subplots import make_subplots
import pandas_ta as ta  # noqa: F401
from typing import List
from data_viz.tracers import PandasTAPlotlyTracer
from data_viz.tracers import PerformancePlotlyTracer
from data_viz.dtypes import IndicatorConfig
import plotly.graph_objs as go


class CandlesBase:
    def __init__(self,
                 candles_df: pd.DataFrame,
                 indicators_config: List[IndicatorConfig] = None,
                 show_annotations=True,
                 line_mode=False,
                 show_buys: bool = True,
                 show_sells: bool = True,
                 show_positions: bool = True,
                 show_indicators=False,
                 main_height=0.7,
                 max_height=1000,
                 rows: int = None,
                 row_heights: list = None):
        self.candles_df = candles_df
        self.show_indicators = show_indicators
        self.indicators_config = indicators_config
        self.show_annotations = show_annotations
        self.indicators_tracer = PandasTAPlotlyTracer()
        self.tracer = PerformancePlotlyTracer()
        self.line_mode = line_mode
        self.main_height = main_height
        self.max_height = max_height
        self.rows = rows
        if rows is None:
            rows, row_heights = self.get_n_rows_and_heights()
            self.rows = rows
        specs = [[{"secondary_y": True}]] * self.rows
        self.base_figure = make_subplots(rows=self.rows,
                                         cols=1,
                                         shared_xaxes=True,
                                         vertical_spacing=0.005,
                                         row_heights=row_heights,
                                         specs=specs)
        if 'timestamp' in candles_df.columns:
            candles_df.set_index("timestamp", inplace=True)
        self.min_time = candles_df.index.min()
        self.max_time = candles_df.index.max()
        self.add_candles_graph()
        if self.show_indicators and self.indicators_config is not None:
            self.add_indicators()
        if show_buys:
            self.add_buy_trades(data=self.buys)
        if show_sells:
            self.add_sell_trades(data=self.sells)
        if show_positions:
            self.add_positions()
        self.update_layout()

    @property
    def buys(self):
        return None

    @property
    def sells(self):
        return None

    def get_n_rows_and_heights(self):
        rows = 1
        if self.show_indicators and self.indicators_config is not None:
            rows = max([config.row for config in self.indicators_config])
        complementary_height = 1 - self.main_height
        row_heights = [self.main_height] + [complementary_height / (rows - 1)] * (rows - 1) if rows > 1 else [1]
        return rows, row_heights

    def figure(self):
        return self.base_figure

    def add_candles_graph(self):
        if self.line_mode:
            self.base_figure.add_trace(
                go.Scatter(x=self.candles_df.index,
                           y=self.candles_df['close'],
                           name="Close",
                           mode='lines',
                           line=dict(color='blue')),
                row=1, col=1,
            )
        else:
            hover_text = []
            if self.show_annotations:
                for timestamp in self.candles_df.index.values:
                    hover_text.append(
                        f"Open: {self.candles_df['open'][timestamp]} <br>"
                        f"High: {self.candles_df['high'][timestamp]} <br>"
                        f"Low: {self.candles_df['low'][timestamp]} <br>"
                        f"Close: {self.candles_df['close'][timestamp]} <br>"
                    )
            self.base_figure.add_trace(
                go.Candlestick(
                    x=self.candles_df.index,
                    open=self.candles_df['open'],
                    high=self.candles_df['high'],
                    low=self.candles_df['low'],
                    close=self.candles_df['close'],
                    name="OHLC",
                    hoverinfo="text",
                    hovertext=hover_text
                ),
                row=1, col=1,
            )

    def add_volume(self):
        self.base_figure.add_trace(
            go.Bar(
                x=self.candles_df.index,
                y=self.candles_df['volume'],
                name="Volume",
                opacity=0.5,
                marker=dict(color='lightgreen'),

            ),
            row=2, col=1,
        )

    def add_buy_trades(self, data: pd.Series):
        buy_traces = self.tracer.get_buys_traces(data=data) if not data.empty else None
        if bool(buy_traces):
            self.base_figure.add_trace(buy_traces,
                                       row=1, col=1)

    def add_sell_trades(self, data: pd.Series):
        sell_traces = self.tracer.get_sells_traces(data=data) if not data.empty else None
        if bool(sell_traces):
            self.base_figure.add_trace(sell_traces,
                                       row=1, col=1)

    def add_quote_inventory_change(self, data: pd.DataFrame, quote_inventory_change_column: str, row_number: int = 3):
        quote_inventory_change_trace = self.tracer.get_quote_inventory_change(
            data=data,
            quote_inventory_change_column=quote_inventory_change_column)
        if quote_inventory_change_trace:
            self.base_figure.add_trace(quote_inventory_change_trace,
                                       row=row_number, col=1)
            self.base_figure.update_yaxes(title_text='Quote Inventory Change', row=row_number, col=1)

    def add_pnl(self, data: pd.DataFrame, realized_pnl_column: str, fees_column: str, net_realized_pnl_column: str,
                row_number: int = 2):
        for trace in self.tracer.get_composed_pnl_traces(data=data,
                                                         realized_pnl_column=realized_pnl_column,
                                                         fees_column=fees_column,
                                                         net_realized_pnl_column=net_realized_pnl_column):
            self.base_figure.add_trace(trace, row=row_number, col=1)
        self.base_figure.update_yaxes(title_text='PNL', row=row_number, col=1)

    def add_positions(self):
        """
        Depending on whether the data source is backtesting or performance, the name of the columns might change.
        """
        pass

    def update_layout(self):
        self.base_figure.update_layout(
            legend=dict(
                orientation="h",
                x=0.5,
                y=1.04,
                xanchor="center",
                yanchor="bottom"
            ),
            height=self.max_height,
            xaxis=dict(rangeslider_visible=False,
                       range=[self.min_time, self.max_time]),
            yaxis=dict(range=[self.candles_df.low.min(), self.candles_df.high.max()]),
            hovermode='x unified'
        )
        self.base_figure.update_yaxes(title_text="Price", row=1, col=1)
        self.base_figure.update_xaxes(title_text="Time", row=self.rows, col=1)

    # ----------------------------
    # INDICATORS METHODS
    # ----------------------------

    def add_bollinger_bands(self, indicator_config: IndicatorConfig):
        if indicator_config.visible:
            bbu_trace, bbm_trace, bbl_trace = self.indicators_tracer.get_bollinger_bands_traces(self.candles_df,
                                                                                                indicator_config)
            if all([bbu_trace, bbm_trace, bbl_trace]):
                self.base_figure.add_trace(trace=bbu_trace,
                                           row=indicator_config.row,
                                           col=indicator_config.col)
                self.base_figure.add_trace(trace=bbm_trace,
                                           row=indicator_config.row,
                                           col=indicator_config.col)
                self.base_figure.add_trace(trace=bbl_trace,
                                           row=indicator_config.row,
                                           col=indicator_config.col)

    def add_ema(self, indicator_config: IndicatorConfig):
        if indicator_config.visible:
            ema_trace = self.indicators_tracer.get_ema_traces(self.candles_df, indicator_config)
            if ema_trace:
                self.base_figure.add_trace(trace=ema_trace,
                                           row=indicator_config.row,
                                           col=indicator_config.col)

    def add_macd(self, indicator_config: IndicatorConfig):
        if indicator_config.visible:
            macd_trace, macd_signal_trace, macd_hist_trace = self.indicators_tracer.get_macd_traces(self.candles_df,
                                                                                                    indicator_config)
            if all([macd_trace, macd_signal_trace, macd_hist_trace]):
                self.base_figure.add_trace(trace=macd_trace,
                                           row=indicator_config.row,
                                           col=indicator_config.col)
                self.base_figure.add_trace(trace=macd_signal_trace,
                                           row=indicator_config.row,
                                           col=indicator_config.col)
                self.base_figure.add_trace(trace=macd_hist_trace,
                                           row=indicator_config.row,
                                           col=indicator_config.col)

    def add_rsi(self, indicator_config: IndicatorConfig):
        if indicator_config.visible:
            rsi_trace = self.indicators_tracer.get_rsi_traces(self.candles_df, indicator_config)
            if rsi_trace:
                self.base_figure.add_trace(trace=rsi_trace,
                                           row=indicator_config.row,
                                           col=indicator_config.col)

    def add_indicators(self):
        for indicator in self.indicators_config:
            if indicator.title == "bbands":
                self.add_bollinger_bands(indicator)
            elif indicator.title == "ema":
                self.add_ema(indicator)
            elif indicator.title == "macd":
                self.add_macd(indicator)
            elif indicator.title == "rsi":
                self.add_rsi(indicator)
            else:
                raise ValueError(f"{indicator.title} is not a valid indicator. Choose from bbands, ema, macd, rsi")


class BacktestingCandles(CandlesBase):
    def __init__(self,
                 candles_df: pd.DataFrame,
                 positions_df: pd.DataFrame,
                 indicators_config: List[IndicatorConfig] = None,
                 line_mode: bool = False,
                 show_buys: bool = True,
                 show_sells: bool = True,
                 show_positions: bool = True,
                 show_indicators: bool = False):
        self.candles_df = candles_df
        self.positions = positions_df
        super().__init__(candles_df=self.candles_df,
                         indicators_config=indicators_config,
                         line_mode=line_mode,
                         show_indicators=show_indicators,
                         show_buys=show_buys,
                         show_sells=show_sells,
                         show_positions=show_positions)

    @property
    def buys(self):
        df = self.positions[["timestamp", "close", "close_price", "close_time", "side"]].copy()
        df["price"] = df.apply(lambda row: row["close"] if row["side"] == "BUY" else row["close_price"], axis=1)
        df["timestamp"] = df.apply(lambda row: row["timestamp"] if row["side"] == "BUY" else row["close_time"], axis=1)
        df.set_index("timestamp", inplace=True)
        return df["price"]

    @property
    def sells(self):
        df = self.positions[["timestamp", "close", "close_price", "close_time", "side"]].copy()
        df["price"] = df.apply(lambda row: row["close"] if row["side"] == "SELL" else row["close_price"], axis=1)
        df["timestamp"] = df.apply(lambda row: row["timestamp"] if row["side"] == "SELL" else row["close_time"], axis=1)
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


class PerformanceCandles(CandlesBase):
    def __init__(self,
                 indicators_config: List[IndicatorConfig] = None,
                 candles_df: pd.DataFrame = None,
                 trade_fill: pd.DataFrame = None,
                 executors_df: pd.DataFrame = None,
                 line_mode: bool = False,
                 show_buys: bool = False,
                 show_sells: bool = False,
                 show_positions: bool = False,
                 show_pnl: bool = True,
                 show_indicators: bool = False,
                 show_quote_inventory_change: bool = True,
                 show_annotations: bool = False,
                 strategy_version: str = "v1",
                 rows: int = None,
                 row_heights: List[float] = None,
                 main_height: float = 0.7):
        self.candles_df = candles_df
        self.trade_fill = trade_fill
        self.executors = executors_df
        self.strategy_version = strategy_version
        self.indicators_config = indicators_config
        self.show_buys = show_buys
        self.show_sells = show_sells
        self.show_positions = show_positions
        self.show_pnl = show_pnl
        self.show_quote_inventory_change = show_quote_inventory_change
        self.show_indicators = show_indicators
        self.main_height = main_height
        if rows is None and row_heights is None:
            rows, row_heights = self.get_n_rows_and_heights()
        super().__init__(candles_df=candles_df,
                         indicators_config=indicators_config,
                         line_mode=line_mode,
                         show_indicators=show_indicators,
                         show_buys=show_buys,
                         show_sells=show_sells,
                         show_positions=show_positions,
                         rows=rows,
                         row_heights=row_heights,
                         main_height=main_height,
                         show_annotations=show_annotations)
        if show_pnl and strategy_version == "v1":
            self.add_pnl(data=self.trade_fill,
                         realized_pnl_column="realized_trade_pnl",
                         fees_column="cum_fees_in_quote",
                         net_realized_pnl_column="net_realized_pnl",
                         row_number=rows - 1 if show_quote_inventory_change else rows)
        elif show_pnl and len(executors_df) > 0:
            self.add_pnl(data=self.executors.sort_values(by="close_datetime"),
                         realized_pnl_column="net_pnl_quote",
                         fees_column="cum_fees_in_quote",
                         net_realized_pnl_column="cum_net_pnl_quote",
                         row_number=rows - 1 if show_quote_inventory_change and strategy_version == "v1" else rows)
        if show_quote_inventory_change:
            self.add_quote_inventory_change(data=self.trade_fill,
                                            quote_inventory_change_column="inventory_cost",
                                            row_number=rows)
        self.update_layout()

    @property
    def buys(self):
        df = self.executors[["datetime", "entry_price", "close_price", "close_datetime", "side"]].copy()
        if len(df) > 0:
            df["price"] = df.apply(lambda row: row["entry_price"] if row["side"] == 1 else row["close_price"], axis=1)
            df["timestamp"] = df.apply(lambda row: row["datetime"] if row["side"] == 1 else row["close_datetime"], axis=1)
            df.set_index("timestamp", inplace=True)
            return df["price"]

    @property
    def sells(self):
        df = self.executors[["datetime", "entry_price", "close_price", "close_datetime", "side"]].copy()
        if len(df) > 0:
            df["price"] = df.apply(lambda row: row["entry_price"] if row["side"] == -1 else row["close_price"], axis=1)
            df["timestamp"] = df.apply(lambda row: row["datetime"] if row["side"] == -1 else row["close_datetime"], axis=1)
            df.set_index("timestamp", inplace=True)
            return df["price"]

    def get_n_rows_and_heights(self):
        rows = 1
        if self.show_indicators and self.indicators_config is not None:
            rows = max([config.row for config in self.indicators_config])
        if self.show_pnl:
            rows += 1
        if self.show_quote_inventory_change:
            rows += 1
        complementary_height = 1 - self.main_height
        row_heights = [self.main_height] + [round(complementary_height / (rows - 1), 3)] * (rows - 1) if rows > 1 else [1]
        return rows, row_heights

    def add_positions(self):
        if self.strategy_version == "v1":
            for index, rown in self.executors.iterrows():
                if abs(rown["net_pnl_quote"]) > 0:
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
        elif self.strategy_version == "v2":
            for index, rown in self.executors.iterrows():
                if abs(rown["net_pnl_quote"]) > 0:
                    self.base_figure.add_trace(self.tracer.get_positions_traces(position_number=rown["id"],
                                                                                open_time=rown["datetime"],
                                                                                close_time=rown["close_datetime"],
                                                                                open_price=rown["bep"],
                                                                                close_price=rown["close_price"],
                                                                                side=rown["side"],
                                                                                close_type=rown["close_type"],
                                                                                stop_loss=rown["sl"], take_profit=rown["tp"],
                                                                                time_limit=rown["tl"],
                                                                                net_pnl_quote=rown["net_pnl_quote"]),
                                               row=1, col=1)

    def add_dca_prices(self):
        if self.strategy_version == "v2":
            for index, rown in self.executors.iterrows():
                if abs(rown["net_pnl_quote"]) > 0:
                    data = list(json.loads(rown["conf"])["prices"])
                    data_series = pd.Series(data, index=[rown["datetime"]] * len(data))
                    self.base_figure.add_trace(self.tracer.get_entry_traces(data=data_series))

    def update_layout(self):
        self.base_figure.update_layout(
            legend=dict(
                orientation="h",
                x=0.5,
                y=1.04,
                xanchor="center",
                yanchor="bottom"
            ),
            height=1000,
            xaxis=dict(rangeslider_visible=False,
                       range=[self.min_time, self.max_time]),
            yaxis=dict(range=[self.candles_df.low.min(), self.candles_df.high.max()]),
            hovermode='x unified'
        )
        self.base_figure.update_yaxes(title_text="Price", row=1, col=1)
        self.base_figure.update_xaxes(title_text="Time", row=self.rows, col=1)
