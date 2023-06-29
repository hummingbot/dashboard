import optuna
from quants_lab.backtesting.backtesting import Backtesting
from quants_lab.backtesting.backtesting_analysis import BacktestingAnalysis
from quants_lab.strategy.mean_reversion.bollinger import Bollinger
from quants_lab.strategy.mean_reversion.macd_bb import MACDBB
from optuna.exceptions import TrialPruned

STUDY_NAME = "bollinger"


def objective(trial):
    strategy = Bollinger(
        exchange="binance_perpetual",
        trading_pair="ETH-USDT",
        interval="3m",
        bb_length=trial.suggest_int("bb_length", 20, 300),
        bb_std=trial.suggest_float("bb_std", 1.0, 3.0),
        bb_long_threshold=trial.suggest_float("bb_long_threshold", -0.5, 0.3),
        bb_short_threshold=trial.suggest_float("bb_short_threshold", 0.7, 1.5),
    )

    # fast_macd = trial.suggest_int("fast_macd", 10, 50)
    # strategy = MACDBB(
    #     exchange="binance_perpetual",
    #     trading_pair="ETH-USDT",
    #     interval="3m",
    #     bb_length=trial.suggest_int("bb_length", 20, 300),
    #     bb_std=trial.suggest_float("bb_std", 1.0, 3.0),
    #     bb_long_threshold=trial.suggest_float("bb_long_threshold", -0.5, 0.3),
    #     bb_short_threshold=trial.suggest_float("bb_short_threshold", 0.7, 1.5),
    #     fast_macd=fast_macd,
    #     slow_macd=trial.suggest_int("slow_macd", fast_macd + 1, 100),
    #     signal_macd=trial.suggest_int("signal_macd", 8, 54)
    #
    # )
    try:
        backtesting = Backtesting(strategy=strategy)
        backtesting_result = backtesting.run_backtesting(
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
        print(e)
        raise TrialPruned()


study = optuna.create_study(direction="maximize", study_name=STUDY_NAME, storage="sqlite:///backtesting_report.db",
                            load_if_exists=True)

study.optimize(objective, n_trials=2000)
