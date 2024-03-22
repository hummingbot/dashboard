import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
import pandas_ta as ta  # noqa: F401
import streamlit as st
from typing import Union

from utils.data_manipulation import StrategyData, SingleMarketStrategyData
import plotly.graph_objs as go

BULLISH_COLOR = "rgba(97, 199, 102, 0.9)"
BEARISH_COLOR = "rgba(255, 102, 90, 0.9)"
FEE_COLOR = "rgba(51, 0, 51, 0.9)"
MIN_INTERVAL_RESOLUTION = "1m"


class PerformanceGraphs:
    BULLISH_COLOR = "rgba(97, 199, 102, 0.9)"
    BEARISH_COLOR = "rgba(255, 102, 90, 0.9)"
    FEE_COLOR = "rgba(51, 0, 51, 0.9)"

    def __init__(self, strategy_data: Union[StrategyData, SingleMarketStrategyData]):
        self.strategy_data = strategy_data

    @property
    def has_summary_table(self):
        if isinstance(self.strategy_data, StrategyData):
            return self.strategy_data.strategy_summary is not None
        else:
            return False

    @property
    def has_position_executor_summary(self):
        if isinstance(self.strategy_data, StrategyData):
            return self.strategy_data.position_executor is not None
        else:
            return False

    def strategy_summary_table(self):
        summary = st.data_editor(self.strategy_data.strategy_summary,
                                 column_config={"PnL Over Time": st.column_config.LineChartColumn("PnL Over Time",
                                                                                                  y_min=0,
                                                                                                  y_max=5000),
                                                "Explore": st.column_config.CheckboxColumn(required=True)
                                                },
                                 use_container_width=True,
                                 hide_index=True
                                 )
        selected_rows = summary[summary.Explore]
        if len(selected_rows) > 0:
            return selected_rows
        else:
            return None

    def candles_graph(self, candles: pd.DataFrame, interval="5m", show_volume=False, extra_rows=2):
        line_mode = interval == MIN_INTERVAL_RESOLUTION
        cg = CandlesGraph(candles, show_volume=show_volume, line_mode=line_mode, extra_rows=extra_rows)
        cg.add_buy_trades(self.strategy_data.buys)
        cg.add_sell_trades(self.strategy_data.sells)
        cg.add_pnl(self.strategy_data, row=2)
        cg.add_quote_inventory_change(self.strategy_data, row=3)
        if self.strategy_data.position_executor is not None:
            cg.add_positions(self.strategy_data.position_executor, row=1)
        return cg.figure()
