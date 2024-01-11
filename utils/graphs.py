import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
import pandas_ta as ta  # noqa: F401
import streamlit as st
from typing import Union

from utils.data_manipulation import StrategyData, SingleMarketStrategyData
import plotly.graph_objs as go

BULLISH_COLOR = "rgba(97, 199, 102, 0.9)"
BEARISH_COLOR = "rgba(255, 102, 90, 0.9)"
FEE_COLOR = "rgba(51, 0, 51, 0.9)"
MIN_INTERVAL_RESOLUTION = "1m"


class CandlesGraph:
    def __init__(self, candles_df: pd.DataFrame, line_mode=False, show_volume=True, extra_rows=1):
        self.candles_df = candles_df
        self.show_volume = show_volume
        self.line_mode = line_mode
        rows, heights = self.get_n_rows_and_heights(extra_rows)
        self.rows = rows
        specs = [[{"secondary_y": True}]] * rows
        self.base_figure = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.005,
                                         row_heights=heights, specs=specs)
        self.min_time = candles_df.reset_index().timestamp.min()
        self.max_time = candles_df.reset_index().timestamp.max()
        self.add_candles_graph()
        if self.show_volume:
            self.add_volume()
        self.update_layout()

    def get_n_rows_and_heights(self, extra_rows):
        rows = 1 + extra_rows + self.show_volume
        row_heights = [0.4] * (extra_rows)
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

    def add_buy_trades(self, orders_data: pd.DataFrame):
        self.base_figure.add_trace(
            go.Scatter(
                x=orders_data['timestamp'],
                y=orders_data['price'],
                name='Buy Orders',
                mode='markers',
                marker=dict(
                    symbol='triangle-up',
                    color='green',
                    size=12,
                    line=dict(color='black', width=1),
                    opacity=0.7,
                ),
                hoverinfo="text",
                hovertext=orders_data["price"].apply(lambda x: f"Buy Order: {x} <br>")),
            row=1, col=1,
        )

    def add_sell_trades(self, orders_data: pd.DataFrame):
        self.base_figure.add_trace(
            go.Scatter(
                x=orders_data['timestamp'],
                y=orders_data['price'],
                name='Sell Orders',
                mode='markers',
                marker=dict(symbol='triangle-down',
                            color='red',
                            size=12,
                            line=dict(color='black', width=1),
                            opacity=0.7,),
                hoverinfo="text",
                hovertext=orders_data["price"].apply(lambda x: f"Sell Order: {x} <br>")),
            row=1, col=1,
        )

    def add_bollinger_bands(self, length=20, std=2.0, row=1):
        df = self.candles_df.copy()
        if len(df) < length:
            st.warning("Not enough data to calculate Bollinger Bands")
            return
        df.ta.bbands(length=length, std=std, append=True)
        self.base_figure.add_trace(
            go.Scatter(
                x=df.index,
                y=df[f'BBU_{length}_{std}'],
                name='Bollinger Bands',
                mode='lines',
                line=dict(color='blue', width=1)),
            row=row, col=1,
        )
        self.base_figure.add_trace(
            go.Scatter(
                x=df.index,
                y=df[f'BBM_{length}_{std}'],
                name='Bollinger Bands',
                mode='lines',
                line=dict(color='blue', width=1)),
            row=1, col=1,
        )
        self.base_figure.add_trace(
            go.Scatter(
                x=df.index,
                y=df[f'BBL_{length}_{std}'],
                name='Bollinger Bands',
                mode='lines',
                line=dict(color='blue', width=1)),
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

    def add_ema(self, length=20, row=1):
        df = self.candles_df.copy()
        if len(df) < length:
            st.warning("Not enough data to calculate EMA")
            return
        df.ta.ema(length=length, append=True)
        self.base_figure.add_trace(
            go.Scatter(
                x=df.index,
                y=df[f'EMA_{length}'],
                name='EMA',
                mode='lines',
                line=dict(color='yellow', width=1)),
            row=row, col=1,
        )

    def add_quote_inventory_change(self, strategy_data: StrategyData, row=3):
        self.base_figure.add_trace(
            go.Scatter(
                x=strategy_data.trade_fill.timestamp,
                y=strategy_data.trade_fill.inventory_cost,
                name="Quote Inventory",
                mode="lines",
                line=dict(shape="hv"),
            ),
            row=row, col=1
        )
        self.base_figure.update_yaxes(title_text='Quote Inventory Change', row=row, col=1)

    def add_pnl(self, strategy_data: SingleMarketStrategyData, row=4):
        self.base_figure.add_trace(
            go.Scatter(
                x=strategy_data.trade_fill.timestamp,
                y=[max(0, realized_pnl) for realized_pnl in strategy_data.trade_fill["realized_trade_pnl"].apply(lambda x: round(x, 4))],
                name="Cum Profit",
                mode='lines',
                line=dict(shape="hv", color="rgba(1, 1, 1, 0.5)", dash="dash", width=0.1),
                fill="tozeroy",  # Fill to the line below (trade pnl)
                fillcolor="rgba(0, 255, 0, 0.5)"
            ),
            row=row, col=1
        )
        self.base_figure.add_trace(
            go.Scatter(
                x=strategy_data.trade_fill.timestamp,
                y=[min(0, realized_pnl) for realized_pnl in strategy_data.trade_fill["realized_trade_pnl"].apply(lambda x: round(x, 4))],
                name="Cum Loss",
                mode='lines',
                line=dict(shape="hv", color="rgba(1, 1, 1, 0.5)", dash="dash", width=0.3),
                # marker=dict(symbol="arrow"),
                fill="tozeroy",  # Fill to the line below (trade pnl)
                fillcolor="rgba(255, 0, 0, 0.5)",
            ),
            row=row, col=1
        )
        self.base_figure.add_trace(
            go.Scatter(
                x=strategy_data.trade_fill.timestamp,
                y=strategy_data.trade_fill["cum_fees_in_quote"].apply(lambda x: round(x, 4)),
                name="Cum Fees",
                mode='lines',
                line=dict(shape="hv", color="rgba(1, 1, 1, 0.1)", dash="dash", width=0.1),
                fill="tozeroy",  # Fill to the line below (trade pnl)
                fillcolor="rgba(51, 0, 51, 0.5)"
            ),
            row=row, col=1
        )
        self.base_figure.add_trace(go.Scatter(name="Net Realized Profit",
                                              x=strategy_data.trade_fill.timestamp,
                                              y=strategy_data.trade_fill["net_realized_pnl"],
                                              mode="lines",
                                              line=dict(shape="hv")),
                                   row=row, col=1
                                   )
        self.base_figure.update_yaxes(title_text='PNL', row=row, col=1)

    def add_positions(self, position_executor_data: pd.DataFrame, row=1):
        position_executor_data["close_datetime"] = pd.to_datetime(position_executor_data["close_timestamp"], unit="s")
        i = 1
        for index, rown in position_executor_data.iterrows():
            i += 1
            self.base_figure.add_trace(go.Scatter(name=f"Position {index}",
                                                  x=[rown.datetime, rown.close_datetime],
                                                  y=[rown.entry_price, rown.close_price],
                                                  mode="lines",
                                                  line=dict(color="lightgreen" if rown.net_pnl_quote > 0 else "red"),
                                                  hoverinfo="text",
                                                  hovertext=f"Position N°: {i} <br>"
                                                            f"Datetime: {rown.datetime} <br>"
                                                            f"Close datetime: {rown.close_datetime} <br>"
                                                            f"Side: {rown.side} <br>"
                                                            f"Entry price: {rown.entry_price} <br>"
                                                            f"Close price: {rown.close_price} <br>"
                                                            f"Close type: {rown.close_type} <br>"
                                                            f"Stop Loss: {100 * rown.sl:.2f}% <br>"
                                                            f"Take Profit: {100 * rown.tp:.2f}% <br>"
                                                            f"Time Limit: {100 * rown.tl:.2f} <br>"
                                                            f"Open Order Type: {rown.open_order_type} <br>"
                                                            f"Leverage: {rown.leverage} <br>"
                                                            f"Controller name: {rown.controller_name} <br>",
                                                  showlegend=False),
                                        row=row, col=1)

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
        if self.show_volume:
            self.base_figure.update_yaxes(title_text="Volume", row=2, col=1)
        self.base_figure.update_xaxes(title_text="Time", row=self.rows, col=1)


class PerformanceGraphs:
    BULLISH_COLOR = "rgba(97, 199, 102, 0.9)"
    BEARISH_COLOR = "rgba(255, 102, 90, 0.9)"
    FEE_COLOR = "rgba(51, 0, 51, 0.9)"

    def __init__(self, strategy_data: Union[StrategyData, SingleMarketStrategyData]):
        self.strategy_data = strategy_data

    @property
    def has_summary_table(self):
        if isinstance(self.strategy_data, StrategyData):
            return self.strategy_data.strategy_summary is not None
        else:
            return False

    @property
    def has_position_executor_summary(self):
        if isinstance(self.strategy_data, StrategyData):
            return self.strategy_data.position_executor is not None
        else:
            return False

    def strategy_summary_table(self):
        summary = st.data_editor(self.strategy_data.strategy_summary,
                                 column_config={"PnL Over Time": st.column_config.LineChartColumn("PnL Over Time",
                                                                                                  y_min=0,
                                                                                                  y_max=5000),
                                                "Explore": st.column_config.CheckboxColumn(required=True)
                                                },
                                 use_container_width=True,
                                 hide_index=True
                                 )
        selected_rows = summary[summary.Explore]
        if len(selected_rows) > 0:
            return selected_rows
        else:
            return None

    def returns_histogram(self):
        df = self.strategy_data.trade_fill.copy()
        fig = go.Figure()
        fig.add_trace(go.Histogram(name="Losses",
                                   x=df.loc[df["realized_pnl"] < 0, "realized_pnl"],
                                   marker_color=BEARISH_COLOR))
        fig.add_trace(go.Histogram(name="Profits",
                                   x=df.loc[df["realized_pnl"] > 0, "realized_pnl"],
                                   marker_color=BULLISH_COLOR))
        fig.update_layout(
            title=dict(
                                text='Returns Distribution',
                                x=0.5,
                                xanchor="center",
                            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=.48
            ))
        return fig

    def position_executor_summary_sunburst(self):
        if self.strategy_data.position_executor is not None:
            df = self.strategy_data.position_executor.copy()
            grouped_df = df.groupby(["trading_pair", "side", "close_type"]).size().reset_index(name="count")

            fig = px.sunburst(grouped_df,
                              path=['trading_pair', 'side', 'close_type'],
                              values="count",
                              color_continuous_scale='RdBu',
                              color_continuous_midpoint=0)

            fig.update_layout(
                title=dict(
                    text='Position Executor Summary',
                    x=0.5,
                    xanchor="center",
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=.48
                )
            )
            return fig
        else:
            return None

    def candles_graph(self, candles: pd.DataFrame, interval="5m", show_volume=False, extra_rows=2):
        line_mode = interval == MIN_INTERVAL_RESOLUTION
        cg = CandlesGraph(candles, show_volume=show_volume, line_mode=line_mode, extra_rows=extra_rows)
        cg.add_buy_trades(self.strategy_data.buys)
        cg.add_sell_trades(self.strategy_data.sells)
        cg.add_pnl(self.strategy_data, row=2)
        cg.add_quote_inventory_change(self.strategy_data, row=3)
        if self.strategy_data.position_executor is not None:
            cg.add_positions(self.strategy_data.position_executor, row=1)
        return cg.figure()
