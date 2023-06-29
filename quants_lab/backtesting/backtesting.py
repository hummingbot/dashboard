from typing import Optional

import pandas as pd

from quants_lab.backtesting.backtesting_analysis import BacktestingAnalysis
from quants_lab.labeling.triple_barrier_method import triple_barrier_method
from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase


class Backtesting:
    def __init__(self, strategy: DirectionalStrategyBase):
        self.strategy = strategy

    def run_backtesting(self,
                        order_amount, leverage, initial_portfolio,
                        take_profit_multiplier, stop_loss_multiplier, time_limit,
                        std_span, taker_fee=0.0003, maker_fee=0.00012,
                        start: Optional[str] = None, end: Optional[str] = None):
        df = self.strategy.get_data(start=start, end=end)
        df = self.strategy.add_indicators(df)
        df = self.strategy.add_signals(df)
        df = triple_barrier_method(
            df=df,
            std_span=std_span,
            tp=take_profit_multiplier,
            sl=stop_loss_multiplier,
            tl=time_limit,
            trade_cost=taker_fee * 2,
            max_executors=1,
        )

        backtesting_analysis = self.get_backtest_analysis(
            df=df,
            maker_fee=maker_fee,
            taker_fee=taker_fee,
            order_amount=order_amount,
            leverage=leverage,
            initial_portfolio=initial_portfolio,
        )
        return backtesting_analysis

    @staticmethod
    def get_backtest_analysis(
            df,
            order_amount=15,
            initial_portfolio=700,
            leverage=20,
            maker_fee=0.00012,
            taker_fee=0.0003,
    ):
        # Set starting params
        first_row = df.iloc[0].tolist()
        first_row.extend([0, 0, 0, 0, 0, initial_portfolio])
        active_signals = df[df["active_signal"] == 1].copy()
        active_signals.loc[:, "amount"] = order_amount
        active_signals.loc[:, "margin_used"] = order_amount / leverage
        active_signals.loc[:, "fee_pct"] = active_signals["close_type"].apply(lambda x: maker_fee + taker_fee if x == "tp" else taker_fee * 2)
        active_signals.loc[:, "fee_usd"] = active_signals["fee_pct"] * active_signals["amount"]
        active_signals.loc[:, "ret_usd"] = active_signals.apply(lambda x: (x["ret"] - x["fee_pct"]) * x["amount"], axis=1)
        active_signals.loc[:, "current_portfolio"] = initial_portfolio + active_signals["ret_usd"].cumsum()
        active_signals.loc[:, "current_portfolio"].fillna(method='ffill', inplace=True)
        positions = pd.concat([pd.DataFrame([first_row], columns=active_signals.columns), active_signals])
        return positions.reset_index(drop=True)
