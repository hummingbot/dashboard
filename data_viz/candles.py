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
                 show_indicators=False,
                 main_height=0.7,
                 max_height=1000,
                 rows: int = None,
                 row_heights: list = None):
        self.candles_df = candles_df
        self.show_indicators = show_indicators
        self.indicators_config = indicators_config
        self.show_annotations = show_annotations
        self.indicators_tracer = PandasTAPlotlyTracer(candles_df)
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
        self.update_layout()

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
                for i in range(len(self.candles_df)):
                    hover_text.append(
                        f"Open: {self.candles_df['open'][i]} <br>"
                        f"High: {self.candles_df['high'][i]} <br>"
                        f"Low: {self.candles_df['low'][i]} <br>"
                        f"Close: {self.candles_df['close'][i]} <br>"
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
        print(f"Sell traces: {sell_traces}")
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
            bbu_trace, bbm_trace, bbl_trace = self.indicators_tracer.get_bollinger_bands_traces(indicator_config)
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
            ema_trace = self.indicators_tracer.get_ema_traces(indicator_config)
            if ema_trace:
                self.base_figure.add_trace(trace=ema_trace,
                                           row=indicator_config.row,
                                           col=indicator_config.col)

    def add_macd(self, indicator_config: IndicatorConfig):
        if indicator_config.visible:
            macd_trace, macd_signal_trace, macd_hist_trace = self.indicators_tracer.get_macd_traces(indicator_config)
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
            rsi_trace = self.indicators_tracer.get_rsi_traces(indicator_config)
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
