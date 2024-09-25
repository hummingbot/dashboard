import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from frontend.visualization.theme import get_color_scheme


def get_pnl_traces(executors: pd.DataFrame):
    color_scheme = get_color_scheme()
    executors.sort_values("close_timestamp", inplace=True)
    executors["cum_net_pnl_quote"] = executors["net_pnl_quote"].cumsum()
    scatter_traces = go.Scatter(name="Cum Realized PnL",
                                x=executors["close_datetime"],
                                y=executors["cum_net_pnl_quote"],
                                marker_color=executors["cum_net_pnl_quote"].apply(
                                    lambda x: color_scheme["buy"] if x > 0 else color_scheme["sell"]),
                                showlegend=False,
                                fill="tozeroy")
    return scatter_traces


def get_volume_bar_traces(executors: pd.DataFrame):
    color_scheme = get_color_scheme()
    executors.sort_values("close_timestamp", inplace=True)
    executors["cum_filled_amount_quote"] = executors["filled_amount_quote"].cumsum() * 2
    scatter_traces = go.Scatter(name="Cum Volume",
                                x=executors["close_datetime"],
                                y=executors["cum_filled_amount_quote"],
                                marker_color=executors["cum_filled_amount_quote"].apply(
                                    lambda x: color_scheme["buy"] if x > 0 else color_scheme["sell"]),
                                showlegend=False,
                                fill="tozeroy")
    return scatter_traces


def get_total_executions_with_position_bar_traces(executors: pd.DataFrame):
    color_scheme = get_color_scheme()
    executors.sort_values("close_timestamp", inplace=True)
    executors["cum_n_trades"] = (executors['net_pnl_pct'] != 0).cumsum()
    scatter_traces = go.Scatter(name="Cum Activity",
                                x=executors["close_datetime"],
                                y=executors["cum_n_trades"],
                                marker_color=executors["cum_n_trades"].apply(
                                    lambda x: color_scheme["buy"] if x > 0 else color_scheme["sell"]),
                                showlegend=False,
                                fill="tozeroy")
    return scatter_traces


def get_accuracy_over_time_traces(executors: pd.DataFrame):
    color_scheme = get_color_scheme()
    executors.sort_values("close_timestamp", inplace=True)
    executors = executors[executors['net_pnl_pct'] != 0]
    executors['cum_win_signals'] = (executors['net_pnl_pct'] > 0).cumsum()
    executors['cum_loss_signals'] = (executors['net_pnl_pct'] < 0).cumsum()
    executors['acc_over_time'] = executors['cum_win_signals'] / range(1, len(executors) + 1)

    acc_trace = go.Scatter(x=executors['close_datetime'],
                           y=executors['acc_over_time'] * 100,
                           mode='lines',
                           line=dict(color='gold', width=2, dash="dash"),
                           name='Accuracy Over Time',
                           fill="tozeroy")
    win_trace = go.Scatter(x=pd.to_datetime(executors["close_timestamp"], unit="s"),
                           y=executors['cum_win_signals'],
                           mode='lines',
                           line=dict(color=color_scheme["buy"], width=2),
                           name='Win',
                           fill="tozeroy")
    loss_trace = go.Scatter(x=pd.to_datetime(executors["close_timestamp"], unit="s"),
                            y=executors['cum_loss_signals'],
                            mode='lines',
                            line=dict(color=color_scheme["sell"], width=2),
                            name='Loss',
                            fill='tozeroy')
    return acc_trace, win_trace, loss_trace


def create_combined_subplots(executors: pd.DataFrame):
    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=["Cumulative PnL",
                                        "Cumulative Volume",
                                        "Cumulative Positions",
                                        "Accuracy",
                                        "Win/Loss"])

    # Adding PnL Bar trace
    pnl_trace = get_pnl_traces(executors)
    fig.add_trace(pnl_trace, row=1, col=1)

    # Adding Volume Bar trace
    volume_trace = get_volume_bar_traces(executors)
    fig.add_trace(volume_trace, row=2, col=1)

    # Adding Total Executions Bar trace
    activity_trace = get_total_executions_with_position_bar_traces(executors)
    fig.add_trace(activity_trace, row=3, col=1)

    # Adding Accuracy, Win Signals, Loss Signals traces
    acc_trace, win_trace, loss_trace = get_accuracy_over_time_traces(executors)
    fig.add_trace(acc_trace, row=4, col=1)
    fig.add_trace(win_trace, row=5, col=1)
    fig.add_trace(loss_trace, row=5, col=1)

    fig.update_layout(height=1000, width=800,
                      title_text="Global Aggregated Performance Metrics",
                      plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)',
                      font=dict(color='white'))

    fig.update_yaxes(title_text="$ Quote", row=1, col=1)
    fig.update_yaxes(title_text="$ Quote", row=2, col=1)
    fig.update_yaxes(title_text="# Executors", row=3, col=1)
    fig.update_yaxes(title_text="%", row=4, col=1)
    fig.update_yaxes(title_text="# Signals", row=5, col=1)

    return fig
