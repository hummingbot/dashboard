import plotly.graph_objs as go
import pandas as pd
from data_viz.dtypes import IndicatorsConfigBase
from data_viz.dtypes import PositionsVisualConfig
from datetime import datetime


BULLISH_COLOR = "rgba(97, 199, 102, 0.9)"
BEARISH_COLOR = "rgba(255, 102, 90, 0.9)"
FEE_COLOR = "rgba(51, 0, 51, 0.9)"


class PandasTAPlotlyTracer:
    def __init__(self, candles_df: pd.DataFrame, indicators_config: IndicatorsConfigBase):
        """
        :param candles_df: candles dataframe with timestamp as index
        """
        self.candles_df = candles_df
        self.indicators_config = indicators_config

    @staticmethod
    def raise_error_if_not_enough_data(indicator_title: str):
        print(f"Not enough data to calculate {indicator_title}")

    def get_bollinger_bands_traces(self):
        config = self.indicators_config.bollinger_bands.copy()
        self.candles_df.ta.bbands(length=config.length, std=config.std, append=True)
        if len(self.candles_df) < config.length:
            self.raise_error_if_not_enough_data(config.title)
            return
        else:
            bbu_trace = go.Scatter(x=self.candles_df.index,
                                   y=self.candles_df[f'BBU_{config.length}_{config.std}'],
                                   name=f'BBU_{config.length}_{config.std}',
                                   mode='lines',
                                   line=dict(color=config.color, width=1))
            bbm_trace = go.Scatter(x=self.candles_df.index,
                                   y=self.candles_df[f'BBM_{config.length}_{config.std}'],
                                   name=f'BBM_{config.length}_{config.std}',
                                   mode='lines',
                                   line=dict(color=config.color, width=1))
            bbl_trace = go.Scatter(x=self.candles_df.index,
                                   y=self.candles_df[f'BBL_{config.length}_{config.std}'],
                                   name=f'BBL_{config.length}_{config.std}',
                                   mode='lines',
                                   line=dict(color=config.color, width=1))
            return bbu_trace, bbm_trace, bbl_trace

    def get_ema_traces(self):
        config = self.indicators_config.ema.copy()
        if len(self.candles_df) < config.length:
            self.raise_error_if_not_enough_data(config.title)
            return
        else:
            self.candles_df.ta.ema(length=config.length, append=True)
            ema_trace = go.Scatter(x=self.candles_df.index,
                                   y=self.candles_df[f'EMA_{config.length}'],
                                   name=f'EMA_{config.length}',
                                   mode='lines',
                                   line=dict(color=config.color, width=1))
            return ema_trace

    def get_macd_traces(self, fast=12, slow=26, signal=9):
        config = self.indicators_config.macd.copy()
        if len(self.candles_df) < any([config.fast, config.slow, config.signal]):
            self.raise_error_if_not_enough_data(config.title)
            return
        else:
            self.candles_df.ta.macd(fast=fast, slow=slow, signal=signal, append=True)
            macd_trace = go.Scatter(x=self.candles_df.index,
                                    y=self.candles_df[f'MACD_{fast}_{slow}_{signal}'],
                                    name=f'MACD_{fast}_{slow}_{signal}',
                                    mode='lines',
                                    line=dict(color=config.color, width=1))
            macd_signal_trace = go.Scatter(x=self.candles_df.index,
                                           y=self.candles_df[f'MACDs_{fast}_{slow}_{signal}'],
                                           name=f'MACDs_{fast}_{slow}_{signal}',
                                           mode='lines',
                                           line=dict(color=config.color, width=1))
            macd_hist_trace = go.Bar(x=self.candles_df.index,
                                     y=self.candles_df[f'MACDh_{fast}_{slow}_{signal}'],
                                     name=f'MACDh_{fast}_{slow}_{signal}',
                                     marker=dict(color=config.color))
            return macd_trace, macd_signal_trace, macd_hist_trace

    def get_rsi_traces(self, length=14):
        config = self.indicators_config.rsi.copy()
        if len(self.candles_df) < config.length:
            self.raise_error_if_not_enough_data(config.title)
            return
        else:
            self.candles_df.ta.rsi(length=length, append=True)
            rsi_trace = go.Scatter(x=self.candles_df.index,
                                   y=self.candles_df[f'RSI_{length}'],
                                   name=f'RSI_{length}',
                                   mode='lines',
                                   line=dict(color=config.color, width=1))
            return rsi_trace


