import plotly.graph_objects as go
import numpy as np
import pandas as pd


def get_pnl_trace(executors):
    pnl = [e.net_pnl_quote for e in executors]
    cum_pnl = np.cumsum(pnl)
    return go.Scatter(
        x=pd.to_datetime([e.close_timestamp for e in executors], unit="ms"),
        y=cum_pnl,
        mode='lines',
        line=dict(color='gold', width=2, dash="dash"),
        name='Cumulative PNL'
    )
