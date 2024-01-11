from abc import ABC, abstractmethod
from typing import Union
import pandas as pd
import plotly.graph_objs as go

from data_viz.tracers import PerformancePlotlyTracer


class ChartsBase(ABC):
    def __init__(self,
                 tracer: PerformancePlotlyTracer = PerformancePlotlyTracer()):
        self.tracer = tracer

    def realized_pnl_over_trading_pair(self, data: pd.DataFrame(), trading_pair_column: str, realized_pnl_column: str, exchange: str):
        """
        :param data: strategy dataframe with timestamp as index
        :param trading_pair_column: column name of trading pair
        :param realized_pnl_column: column name of realized pnl
        :param exchange: column name of exchange
        """
        fig = go.Figure()
        for exchange in data[exchange].unique():
            fig.add_trace(self.tracer.get_realized_pnl_over_trading_pair_traces(data=data,
                                                                                trading_pair=trading_pair_column,
                                                                                realized_pnl=realized_pnl_column,
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

    def intraday_performance(self, data: pd.DataFrame(), quote_volume_column: str, datetime_column: str, realized_pnl_column: str):
        def hr2angle(hr):
            return (hr * 15) % 360

        def hr_str(hr):
            # Normalize hr to be between 1 and 12
            hr_string = str(((hr - 1) % 12) + 1)
            suffix = ' AM' if (hr % 24) < 12 else ' PM'
            return hr_string + suffix

        data["hour"] = data[datetime_column].dt.hour
        realized_pnl_per_hour = data.groupby("hour")[[realized_pnl_column, quote_volume_column]].sum().reset_index()
        fig = go.Figure()
        fig.add_trace(self.tracer.get_intraday_performance_traces(data=realized_pnl_per_hour,
                                                                  quote_volume_column=quote_volume_column,
                                                                  hour_column="hour",
                                                                  realized_pnl_column=realized_pnl_column))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    showline=False,
                ),
                angularaxis=dict(
                    rotation=90,
                    direction="clockwise",
                    tickvals=[hr2angle(hr) for hr in range(24)],
                    ticktext=[hr_str(hr) for hr in range(24)],
                ),
                bgcolor='rgba(255, 255, 255, 0)',

            ),
            legend=dict(
                orientation="h",
                x=0.5,
                y=1.08,
                xanchor="center",
                yanchor="bottom"
            ),
            title=dict(
                text='Intraday Performance',
                x=0.5,
                y=0.93,
                xanchor="center",
                yanchor="bottom"
            ),
        )
        return fig

    def returns_distribution(self):
        pass

    def positions_sunburst(self):
        pass
