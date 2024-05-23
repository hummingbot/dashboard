import plotly.graph_objects as go
import pandas as pd
from decimal import Decimal

from hummingbot.connector.connector_base import TradeType


def add_executors_trace(fig, executors, row, col):
    for executor in executors:
        entry_time = pd.to_datetime(executor.timestamp, unit='ms')
        entry_price = executor.custom_info["current_position_average_price"]
        exit_time = pd.to_datetime(executor.close_timestamp, unit='ms')
        exit_price = executor.custom_info["close_price"]
        name = "Buy Executor" if executor.config.side == TradeType.BUY else "Sell Executor"

        if executor.filled_amount_quote == 0:
            fig.add_trace(go.Scatter(x=[entry_time, exit_time], y=[entry_price, entry_price], mode='lines',
                                     line=dict(color='grey', width=2, dash="dash"), name=name), row=row, col=col)
        else:
            if executor.net_pnl_quote > Decimal(0):
                fig.add_trace(go.Scatter(x=[entry_time, exit_time], y=[entry_price, exit_price], mode='lines',
                                         line=dict(color='green', width=3), name=name), row=row, col=col)
            else:
                fig.add_trace(go.Scatter(x=[entry_time, exit_time], y=[entry_price, exit_price], mode='lines',
                                         line=dict(color='red', width=3), name=name), row=row, col=col)
    return fig
