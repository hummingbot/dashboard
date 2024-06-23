import plotly.graph_objects as go
import numpy as np
import pandas as pd

from frontend.visualization.theme import get_color_scheme


def get_pnl_trace(executors):
    pnl = [e.net_pnl_quote for e in executors]
    cum_pnl = np.cumsum(pnl)
    return go.Scatter(
        x=pd.to_datetime([e.close_timestamp for e in executors], unit="s"),
        y=cum_pnl,
        mode='lines',
        line=dict(color='gold', width=2, dash="dash"),
        name='Cumulative PNL'
    )


def get_pnl_bar_fig(executors: pd.DataFrame):
    color_scheme = get_color_scheme()
    bar_traces = go.Bar(name="Cum Realized PnL",
                        x=[x + 1 for x in range(len(executors))],
                        y=executors["cum_net_pnl_quote"],
                        marker_color=executors["cum_net_pnl_quote"].apply(
                            lambda x: color_scheme["buy"] if x > 0 else color_scheme["sell"]),
                        showlegend=False)
    fig = go.Figure()
    fig.add_trace(bar_traces)
    fig.update_layout(xaxis_title="Trade Number",
                      yaxis_title="Cumulative Realized PnL",
                      title="Cumulative Realized PnL",
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)',
                      font=dict(color='white'))
    return fig
