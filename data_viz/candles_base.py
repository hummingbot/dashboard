import pandas as pd
from plotly.subplots import make_subplots
import pandas_ta as ta  # noqa: F401
from abc import ABC

from utils.data_manipulation import StrategyData, SingleMarketStrategyData
from data_viz.tracers import PandasTAPlotlyTracer
from data_viz.tracers import PerformancePlotlyTracer
from data_viz.dtypes import IndicatorsConfigBase
import plotly.graph_objs as go


class CandlesBase(ABC):
    def __init__(self,
                 candles_df: pd.DataFrame,
                 indicators_config: IndicatorsConfigBase = None,
                 line_mode=False,
                 show_volume=False,
                 extra_rows=5):
        self.candles_df = candles_df
        self.indicators_config = indicators_config
        self.indicators_tracer = PandasTAPlotlyTracer(candles_df,
                                                      indicators_config)
        self.tracer = PerformancePlotlyTracer()
        self.show_volume = show_volume
        self.line_mode = line_mode
        rows, heights = self.get_n_rows_and_heights(extra_rows)
        self.rows = rows
        specs = [[{"secondary_y": True}]] * rows
        self.base_figure = make_subplots(rows=rows,
                                         cols=1,
                                         shared_xaxes=True,
                                         vertical_spacing=0.005,
                                         row_heights=heights,
                                         specs=specs)
        if 'timestamp' in candles_df.columns:
            candles_df.set_index("timestamp", inplace=True)
        self.min_time = candles_df.index.min()
        self.max_time = candles_df.index.max()
        self.add_candles_graph()
        if self.show_volume:
            self.add_volume()
        if self.indicators_config is not None:
            self.add_indicators()
        self.update_layout()

    def get_n_rows_and_heights(self, extra_rows):
        rows = 1 + extra_rows + self.show_volume
        row_heights = [0.4] * extra_rows
        if self.show_volume:
            row_heights.insert(0, 0.05)
        row_heights.insert(0, 0.8)
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
        self.base_figure.add_trace(self.tracer.get_buys_traces(data=data),
                                   row=1, col=1)

    def add_sell_trades(self, data: pd.Series):
        self.base_figure.add_trace(self.tracer.get_sells_traces(data=data),
                                   row=1, col=1)

    def add_quote_inventory_change(self, data: pd.DataFrame, quote_inventory_change_column: str, row_number: int = 3):
        self.base_figure.add_trace(self.tracer.get_quote_inventory_change(data=data,
                                                                          quote_inventory_change_column=quote_inventory_change_column),
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
            title={
                'text': "Market activity",
                'y': 0.99,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
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
        # TODO: Instead of using show_volume it should iterate over custom indicators adding corresponding titles
        if self.show_volume:
            self.base_figure.update_yaxes(title_text="Volume", row=2, col=1)
        self.base_figure.update_xaxes(title_text="Time", row=self.rows, col=1)

    # ----------------------------
    # INDICATORS METHODS
    # ----------------------------

    def add_bollinger_bands(self):
        if self.indicators_config.bollinger_bands.visible:
            bbu_trace, bbm_trace, bbl_trace = self.indicators_tracer.get_bollinger_bands_traces()
            self.base_figure.add_trace(trace=bbu_trace,
                                       row=self.indicators_config.bollinger_bands.row,
                                       col=self.indicators_config.bollinger_bands.col)
            self.base_figure.add_trace(trace=bbm_trace,
                                       row=self.indicators_config.bollinger_bands.row,
                                       col=self.indicators_config.bollinger_bands.col)
            self.base_figure.add_trace(trace=bbl_trace,
                                       row=self.indicators_config.bollinger_bands.row,
                                       col=self.indicators_config.bollinger_bands.col)
        else:
            return

    def add_ema(self):
        if self.indicators_config.ema.visible:
            ema_trace = self.indicators_tracer.get_ema_traces()
            self.base_figure.add_trace(trace=ema_trace,
                                       row=self.indicators_config.ema.row,
                                       col=self.indicators_config.ema.col)
        else:
            return

    def add_macd(self):
        if self.indicators_config.macd.visible:
            macd_trace, macd_signal_trace, macd_hist_trace = self.indicators_tracer.get_macd_traces()
            print(self.indicators_config.macd.row)
            print(self.indicators_config.macd.col)
            self.base_figure.add_trace(trace=macd_trace,
                                       row=self.indicators_config.macd.row,
                                       col=self.indicators_config.macd.col)
            self.base_figure.add_trace(trace=macd_signal_trace,
                                       row=self.indicators_config.macd.row,
                                       col=self.indicators_config.macd.col)
            self.base_figure.add_trace(trace=macd_hist_trace,
                                       row=self.indicators_config.macd.row,
                                       col=self.indicators_config.macd.col)
        else:
            return

    def add_rsi(self):
        if self.indicators_config.rsi.visible:
            rsi_trace = self.indicators_tracer.get_rsi_traces()
            self.base_figure.add_trace(trace=rsi_trace,
                                       row=self.indicators_config.rsi.row,
                                       col=self.indicators_config.rsi.col)
        else:
            return

    def add_indicators(self):
        self.add_bollinger_bands()
        self.add_ema()
        self.add_macd()
        self.add_rsi()
