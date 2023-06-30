import pandas_ta as ta
import optuna
import numpy as np
from optuna import TrialPruned
import traceback

from quants_lab.backtesting.backtesting import Backtesting
from quants_lab.backtesting.backtesting_analysis import BacktestingAnalysis
from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase
from quants_lab.utils import data_management


class MACDCumDiff(DirectionalStrategyBase):
    def __init__(self,
                 exchange="binance_perpetual",
                 trading_pair="DOGE-BUSD",
                 interval="5m",
                 delta_macd_thold=0.0006,
                 macdh_thold=0.0,
                 target_thold=0.0045,
                 macd_fast=12,
                 macd_slow=26,
                 macd_signal=9):
        self.exchange = exchange
        self.trading_pair = trading_pair
        self.interval = interval
        self.delta_macd_thold = delta_macd_thold
        self.macdh_thold = macdh_thold
        self.target_thold = target_thold
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal

    def get_raw_data(self):
        df = data_management.get_dataframe(
            exchange=self.exchange,
            trading_pair=self.trading_pair,
            interval=self.interval,
        )
        return df

    def add_indicators(self, df):
        df.ta.macd(fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal, append=True)
        return df

    def add_signals(self, df):
        macdh = f'MACDh_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}'
        macdh_norm = f'MACDh_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}_norm'
        df[macdh_norm] = df[macdh] / df['close']

        df['diff'] = df[macdh_norm].diff()
        df['start'] = np.sign(df['diff']) != np.sign(df['diff'].shift())
        df['id'] = df['start'].cumsum()
        df['macd_cum_diff'] = df.groupby('id')['diff'].cumsum()

        df['target'] = df['close'].rolling(100).std() / df['close']

        macd_long_cond = (df['macd_cum_diff'] > self.delta_macd_thold) & (df[macdh_norm] > self.macdh_thold) & (df['target'] > self.target_thold)
        macd_short_cond = (df['macd_cum_diff'] < - self.delta_macd_thold) & (df[macdh_norm] < - self.macdh_thold) & (df['target'] > self.target_thold)

        df['side'] = 0
        df.loc[macd_long_cond, 'side'] = 1
        df.loc[macd_short_cond, 'side'] = -1
        return df

    def objective(self, trial):
        self.delta_macd_thold = trial.suggest_float("delta_macd_thold", 0.0001, 0.001)
        self.macdh_thold = trial.suggest_float("macdh_thold", -0.1, 0.1)
        self.target_thold = trial.suggest_float("target_thold", 0.0025, 0.02)
        self.macd_fast = trial.suggest_int("macd_fast", 12, 30)
        self.macd_slow = trial.suggest_int("macd_slow", 26, 50)
        self.macd_signal = trial.suggest_int("macd_signal", 9, 25)

        try:
            backtesting = Backtesting(strategy=self)
            backtesting_result = backtesting.run_backtesting(
                start='2023-05-31',
                end='2023-06-20',
                order_amount=50,
                leverage=20,
                initial_portfolio=100,
                take_profit_multiplier=trial.suggest_float("take_profit_multiplier", 1.0, 5.0),
                stop_loss_multiplier=trial.suggest_float("stop_loss_multiplier", 1.0, 5.0),
                time_limit=60 * 60 * trial.suggest_int("time_limit", 1, 24),
                std_span=None,
            )
            backtesting_analysis = BacktestingAnalysis(
                positions=backtesting_result,
            )

            trial.set_user_attr("net_profit_usd", backtesting_analysis.net_profit_usd())
            trial.set_user_attr("net_profit_pct", backtesting_analysis.net_profit_pct())
            trial.set_user_attr("max_drawdown_usd", backtesting_analysis.max_drawdown_usd())
            trial.set_user_attr("max_drawdown_pct", backtesting_analysis.max_drawdown_pct())
            trial.set_user_attr("sharpe_ratio", backtesting_analysis.sharpe_ratio())
            trial.set_user_attr("accuracy", backtesting_analysis.accuracy())
            trial.set_user_attr("total_positions", backtesting_analysis.total_positions())
            trial.set_user_attr("win_signals", backtesting_analysis.win_signals().shape[0])
            trial.set_user_attr("loss_signals", backtesting_analysis.loss_signals().shape[0])
            trial.set_user_attr("profit_factor", backtesting_analysis.profit_factor())
            trial.set_user_attr("duration_in_hours", backtesting_analysis.duration_in_minutes() / 60)
            trial.set_user_attr("avg_trading_time_in_hours", backtesting_analysis.avg_trading_time_in_minutes() / 60)
            return backtesting_analysis.net_profit_pct()
        except Exception as e:
            traceback.print_exc()
            raise TrialPruned() from e
