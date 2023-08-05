from utils.st_utils import initialize_st_page
from utils.optuna_database_manager import OptunaDBManager
import pandas as pd
import streamlit as st
import plotly.graph_objs as go

initialize_st_page(title="Analyze", icon="🔬", initial_sidebar_state="collapsed")


def pnl_vs_maxdrawdown(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(name="Pnl vs Max Drawdown",
                             x=100 * df["max_drawdown_pct"],
                             y=100 * df["net_profit_pct"],
                             mode="markers",
                             text=None,
                             hovertext=df["hover_text"]))
    fig.update_layout(
        title="PnL vs Max Drawdown",
        xaxis_title="Max Drawdown [%]",
        yaxis_title="Net Profit [%]",
        height=800
    )
    fig.data[0].text = []
    return fig


opt_db = OptunaDBManager("backtesting_report.db")
st.plotly_chart(pnl_vs_maxdrawdown(opt_db.merged_df), use_container_width=True)
