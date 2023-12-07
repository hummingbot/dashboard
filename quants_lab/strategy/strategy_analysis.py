from typing import Optional

import pandas as pd
from plotly.subplots import make_subplots
import pandas_ta as ta  # noqa: F401
import plotly.graph_objs as go
import numpy as np


class StrategyAnalysis:
    def __init__(self, positions: pd.DataFrame, candles_df: Optional[pd.DataFrame] = None):
        self.candles_df = candles_df
        self.positions = positions
        self.candles_df["timestamp"] = pd.to_datetime(self.candles_df["timestamp"], unit="ms")
        self.positions["timestamp"] = pd.to_datetime(self.positions["timestamp"], unit="ms")
        self.positions["close_time"] = pd.to_datetime(self.positions["close_time"], unit="ms")
        self.base_figure = None

    def create_base_figure(self, candlestick=True, volume=True, positions=False, trade_pnl=False, extra_rows=0):
        rows, heights = self.get_n_rows_and_heights(extra_rows + trade_pnl, volume)
        self.rows = rows
        specs = [[{"secondary_y": True}]] * rows
        self.base_figure = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.01,
                                         row_heights=heights, specs=specs)
        if candlestick:
            self.add_candles_graph()
        if volume:
            self.add_volume()
        if positions:
            self.add_positions()
        if trade_pnl:
            self.add_trade_pnl(row=rows)
        self.update_layout(volume)

    def add_positions(self):
        # Add long and short positions
        active_signals = self.positions.copy()
        active_signals.loc[active_signals["signal"] == -1, "symbol"] = "triangle-down"
        active_signals.loc[active_signals["signal"] == 1, "symbol"] = "triangle-up"
        active_signals.loc[active_signals["profitable"] == 1, "color"] = "lightgreen"
        active_signals.loc[active_signals["profitable"] == -1, "color"] = "red"
        self.base_figure.add_trace(go.Scatter(x=active_signals.loc[(active_signals["side"] != 0), "timestamp"],
                                              y=active_signals.loc[active_signals["side"] != 0, "close"],
                                              name="Entry Price: $",
                                              mode="markers",
                                              marker_color=active_signals.loc[(active_signals["side"] != 0), "color"],
                                              marker_symbol=active_signals.loc[(active_signals["side"] != 0), "symbol"],
                                              marker_size=20,
                                              marker_line={"color": "black", "width": 0.7}),
                                   row=1, col=1)

        for index, row in active_signals.iterrows():
            self.base_figure.add_shape(type="rect",
                                       fillcolor="green",
                                       opacity=0.5,
                                       x0=row.timestamp,
                                       y0=row.close,
                                       x1=row.close_time,
                                       y1=row.take_profit_price,
                                       line=dict(color="green"),
                                       row=1, col=1)
            # Add SL
            self.base_figure.add_shape(type="rect",
                                       fillcolor="red",
                                       opacity=0.5,
                                       x0=row.timestamp,
                                       y0=row.close,
                                       x1=row.close_time,
                                       y1=row.stop_loss_price,
                                       line=dict(color="red"),
                                       row=1, col=1)

    def get_n_rows_and_heights(self, extra_rows, volume=True):
        rows = 1 + extra_rows + volume
        row_heights = [0.5] * (extra_rows)
        if volume:
            row_heights.insert(0, 0.2)
        row_heights.insert(0, 0.8)
        return rows, row_heights

    def figure(self):
        return self.base_figure

    def add_candles_graph(self):
        self.base_figure.add_trace(
            go.Candlestick(
                x=self.candles_df["timestamp"],
                open=self.candles_df["open"],
                high=self.candles_df["high"],
                low=self.candles_df["low"],
                close=self.candles_df["close"],
                name="OHLC"
            ),
            row=1, col=1,
        )

    def add_volume(self):
        self.base_figure.add_trace(
            go.Bar(
                x=self.candles_df["timestamp"],
                y=self.candles_df["volume"],
                name="Volume",
                opacity=0.5,
                marker=dict(color="lightgreen")
            ),
            row=2, col=1,
        )

    def add_trade_pnl(self, row=2):
        self.base_figure.add_trace(
            go.Scatter(
                x=self.positions["timestamp"],
                y=self.positions["net_pnl_quote"].cumsum(),
                name="Cumulative Trade PnL",
                mode="lines",
                line=dict(color="chocolate", width=2)),
            row=row, col=1
        )
        self.base_figure.update_yaxes(title_text="Cum Trade PnL", row=row, col=1)

    def update_layout(self, volume=True):
        self.base_figure.update_layout(
            title={
                "text": "Backtesting Analysis",
                "y": 0.95,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top"
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
            hovermode="x unified"
        )
        self.base_figure.update_yaxes(title_text="Price", row=1, col=1)
        if volume:
            self.base_figure.update_yaxes(title_text="Volume", row=2, col=1)
        self.base_figure.update_xaxes(title_text="Time", row=self.rows, col=1)

    def initial_portfolio(self):
        return self.positions["inventory"].dropna().values[0]

    def final_portfolio(self):
        return self.positions["inventory"].dropna().values[-1]

    def net_profit_usd(self):
        return self.final_portfolio() - self.initial_portfolio()

    def net_profit_pct(self):
        return self.net_profit_usd() / self.initial_portfolio()

    def returns(self):
        return self.positions["net_pnl_quote"] / self.initial_portfolio()

    def total_positions(self):
        return self.positions.shape[0] - 1

    def win_signals(self):
        return self.positions.loc[(self.positions["profitable"] > 0) & (self.positions["side"] != 0)]

    def loss_signals(self):
        return self.positions.loc[(self.positions["profitable"] < 0) & (self.positions["side"] != 0)]

    def accuracy(self):
        return self.win_signals().shape[0] / self.total_positions()

    def max_drawdown_usd(self):
        cumulative_returns = self.positions["net_pnl_quote"].cumsum()
        peak = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - peak)
        max_draw_down = np.min(drawdown)
        return max_draw_down

    def max_drawdown_pct(self):
        return self.max_drawdown_usd() / self.initial_portfolio()

    def sharpe_ratio(self):
        returns = self.returns()
        return returns.mean() / returns.std()

    def profit_factor(self):
        total_won = self.win_signals().loc[:,  "net_pnl_quote"].sum()
        total_loss = - self.loss_signals().loc[:, "net_pnl_quote"].sum()
        return total_won / total_loss

    def duration_in_minutes(self):
        return (self.positions["timestamp"].iloc[-1] - self.positions["timestamp"].iloc[0]).total_seconds() / 60

    def avg_trading_time_in_minutes(self):
        time_diff_minutes = (self.positions["close_time"] - self.positions["timestamp"]).dt.total_seconds() / 60
        return time_diff_minutes.mean()

    def start_date(self):
        return pd.to_datetime(self.candles_df.timestamp.min(), unit="ms")

    def end_date(self):
        return pd.to_datetime(self.candles_df.timestamp.max(), unit="ms")

    def avg_profit(self):
        return self.positions.net_pnl_quote.mean()

    def text_report(self):
        return f"""
Strategy Performance Report:
    - Net Profit: {self.net_profit_usd():,.2f} USD ({self.net_profit_pct() * 100:,.2f}%)
    - Total Positions: {self.total_positions()}
    - Win Signals: {self.win_signals().shape[0]}
    - Loss Signals: {self.loss_signals().shape[0]}
    - Accuracy: {self.accuracy():,.2f}%
    - Profit Factor: {self.profit_factor():,.2f}
    - Max Drawdown: {self.max_drawdown_usd():,.2f} USD | {self.max_drawdown_pct() * 100:,.2f}%
    - Sharpe Ratio: {self.sharpe_ratio():,.2f}
    - Duration: {self.duration_in_minutes() / 60:,.2f} Hours
    - Average Trade Duration: {self.avg_trading_time_in_minutes():,.2f} minutes
    """

    def pnl_over_time(self):
        fig = go.Figure()
        fig.add_trace(go.Scatter(name="PnL Over Time",
                                 x=self.positions.index,
                                 y=self.positions.net_pnl_quote.cumsum()))
        # Update layout with the required attributes
        fig.update_layout(
            title="PnL Over Time",
            xaxis_title="N° Position",
            yaxis=dict(title="Net PnL USD", side="left", showgrid=False),
        )
        return fig