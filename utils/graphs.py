import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
import pandas_ta as ta  # noqa: F401
import streamlit as st
from typing import Union

from utils.data_manipulation import StrategyData, SingleMarketStrategyData
from quants_lab.strategy.strategy_analysis import StrategyAnalysis
import plotly.graph_objs as go

BULLISH_COLOR = "rgba(97, 199, 102, 0.9)"
BEARISH_COLOR = "rgba(255, 102, 90, 0.9)"
FEE_COLOR = "rgba(51, 0, 51, 0.9)"


class CandlesGraph:
    def __init__(self, candles_df: pd.DataFrame, show_volume=True, extra_rows=1):
        self.candles_df = candles_df
        self.show_volume = show_volume
        rows, heights = self.get_n_rows_and_heights(extra_rows)
        self.rows = rows
        specs = [[{"secondary_y": True}]] * rows
        self.base_figure = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.005,
                                         row_heights=heights, specs=specs)
        self.min_time = candles_df.reset_index().timestamp.min()
        self.max_time = candles_df.reset_index().timestamp.max()
        self.add_candles_graph()
        if self.show_volume:
            self.add_volume()
        self.update_layout()

    def get_n_rows_and_heights(self, extra_rows):
        rows = 1 + extra_rows + self.show_volume
        row_heights = [0.4] * (extra_rows)
        if self.show_volume:
            row_heights.insert(0, 0.05)
        row_heights.insert(0, 0.8)
        return rows, row_heights

    def figure(self):
        return self.base_figure

    def add_candles_graph(self):
        self.base_figure.add_trace(
            go.Candlestick(
                x=self.candles_df.index,
                open=self.candles_df['open'],
                high=self.candles_df['high'],
                low=self.candles_df['low'],
                close=self.candles_df['close'],
                name="OHLC"
            ),
            row=1, col=1,
        )

    def add_buy_trades(self, orders_data: pd.DataFrame):
        self.base_figure.add_trace(
            go.Scatter(
                x=orders_data['timestamp'],
                y=orders_data['price'],
                name='Buy Orders',
                mode='markers',
                marker=dict(
                    symbol='triangle-up',
                    color='green',
                    size=12,
                    line=dict(color='black', width=1),
                    opacity=0.7,
                )),
            row=1, col=1,
        )

    def add_sell_trades(self, orders_data: pd.DataFrame):
        self.base_figure.add_trace(
            go.Scatter(
                x=orders_data['timestamp'],
                y=orders_data['price'],
                name='Sell Orders',
                mode='markers',
                marker=dict(symbol='triangle-down',
                            color='red',
                            size=12,
                            line=dict(color='black', width=1),
                            opacity=0.7, )),
            row=1, col=1,
        )

    def add_bollinger_bands(self, length=20, std=2.0, row=1):
        df = self.candles_df.copy()
        if len(df) < length:
            st.warning("Not enough data to calculate Bollinger Bands")
            return
        df.ta.bbands(length=length, std=std, append=True)
        self.base_figure.add_trace(
            go.Scatter(
                x=df.index,
                y=df[f'BBU_{length}_{std}'],
                name='Bollinger Bands',
                mode='lines',
                line=dict(color='blue', width=1)),
            row=row, col=1,
        )
        self.base_figure.add_trace(
            go.Scatter(
                x=df.index,
                y=df[f'BBM_{length}_{std}'],
                name='Bollinger Bands',
                mode='lines',
                line=dict(color='blue', width=1)),
            row=1, col=1,
        )
        self.base_figure.add_trace(
            go.Scatter(
                x=df.index,
                y=df[f'BBL_{length}_{std}'],
                name='Bollinger Bands',
                mode='lines',
                line=dict(color='blue', width=1)),
            row=1, col=1,
        )

    def add_volume(self):
        self.base_figure.add_trace(
            go.Bar(
                x=self.candles_df.index,
                y=self.candles_df['volume'],
                name="Volume",
                opacity=0.5,
                marker=dict(color='lightgreen'),

            ),
            row=2, col=1,
        )

    def add_ema(self, length=20, row=1):
        df = self.candles_df.copy()
        if len(df) < length:
            st.warning("Not enough data to calculate EMA")
            return
        df.ta.ema(length=length, append=True)
        self.base_figure.add_trace(
            go.Scatter(
                x=df.index,
                y=df[f'EMA_{length}'],
                name='EMA',
                mode='lines',
                line=dict(color='yellow', width=1)),
            row=row, col=1,
        )

    def add_quote_inventory_change(self, strategy_data: StrategyData, row=3):
        self.base_figure.add_trace(
            go.Scatter(
                x=strategy_data.trade_fill.timestamp,
                y=strategy_data.trade_fill.inventory_cost,
                name="Quote Inventory",
                mode="lines",
                line=dict(shape="hv"),
            ),
            row=row, col=1
        )
        self.base_figure.update_yaxes(title_text='Quote Inventory Change', row=row, col=1)

    def add_pnl(self, strategy_data: SingleMarketStrategyData, row=4):
        self.base_figure.add_trace(
            go.Scatter(
                x=strategy_data.trade_fill.timestamp,
                y=[max(0, realized_pnl) for realized_pnl in strategy_data.trade_fill["realized_trade_pnl"].apply(lambda x: round(x, 4))],
                name="Cum Profit",
                mode='lines',
                line=dict(shape="hv", color="rgba(1, 1, 1, 0.5)", dash="dash", width=0.1),
                fill="tozeroy",  # Fill to the line below (trade pnl)
                fillcolor="rgba(0, 255, 0, 0.5)"
            ),
            row=row, col=1
        )
        self.base_figure.add_trace(
            go.Scatter(
                x=strategy_data.trade_fill.timestamp,
                y=[min(0, realized_pnl) for realized_pnl in strategy_data.trade_fill["realized_trade_pnl"].apply(lambda x: round(x, 4))],
                name="Cum Loss",
                mode='lines',
                line=dict(shape="hv", color="rgba(1, 1, 1, 0.5)", dash="dash", width=0.3),
                # marker=dict(symbol="arrow"),
                fill="tozeroy",  # Fill to the line below (trade pnl)
                fillcolor="rgba(255, 0, 0, 0.5)",
            ),
            row=row, col=1
        )
        self.base_figure.add_trace(
            go.Scatter(
                x=strategy_data.trade_fill.timestamp,
                y=strategy_data.trade_fill["cum_fees_in_quote"].apply(lambda x: round(x, 4)),
                name="Cum Fees",
                mode='lines',
                line=dict(shape="hv", color="rgba(1, 1, 1, 0.1)", dash="dash", width=0.1),
                fill="tozeroy",  # Fill to the line below (trade pnl)
                fillcolor="rgba(51, 0, 51, 0.5)"
            ),
            row=row, col=1
        )
        self.base_figure.add_trace(go.Scatter(name="Net Realized Profit",
                                              x=strategy_data.trade_fill.timestamp,
                                              y=strategy_data.trade_fill["net_realized_pnl"],
                                              mode="lines",
                                              line=dict(shape="hv")),
                                   row=row, col=1
                                   )
        self.base_figure.update_yaxes(title_text='PNL', row=row, col=1)

    def add_positions(self, position_executor_data: pd.DataFrame, row=1):
        position_executor_data["close_datetime"] = pd.to_datetime(position_executor_data["close_timestamp"], unit="s")
        for index, rown in position_executor_data.iterrows():
            self.base_figure.add_trace(go.Scatter(name=f"Position {index}",
                                                  x=[rown.datetime, rown.close_datetime],
                                                  y=[rown.entry_price, rown.close_price],
                                                  mode="lines",
                                                  line=dict(color="lightgreen" if rown.net_pnl_quote > 0 else "red"),
                                                  showlegend=False),
                                        row=row, col=1)

    def update_layout(self):
        self.base_figure.update_layout(
            title={
                'text': "Market activity",
                'y': 0.99,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            legend=dict(
                orientation="h",
                x=0.5,
                y=1.04,
                xanchor="center",
                yanchor="bottom"
            ),
            height=1000,
            xaxis=dict(rangeslider_visible=False,
                       range=[self.min_time, self.max_time]),
            yaxis=dict(range=[self.candles_df.low.min(), self.candles_df.high.max()]),
            hovermode='x unified'
        )
        self.base_figure.update_yaxes(title_text="Price", row=1, col=1)
        if self.show_volume:
            self.base_figure.update_yaxes(title_text="Volume", row=2, col=1)
        self.base_figure.update_xaxes(title_text="Time", row=self.rows, col=1)


class BacktestingGraphs:
    def __init__(self, study_df: pd.DataFrame):
        self.study_df = study_df

    def pnl_vs_maxdrawdown(self):
        fig = go.Figure()
        fig.add_trace(go.Scatter(name="Pnl vs Max Drawdown",
                                 x=-100 * self.study_df["max_drawdown_pct"],
                                 y=100 * self.study_df["net_pnl_pct"],
                                 mode="markers",
                                 text=None,
                                 hovertext=self.study_df["hover_text"]))
        fig.update_layout(
            title="PnL vs Max Drawdown",
            xaxis_title="Max Drawdown [%]",
            yaxis_title="Net Profit [%]",
            height=800
        )
        fig.data[0].text = []
        return fig

    @staticmethod
    def get_trial_metrics(strategy_analysis: StrategyAnalysis,
                          add_volume: bool = True,
                          add_positions: bool = True,
                          add_pnl: bool = True):
        """Isolated method because it needs to be called from analyze and simulate pages"""
        metrics_container = st.container()
        with metrics_container:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🏦 Market")
            with col2:
                st.subheader("📋 General stats")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Exchange", st.session_state["strategy_params"]["exchange"])
            with col2:
                st.metric("Trading Pair", st.session_state["strategy_params"]["trading_pair"])
            with col3:
                st.metric("Start date", strategy_analysis.start_date().strftime("%Y-%m-%d %H:%M"))
                st.metric("End date", strategy_analysis.end_date().strftime("%Y-%m-%d %H:%M"))
            with col4:
                st.metric("Duration (hours)", f"{strategy_analysis.duration_in_minutes() / 60:.2f}")
                st.metric("Price change", st.session_state["strategy_params"]["trading_pair"])
            st.subheader("📈 Performance")
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
            with col1:
                st.metric("Net PnL USD",
                          f"{strategy_analysis.net_profit_usd():.2f}",
                          delta=f"{100 * strategy_analysis.net_profit_pct():.2f}%",
                          help="The overall profit or loss achieved.")
            with col2:
                st.metric("Total positions",
                          f"{strategy_analysis.total_positions()}",
                          help="The total number of closed trades, winning and losing.")
            with col3:
                st.metric("Accuracy",
                          f"{100 * (len(strategy_analysis.win_signals()) / strategy_analysis.total_positions()):.2f} %",
                          help="The percentage of winning trades, the number of winning trades divided by the"
                               " total number of closed trades")
            with col4:
                st.metric("Profit factor",
                          f"{strategy_analysis.profit_factor():.2f}",
                          help="The amount of money the strategy made for every unit of money it lost, "
                               "gross profits divided by gross losses.")
            with col5:
                st.metric("Max Drawdown",
                          f"{strategy_analysis.max_drawdown_usd():.2f}",
                          delta=f"{100 * strategy_analysis.max_drawdown_pct():.2f}%",
                          help="The greatest loss drawdown, i.e., the greatest possible loss the strategy had compared "
                               "to its highest profits")
            with col6:
                st.metric("Avg Profit",
                          f"{strategy_analysis.avg_profit():.2f}",
                          help="The sum of money gained or lost by the average trade, Net Profit divided by "
                               "the overall number of closed trades.")
            with col7:
                st.metric("Avg Minutes",
                          f"{strategy_analysis.avg_trading_time_in_minutes():.2f}",
                          help="The average number of minutes that elapsed during trades for all closed trades.")
            with col8:
                st.metric("Sharpe Ratio",
                          f"{strategy_analysis.sharpe_ratio():.2f}",
                          help="The Sharpe ratio is a measure that quantifies the risk-adjusted return of an investment"
                               " or portfolio. It compares the excess return earned above a risk-free rate per unit of"
                               " risk taken.")

            st.plotly_chart(strategy_analysis.pnl_over_time(), use_container_width=True)
            strategy_analysis.create_base_figure(volume=add_volume, positions=add_positions, trade_pnl=add_pnl)
            st.plotly_chart(strategy_analysis.figure(), use_container_width=True)
        return metrics_container


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

    def summary_chart(self):
        fig = px.bar(self.strategy_data.strategy_summary, x="Trading Pair", y="Realized PnL", color="Exchange")
        fig.update_traces(width=min(1.0, 0.1 * len(self.strategy_data.strategy_summary)))
        return fig

    def pnl_over_time(self):
        df = self.strategy_data.trade_fill.copy()
        df.reset_index(drop=True, inplace=True)
        df_above = df[df['net_realized_pnl'] >= 0]
        df_below = df[df['net_realized_pnl'] < 0]

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Cum Realized PnL",
                             x=df_above.index,
                             y=df_above["net_realized_pnl"],
                             marker_color=BULLISH_COLOR,
                             # hoverdq
                             showlegend=False))
        fig.add_trace(go.Bar(name="Cum Realized PnL",
                             x=df_below.index,
                             y=df_below["net_realized_pnl"],
                             marker_color=BEARISH_COLOR,
                             showlegend=False))
        fig.update_layout(title=dict(
            text='Cummulative PnL',  # Your title text
            x=0.43,
            y=0.95,
        ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)')
        return fig

    def intraday_performance(self):
        df = self.strategy_data.trade_fill.copy()

        def hr2angle(hr):
            return (hr * 15) % 360

        def hr_str(hr):
            # Normalize hr to be between 1 and 12
            hr_string = str(((hr - 1) % 12) + 1)
            suffix = ' AM' if (hr % 24) < 12 else ' PM'
            return hr_string + suffix

        df["hour"] = df["timestamp"].dt.hour
        realized_pnl_per_hour = df.groupby("hour")[["realized_pnl", "quote_volume"]].sum().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Barpolar(
            name="Profits",
            r=realized_pnl_per_hour["quote_volume"],
            theta=realized_pnl_per_hour["hour"] * 15,
            marker=dict(
                color=realized_pnl_per_hour["realized_pnl"],
                colorscale="RdYlGn",
                cmin=-(abs(realized_pnl_per_hour["realized_pnl"]).max()),
                cmid=0.0,
                cmax=(abs(realized_pnl_per_hour["realized_pnl"]).max()),
                colorbar=dict(
                    title='Realized PnL',
                    x=0,
                    y=-0.5,
                    xanchor='left',
                    yanchor='bottom',
                    orientation='h'
                )
            )))
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

    def returns_histogram(self):
        df = self.strategy_data.trade_fill.copy()
        fig = go.Figure()
        fig.add_trace(go.Histogram(name="Losses",
                                   x=df.loc[df["realized_pnl"] < 0, "realized_pnl"],
                                   marker_color=BEARISH_COLOR))
        fig.add_trace(go.Histogram(name="Profits",
                                   x=df.loc[df["realized_pnl"] > 0, "realized_pnl"],
                                   marker_color=BULLISH_COLOR))
        fig.update_layout(
            title=dict(
                                text='Returns Distribution',
                                x=0.5,
                                xanchor="center",
                            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=.48
            ))
        return fig

    def position_executor_summary_sunburst(self):
        if self.strategy_data.position_executor is not None:
            df = self.strategy_data.position_executor.copy()
            grouped_df = df.groupby(["trading_pair", "side", "close_type"]).size().reset_index(name="count")

            fig = px.sunburst(grouped_df,
                              path=['trading_pair', 'side', 'close_type'],
                              values="count",
                              color_continuous_scale='RdBu',
                              color_continuous_midpoint=0)

            fig.update_layout(
                title=dict(
                    text='Position Executor Summary',
                    x=0.5,
                    xanchor="center",
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=.48
                )
            )
            return fig
        else:
            return None

    def candles_graph(self, candles: pd.DataFrame, show_volume=False, extra_rows=2):
        cg = CandlesGraph(candles, show_volume=show_volume, extra_rows=extra_rows)
        cg.add_buy_trades(self.strategy_data.buys)
        cg.add_sell_trades(self.strategy_data.sells)
        cg.add_pnl(self.strategy_data, row=2)
        cg.add_quote_inventory_change(self.strategy_data, row=3)
        if self.strategy_data.position_executor is not None:
            cg.add_positions(self.strategy_data.position_executor, row=1)
        return cg.figure()
