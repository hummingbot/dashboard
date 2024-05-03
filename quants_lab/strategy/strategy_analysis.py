import pandas as pd
import pandas_ta as ta  # noqa: F401
import numpy as np


class StrategyAnalysis:
    def __init__(self, positions: pd.DataFrame):
        self.positions = positions
        self.positions["timestamp"] = pd.to_datetime(self.positions["timestamp"], unit="ms")
        self.positions["close_time"] = pd.to_datetime(self.positions["close_time"], unit="ms")
        self.base_figure = None

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
        total_won = self.win_signals().loc[:, "net_pnl_quote"].sum()
        total_loss = - self.loss_signals().loc[:, "net_pnl_quote"].sum()
        return total_won / total_loss

    def duration_in_minutes(self):
        return (self.positions["timestamp"].iloc[-1] - self.positions["timestamp"].iloc[0]).total_seconds() / 60

    def avg_trading_time_in_minutes(self):
        time_diff_minutes = (self.positions["close_time"] - self.positions["timestamp"]).dt.total_seconds() / 60
        return time_diff_minutes.mean()

    def start_date(self):
        return pd.to_datetime(self.positions.timestamp.min(), unit="ms")

    def end_date(self):
        return pd.to_datetime(self.positions.timestamp.max(), unit="ms")

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