class PerformancePlotlyTracer:
    def __init__(self,
                 positions_visual_config: PositionsVisualConfig = PositionsVisualConfig()):
        self.positions_visual_config = positions_visual_config

    @staticmethod
    def get_buys_traces(data: pd.Series):
        buy_trades_trace = go.Scatter(
            x=data.index,
            y=data.values,
            name="Buy Orders",
            mode="markers",
            marker=dict(
                symbol="triangle-up",
                color="green",
                size=12,
                line=dict(color="black", width=1),
                opacity=0.7,
            ),
            hoverinfo="text",
            hovertext=data.apply(lambda x: f"Buy Order: {x} <br>")
        )
        return buy_trades_trace

    @staticmethod
    def get_sells_traces(data: pd.Series):
        sell_trades_trace = go.Scatter(
            x=data.index,
            y=data.values,
            name="Sell Orders",
            mode="markers",
            marker=dict(
                symbol="triangle-down",
                color="red",
                size=12,
                line=dict(color="black", width=1),
                opacity=0.7,
            ),
            hoverinfo="text",
            hovertext=data.apply(lambda x: f"Sell Order: {x} <br>")
        )
        return sell_trades_trace

    @staticmethod
    def get_positions_traces(position_number: int,
                             open_time: datetime,
                             close_time: datetime,
                             open_price: float,
                             close_price: float,
                             side: int,
                             close_type: str,
                             stop_loss: float,
                             take_profit: float,
                             time_limit: float,
                             net_pnl_quote: float):
        """
        Draws a line between the open and close price of a position
        """
        positions_trace = go.Scatter(name=f"Position {position_number}",
                                     x=[open_time, close_time],
                                     y=[open_price, close_price],
                                     mode="lines",
                                     line=dict(color="lightgreen" if net_pnl_quote > 0 else "red"),
                                     hoverinfo="text",
                                     hovertext=f"Position N°: {position_number} <br>"
                                               f"Open datetime: {open_time} <br>"
                                               f"Close datetime: {close_time} <br>"
                                               f"Side: {side} <br>"
                                               f"Entry price: {open_price} <br>"
                                               f"Close price: {close_price} <br>"
                                               f"Close type: {close_type} <br>"
                                               f"Stop Loss: {100 * stop_loss:.2f}% <br>"
                                               f"Take Profit: {100 * take_profit:.2f}% <br>"
                                               f"Time Limit: {time_limit} <br>",
                                     showlegend=False)
        return positions_trace

    @staticmethod
    def get_realized_pnl_over_trading_pair_traces(data: pd.DataFrame(), trading_pair: str, realized_pnl: str, exchange: str):
        realized_pnl_over_trading_pair_traces = go.Bar(x=data[trading_pair],
                                                       y=data[realized_pnl],
                                                       name=exchange,
                                                       showlegend=True)
        return realized_pnl_over_trading_pair_traces

    @staticmethod
    def get_realized_pnl_over_time_traces(data: pd.DataFrame(), cum_realized_pnl_column: str):
        realized_pnl_over_time_traces = go.Bar(name="Cum Realized PnL",
                                               x=[x + 1 for x in range(len(data))],
                                               y=data[cum_realized_pnl_column],
                                               marker_color=data[cum_realized_pnl_column].apply(lambda x: BULLISH_COLOR if x > 0 else BEARISH_COLOR),
                                               showlegend=False)
        return realized_pnl_over_time_traces

    @staticmethod
    def get_pnl_vs_max_drawdown_traces(data: pd.DataFrame(), max_drawdown_pct_column: str, net_pnl_pct_column: str,
                                       hovertext_column: str):
        pnl_vs_max_drawdown_traces = go.Scatter(name="Pnl vs Max Drawdown",
                                                x=-100 * data[max_drawdown_pct_column],
                                                y=100 * data[net_pnl_pct_column],
                                                mode="markers",
                                                text=None,
                                                hovertext=data[hovertext_column])
        return pnl_vs_max_drawdown_traces

    @staticmethod
    def get_composed_pnl_traces(data: pd.DataFrame(), realized_pnl_column: str, fees_column: str,
                                net_realized_pnl_column: str):
        cum_profit_trace = go.Scatter(
                x=data.timestamp,
                y=[max(0, realized_pnl) for realized_pnl in data[realized_pnl_column].apply(lambda x: round(x, 4))],
                name="Cum Profit",
                mode='lines',
                line=dict(shape="hv", color="rgba(1, 1, 1, 0.5)", dash="dash", width=0.1),
                fill="tozeroy",
                fillcolor="rgba(0, 255, 0, 0.5)"
            )
        cum_loss_trace = go.Scatter(
                x=data.timestamp,
                y=[min(0, realized_pnl) for realized_pnl in data[realized_pnl_column].apply(lambda x: round(x, 4))],
                name="Cum Loss",
                mode='lines',
                line=dict(shape="hv", color="rgba(1, 1, 1, 0.5)", dash="dash", width=0.3),
                fill="tozeroy",
                fillcolor="rgba(255, 0, 0, 0.5)",
            )
        cum_fees_trace = go.Scatter(
                x=data.timestamp,
                y=data[fees_column].apply(lambda x: round(x, 4)),
                name="Cum Fees",
                mode='lines',
                line=dict(shape="hv", color="rgba(1, 1, 1, 0.1)", dash="dash", width=0.1),
                fill="tozeroy",
                fillcolor="rgba(51, 0, 51, 0.5)"
            )
        net_realized_profit_trace = go.Scatter(name="Net Realized Profit",
                                               x=data.timestamp,
                                               y=data[net_realized_pnl_column],
                                               mode="lines",
                                               line=dict(shape="hv"))
        composed_pnl_traces = [cum_profit_trace, cum_loss_trace, cum_fees_trace, net_realized_profit_trace]
        return composed_pnl_traces

    @staticmethod
    def get_quote_inventory_change(data: pd.DataFrame, quote_inventory_change_column: str):
        quote_inventory_change_trace = go.Scatter(name="Quote Inventory",
                                                  x=data.timestamp,
                                                  y=data[quote_inventory_change_column],
                                                  mode="lines",
                                                  line=dict(shape="hv"))
        return quote_inventory_change_trace

    @staticmethod
    def get_intraday_performance_traces(data: pd.DataFrame, quote_volume_column: str, hour_column: str, realized_pnl_column: str):
        intraday_performance_traces = go.Barpolar(
            name="Profits",
            r=data[quote_volume_column],
            theta=data[hour_column] * 15,
            marker=dict(
                color=data[realized_pnl_column],
                colorscale="RdYlGn",
                cmin=-(abs(data[realized_pnl_column]).max()),
                cmid=0.0,
                cmax=(abs(data[realized_pnl_column]).max()),
                colorbar=dict(
                    title='Realized PnL',
                    x=0,
                    y=-0.5,
                    xanchor='left',
                    yanchor='bottom',
                    orientation='h'
                )))
        return intraday_performance_traces

    @staticmethod
    def get_returns_distribution_traces(data: pd.DataFrame(), realized_pnl_column: str):
        losses = data.loc[data[realized_pnl_column] < 0, realized_pnl_column]
        profits = data.loc[data[realized_pnl_column] > 0, realized_pnl_column]
        returns_distribution_traces = [go.Histogram(name="Losses", x=losses, marker_color=BEARISH_COLOR),
                                       go.Histogram(name="Profits", x=profits, marker_color=BULLISH_COLOR)]
        return returns_distribution_traces
