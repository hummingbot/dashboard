from typing import List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from hummingbot.strategy_v2.models.executors_info import ExecutorInfo


def get_pnl_trace(executors: List[ExecutorInfo]):
    # Handle both dict and object formats
    if executors and isinstance(executors[0], dict):
        pnl = [e['net_pnl_quote'] for e in executors]
        timestamps = [e['close_timestamp'] for e in executors]
    else:
        pnl = [e.net_pnl_quote for e in executors]
        timestamps = [e.close_timestamp for e in executors]
    
    cum_pnl = np.cumsum(pnl)
    return go.Scatter(
        x=pd.to_datetime(timestamps, unit="s"),
        y=cum_pnl,
        mode='lines',
        line=dict(color='gold', width=2, dash="dash"),
        name='Cumulative PNL'
    )
