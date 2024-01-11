from abc import ABC, abstractmethod
from typing import Union
import pandas as pd
import plotly.graph_objs as go

from data_viz.tracers import PerformancePlotlyTracer


class ChartsBase(ABC):
    def __init__(self,
                 tracer: PerformancePlotlyTracer = PerformancePlotlyTracer()):
        self.tracer = tracer

    def realized_pnl_over_trading_pair(self, data: pd.DataFrame(), trading_pair: str, realized_pnl: str, exchange: str):
        """
        :param data: strategy dataframe with timestamp as index
        :param trading_pair: column name of trading pair
        :param realized_pnl: column name of realized pnl
        :param exchange: column name of exchange
        """
        fig = go.Figure()
        for exchange in data[exchange].unique():
            fig.add_trace(self.tracer.get_realized_pnl_over_trading_pair_traces(data=data,
                                                                                trading_pair=trading_pair,
                                                                                realized_pnl=realized_pnl,
                                                                                exchange=exchange))
        fig.update_traces(width=min(1.0, 0.1 * len(data)))
        fig.update_layout(barmode='stack')
        return fig

    def realized_pnl_over_time(self, data: pd.DataFrame, cum_realized_pnl_column: str):
        fig = go.Figure()
        fig.add_trace(self.tracer.get_realized_pnl_over_time_traces(data=data,
                                                                    cum_realized_pnl_column=cum_realized_pnl_column))
        fig.update_layout(title=dict(text='Cummulative PnL', x=0.43, y=0.95),
                          plot_bgcolor='rgba(0,0,0,0)',
                          paper_bgcolor='rgba(0,0,0,0)')
        return fig

    def pnl_vs_max_drawdown(self, data: pd.DataFrame(), max_drawdown_pct_column: str, net_pnl_pct_column: str, hovertext_column: str):
        fig = go.Figure()
        fig.add_trace(self.tracer.get_pnl_vs_max_drawdown_traces(data=data,
                                                                 max_drawdown_pct_column=max_drawdown_pct_column,
                                                                 net_pnl_pct_column=net_pnl_pct_column,
                                                                 hovertext_column=hovertext_column))
        fig.update_layout(title="PnL vs Max Drawdown",
                          xaxis_title="Max Drawdown [%]",
                          yaxis_title="Net Profit [%]",
                          height=800)
        return fig

    def candlestick(self):
        pass

    def intraday_performance(self):
        pass

    def returns_distribution(self):
        pass

    def positions_sunburst(self):
        pass
