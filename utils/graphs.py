import pandas as pd
from plotly.subplots import make_subplots
import pandas_ta as ta  # noqa: F401
import streamlit as st

from utils.data_manipulation import StrategyData
import plotly.graph_objs as go


class CandlesGraph:
    def __init__(self, candles_df: pd.DataFrame, show_volume=True, extra_rows=1):
        self.candles_df = candles_df
        self.show_volume = show_volume
        rows, heights = self.get_n_rows_and_heights(extra_rows)
        self.rows = rows
        specs = [[{"secondary_y": True}]] * rows
        self.base_figure = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.005,
                                         row_heights=heights, specs=specs)
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
        self.base_figure.add_trace(
            go.Candlestick(
                x=self.candles_df['datetime'],
                open=self.candles_df['open'],
                high=self.candles_df['high'],
                low=self.candles_df['low'],
                close=self.candles_df['close'],
                name="OHLC"
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
                )),
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
                            opacity=0.7, )),
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
                x=df['datetime'],
                y=df[f'BBU_{length}_{std}'],
                name='Bollinger Bands',
                mode='lines',
                line=dict(color='blue', width=1)),
            row=row, col=1,
        )
        self.base_figure.add_trace(
            go.Scatter(
                x=df['datetime'],
                y=df[f'BBM_{length}_{std}'],
                name='Bollinger Bands',
                mode='lines',
                line=dict(color='blue', width=1)),
            row=1, col=1,
        )
        self.base_figure.add_trace(
            go.Scatter(
                x=df['datetime'],
                y=df[f'BBL_{length}_{std}'],
                name='Bollinger Bands',
                mode='lines',
                line=dict(color='blue', width=1)),
            row=1, col=1,
        )

    def add_volume(self):
        self.base_figure.add_trace(
            go.Bar(
                x=self.candles_df['datetime'],
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
                x=df['datetime'],
                y=df[f'EMA_{length}'],
                name='EMA',
                mode='lines',
                line=dict(color='yellow', width=1)),
            row=row, col=1,
        )

    def add_base_inventory_change(self, strategy_data: StrategyData, row=3):
        # Create a list of colors based on the sign of the amount_new column
        self.base_figure.add_trace(
            go.Bar(
                x=strategy_data.trade_fill["timestamp"],
                y=strategy_data.trade_fill["net_amount"],
                name="Base Inventory Change",
                opacity=0.5,
                marker=dict(color=["lightgreen" if amount > 0 else "indianred" for amount in
                                   strategy_data.trade_fill["net_amount"]])
            ),
            row=row, col=1,
        )
        # TODO: Review impact in different subgraphs
        merged_df = self.get_merged_df(strategy_data)
        self.base_figure.add_trace(
            go.Scatter(
                x=merged_df.datetime,
                y=merged_df["cum_net_amount"],
                name="Cumulative Base Inventory Change",
                mode="lines+markers+text",
                marker=dict(color="black", size=6),
                line=dict(color="royalblue", width=2),
                text=merged_df["cum_net_amount"],
                textposition="top center",
                texttemplate="%{text:.2f}"
            ),
            row=row, col=1
        )
        self.base_figure.update_yaxes(title_text='Base Inventory Change', row=row, col=1)

    def add_pnl(self, strategy_data: SingleMarketStrategyData, row=4):
        merged_df = self.get_merged_df(strategy_data)

        self.base_figure.add_trace(
            go.Scatter(
                x=merged_df["timestamp"],
                y=merged_df["net_pnl_continuos"].apply(lambda x: round(x, 3)),
                name="Cumulative Net PnL",
                mode="lines",
                marker=dict(color="black", size=6),
                line=dict(color="black", width=2),
                text=merged_df["net_pnl_continuos"],
                textposition="top center",
                texttemplate="%{text:.3f}"
            ),
            row=row, col=1
        )
        self.base_figure.add_trace(
            go.Scatter(
                x=merged_df["timestamp"],
                y=merged_df["cum_fees_in_quote"].apply(lambda x: round(x, 3)),
                name="Cumulative Fees",
                mode="lines",
                fill="tozeroy",  # Fill to the line below (trade pnl)
                line=dict(color="yellow", width=2),
                text=merged_df["cum_fees_in_quote"],
            ),
            row=row, col=1
        )

        self.base_figure.add_trace(
            go.Scatter(
                x=merged_df["timestamp"],
                y=merged_df["trade_pnl_continuos"].apply(lambda x: round(x, 3)),
                name="Cumulative Trade PnL",
                mode="lines",
                fill="tonexty",  # Fill to the line below (net pnl)
                line=dict(color="salmon", width=2),
                text=merged_df["trade_pnl_continuos"],
            ),
            row=row, col=1
        )
        self.base_figure.update_yaxes(title_text='PNL', row=row, col=1)

    def update_layout(self):
        self.base_figure.update_layout(
            title={
                'text': "Market activity",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="right",
                x=1
            ),
            height=1500,
            xaxis_rangeslider_visible=False,
            hovermode='x unified'
        )
        self.base_figure.update_yaxes(title_text="Price", row=1, col=1)
        if self.show_volume:
            self.base_figure.update_yaxes(title_text="Volume", row=2, col=1)
        self.base_figure.update_xaxes(title_text="Time", row=self.rows, col=1)

    def get_merged_df(self, strategy_data: StrategyData):
        merged_df = pd.merge_asof(self.candles_df, strategy_data.trade_fill, left_on="datetime", right_on="timestamp", direction="backward")
        merged_df["trade_pnl_continuos"] = merged_df["unrealized_trade_pnl"] + merged_df["cum_net_amount"] * merged_df["close"]
        merged_df["net_pnl_continuos"] = merged_df["trade_pnl_continuos"] - merged_df["cum_fees_in_quote"]
        return merged_df
