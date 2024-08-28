def add_traces_to_fig(fig, traces, row=1, col=1):
    for trace in traces:
        fig.add_trace(trace, row=row, col=col)
