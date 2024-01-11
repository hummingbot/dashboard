from typing import Union
import pandas as pd
import plotly.graph_objects as go

from data_viz.charts_base import ChartsBase
from data_viz.tracers import PerformancePlotlyTracer
from quants_lab.strategy.strategy_analysis import StrategyAnalysis


class BacktestingCharts(ChartsBase):
    def __init__(self,
                 # TODO: Rename StrategyData as RealPerformanceData and StrategyAnalysis as BacktestingAnalysis
                 source: Union[StrategyAnalysis, None] = None):
        super().__init__()
        self.source = source
        self.tracer = PerformancePlotlyTracer()

    @property
    def realized_pnl_over_time_fig(self):
        if self.source is not None:
            data = self.source.positions.copy()
            data.sort_values(by="timestamp", inplace=True)
            return self.realized_pnl_over_time(data=data,
                                               cum_realized_pnl_column="net_pnl_quote")
        else:
            return go.Figure()

    def pnl_vs_max_drawdown_fig(self, data: pd.DataFrame = None):
        return self.pnl_vs_max_drawdown(data=data,
                                        max_drawdown_pct_column="max_drawdown_pct",
                                        net_pnl_pct_column="net_pnl_pct",
                                        hovertext_column="hover_text")
