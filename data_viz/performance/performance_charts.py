from typing import Union

from data_viz.charts import ChartsBase
from data_viz.tracers import PerformancePlotlyTracer
from utils.data_manipulation import StrategyData, SingleMarketStrategyData


class PerformanceCharts(ChartsBase):
    def __init__(self,
                 # TODO: Rename StrategyData as RealPerformanceData and StrategyAnalysis as BacktestingAnalysis
                 source: Union[StrategyData, SingleMarketStrategyData]):
        super().__init__()
        self.source = source
        self.tracer = PerformancePlotlyTracer()

    @property
    def realized_pnl_over_trading_pair_fig(self):
        return self.realized_pnl_over_trading_pair(data=self.source.strategy_summary,
                                                   trading_pair_column="Trading Pair",
                                                   realized_pnl_column="Realized PnL", exchange="Exchange")

    @property
    def realized_pnl_over_time_fig(self):
        data = self.source.trade_fill.copy()
        data.sort_values(by="timestamp", inplace=True)
        return self.realized_pnl_over_time(data=data,
                                           cum_realized_pnl_column="net_realized_pnl")

    @property
    def intraday_performance_fig(self):
        data = self.source.trade_fill.copy()
        return self.intraday_performance(data=data,
                                         quote_volume_column="quote_volume",
                                         datetime_column="timestamp",
                                         realized_pnl_column="realized_pnl")

    @property
    def returns_distribution_fig(self):
        data = self.source.trade_fill.copy()
        return self.returns_distribution(data=data,
                                         realized_pnl_column="realized_pnl")

    @property
    def positions_summary_sunburst_fig(self):
        if self.source.position_executor is not None:
            df = self.source.position_executor.copy()
            data = df.groupby(["trading_pair", "side", "close_type"]).size().reset_index(name="count")
            return self.positions_summary_sunburst(data=data,
                                                   trading_pair_column="trading_pair",
                                                   side_column="side",
                                                   close_type_column="close_type",
                                                   values_column="count")
        else:
            return None
