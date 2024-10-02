import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backend.services.backend_api_client import BackendAPIClient
from frontend.visualization.dca_builder import create_dca_graph

backend_api = BackendAPIClient()


def display_dca_tab(config_type, config):
    if config_type != "dca":
        st.info("No DCA configuration available for this controller.")
    else:
        dca_inputs, dca_amount = get_dca_inputs(config)
        fig = create_dca_graph(dca_inputs, dca_amount)
        st.plotly_chart(fig, use_container_width=True)


def get_dca_inputs(config: dict):
    take_profit = config.get("take_profit", 0.0)
    if take_profit is None:
        take_profit = config["trailing_stop"]["activation_price"]
    dca_inputs = {
        "dca_spreads": config.get("dca_spreads", []),
        "dca_amounts_pct": config.get("dca_amounts_pct", []),
        "stop_loss": config.get("stop_loss", 0.0),
        "take_profit": take_profit,
        "time_limit": config.get("time_limit", 0.0),
        "buy_amounts_pct": config.get("buy_amounts_pct", []),
        "sell_amounts_pct": config.get("sell_amounts_pct", [])
    }
    dca_amount = config["total_amount_quote"]
    return dca_inputs, dca_amount


def display_dca_performance(executors: pd.DataFrame):
    col1, col2, col3 = st.columns(3)
    with col1:
        level_id_data = executors.groupby("level_id").agg({"id": "count"}).reset_index()
        level_id_pie_chart_traces = go.Pie(labels=executors["level_id"],
                                           values=executors["id"],
                                           hole=0.4)
        st.plotly_chart(level_id_pie_chart_traces, use_container_width=True)
    with col2:
        intra_level_id_data = executors.groupby(['exit_level', 'close_type']).size().reset_index(name='count')
        fig = go.Figure()
        fig.add_trace(go.Pie(labels=intra_level_id_data.loc[intra_level_id_data["exit_level"] != 0, 'exit_level'],
                             values=intra_level_id_data.loc[intra_level_id_data["exit_level"] != 0, 'count'],
                             hole=0.4))
        fig.update_layout(title='Count of Close Types by Exit Level')
        st.plotly_chart(fig, use_container_width=True)

    # Intra level Analysis
    with col3:
        intra_level_id_pnl_data = executors.groupby(['exit_level'])['net_pnl_quote'].sum().reset_index(
            name='pnl')
        fig = go.Figure()
        for close_type in intra_level_id_data['close_type'].unique():
            temp_data = intra_level_id_data[intra_level_id_data['close_type'] == close_type]
            fig.add_trace(go.Bar(
                x=temp_data['exit_level'],
                y=temp_data['count'],
                name=close_type,
                yaxis='y'
            ))

        fig.add_trace(go.Scatter(x=intra_level_id_pnl_data['exit_level'],
                                 y=intra_level_id_pnl_data['pnl'],
                                 mode='lines+markers',
                                 name='PnL',
                                 text=intra_level_id_pnl_data['pnl'].apply(lambda x: f"$ {x:.2f}"),
                                 textposition='top center',
                                 yaxis='y2'))

        # Determine the maximum absolute value of count and pnl for setting the y-axis range
        max_count = max(abs(intra_level_id_data['count'].min()), abs(intra_level_id_data['count'].max()))
        max_pnl = max(abs(intra_level_id_pnl_data['pnl'].min()), abs(intra_level_id_pnl_data['pnl'].max()))

        # Update layout
        fig.update_layout(
            title='Count of Close Types by Exit Level and PnL by Exit Level',
            xaxis=dict(title='Exit Level'),
            yaxis=dict(title='Count', side='left', range=[-max_count, max_count]),
            yaxis2=dict(title='PnL', overlaying='y', side='right', range=[-max_pnl, max_pnl]),
            barmode='group'
        )

        st.plotly_chart(fig, use_container_width=True)

    # Apply custom sorting function to create a new column 'sorting_order'
    level_id_data[['type', 'number']] = level_id_data['level_id'].str.split('_', expand=True)
    level_id_data["number"] = level_id_data["number"].astype(int)
    level_id_data['sorting_order'] = level_id_data.apply(custom_sort, axis=1)
    level_id_data = level_id_data.sort_values(by='sorting_order')
    level_id_data.drop(columns=['type', 'number', 'sorting_order'], inplace=True)

    fig = go.Figure()
    level_id_pie_chart_traces = go.Bar(x=level_id_data["level_id"], y=level_id_data["id"])
    fig.add_trace(level_id_pie_chart_traces)
    fig.update_layout(title="Level ID Distribution")
    st.plotly_chart(fig, use_container_width=True)


def custom_sort(row):
    if row['type'] == 'buy':
        return 0, -row['number']
    else:
        return 1, row['number']
