from decimal import Decimal

import pandas as pd
import pandas_ta as ta

from hummingbot.core.data_type.common import TradeType, PriceType
from hummingbot.data_feed.candles_feed.candles_factory import CandlesFactory
from hummingbot.smart_components.position_executor.data_types import PositionConfig
from hummingbot.smart_components.position_executor.position_executor import PositionExecutor
from hummingbot.strategy.directional_strategy_base import DirectionalStrategyBase


class StatisticalArbitrageLeft(DirectionalStrategyBase):
    """
    BotCamp Cohort #5 July 2023
    Design Template: https://github.com/hummingbot/hummingbot-botcamp/issues/48

    Description:
    Statistical Arbitrage strategy implementation based on the DirectionalStrategyBase.
    This strategy execute trades based on the Z-score values.
    This strategy is divided into a left and right side code.
    Left side code is statistical_arbitrage_left.py.
    Right side code is statistical_arbitrage_right.py.
    This code the left side of this strategy
    When z-score indicates an entry signal. the left side will execute a long position and right side will execute a short position.
    When z-score indicates an exit signal. the left side will execute a short position and right side will execute a long position.
    """
    directional_strategy_name: str = "statistical_arbitrage"
    # Define the trading pair and exchange that we want to use and the csv where we are going to store the entries
    trading_pair: str = "ETH-USDT"  # left side trading pair
    trading_pair_2: str = "MATIC-USDT"  # right side trading pair
    exchange: str = "binance_perpetual"
    order_amount_usd = Decimal("65")
    leverage = 10
    length = 100
    max_executors = 2
    max_hours_to_hold_position = 12

    # Configure the parameters for the position
    zscore_long_threshold: int = -1.5
    zscore_short_threshold: int = 1.5

    arbitrage_take_profit = Decimal("0.01")
    arbitrage_stop_loss = Decimal("0.02")

    candles = [
        CandlesFactory.get_candle(connector=exchange,
                                  trading_pair=trading_pair,
                                  interval="1h", max_records=1000),
        CandlesFactory.get_candle(connector=exchange,
                                  trading_pair=trading_pair_2,
                                  interval="1h", max_records=1000),
    ]
    last_signal = 0
    report_frequency_in_hours = 6
    next_report_time = 0
    markets = {exchange: {trading_pair, trading_pair_2}}

    def on_tick(self):
        self.check_and_send_report()
        self.clean_and_store_executors()
        if self.is_perpetual:
            self.check_and_set_leverage()

        if self.all_candles_ready:
            signal = self.get_signal()
            if len(self.active_executors) == 0:
                position_configs = self.get_arbitrage_position_configs(signal)
                if position_configs:
                    self.last_signal = signal
                    for position_config in position_configs:
                        executor = PositionExecutor(strategy=self,
                                                    position_config=position_config)
                        self.active_executors.append(executor)
            else:
                consolidated_pnl = self.get_unrealized_pnl()
                if consolidated_pnl > self.arbitrage_take_profit or consolidated_pnl < -self.arbitrage_stop_loss:
                    self.logger().info("Exit Arbitrage")
                    for executor in self.active_executors:
                        executor.early_stop()
                    self.last_signal = 0

    def get_arbitrage_position_configs(self, signal):
        trading_pair_1_amount, trading_pair_2_amount = self.get_order_amounts()
        if signal == 1:
            buy_config = PositionConfig(
                timestamp=self.current_timestamp,
                trading_pair=self.trading_pair,
                exchange=self.exchange,
                side=TradeType.BUY,
                amount=trading_pair_1_amount,
                leverage=self.leverage,
                time_limit=int(60 * 60 * self.max_hours_to_hold_position),
            )
            sell_config = PositionConfig(
                timestamp=self.current_timestamp,
                trading_pair=self.trading_pair_2,
                exchange=self.exchange,
                side=TradeType.SELL,
                amount=trading_pair_2_amount,
                leverage=self.leverage,
                time_limit=int(60 * 60 * self.max_hours_to_hold_position),
            )
            return [buy_config, sell_config]
        elif signal == -1:
            buy_config = PositionConfig(
                timestamp=self.current_timestamp,
                trading_pair=self.trading_pair_2,
                exchange=self.exchange,
                side=TradeType.BUY,
                amount=trading_pair_2_amount,
                leverage=self.leverage,
                time_limit=int(60 * 60 * self.max_hours_to_hold_position),
            )
            sell_config = PositionConfig(
                timestamp=self.current_timestamp,
                trading_pair=self.trading_pair,
                exchange=self.exchange,
                side=TradeType.SELL,
                amount=trading_pair_1_amount,
                leverage=self.leverage,
                time_limit=int(60 * 60 * self.max_hours_to_hold_position),
            )
            return [buy_config, sell_config]

    def get_order_amounts(self):
        base_quantized_1, usd_quantized_1 = self.get_order_amount_quantized_in_base_and_usd(self.trading_pair, self.order_amount_usd)
        base_quantized_2, usd_quantized_2 = self.get_order_amount_quantized_in_base_and_usd(self.trading_pair_2, self.order_amount_usd)
        if usd_quantized_2 > usd_quantized_1:
            base_quantized_2, usd_quantized_2 = self.get_order_amount_quantized_in_base_and_usd(self.trading_pair_2, usd_quantized_1)
        elif usd_quantized_1 > usd_quantized_2:
            base_quantized_1, usd_quantized_1 = self.get_order_amount_quantized_in_base_and_usd(self.trading_pair, usd_quantized_2)
        return base_quantized_1, base_quantized_2

    def get_order_amount_quantized_in_base_and_usd(self, trading_pair: str, order_amount_usd: Decimal):
        price = self.connectors[self.exchange].get_price_by_type(trading_pair, PriceType.MidPrice)
        amount_quantized = self.connectors[self.exchange].quantize_order_amount(trading_pair, order_amount_usd / price)
        return amount_quantized, amount_quantized * price

    def get_signal(self):
        candles_df = self.get_processed_df()
        z_score = candles_df.iat[-1, -1]
        # all execution are only on the left side trading pair
        if z_score < self.zscore_long_threshold:
            return 1
        elif z_score > self.zscore_short_threshold:
            return -1
        else:
            return 0

    def get_processed_df(self):
        candles_df_1 = self.candles[0].candles_df
        candles_df_2 = self.candles[1].candles_df

        # calculate the spread and z-score based on the candles of 2 trading pairs
        df = pd.merge(candles_df_1, candles_df_2, on="timestamp", how='inner', suffixes=('', '_2'))
        hedge_ratio = df["close"].tail(self.length).mean() / df["close_2"].tail(self.length).mean()

        df["spread"] = df["close"] - (df["close_2"] * hedge_ratio)
        df["z_score"] = ta.zscore(df["spread"], length=self.length)
        return df

    def market_data_extra_info(self):
        """
        Provides additional information about the market data to the format status.
        Returns:
            List[str]: A list of formatted strings containing market data information.
        """
        lines = []
        columns_to_show = ["timestamp", "open", "low", "high", "close", "volume", "z_score", "close_2"]
        candles_df = self.get_processed_df()
        distance_to_target = self.get_unrealized_pnl() - self.arbitrage_take_profit
        lines.extend(
            [f"Consolidated PNL (%): {self.get_unrealized_pnl() * 100:.2f} | Target (%): {self.arbitrage_take_profit * 100:.2f} | Diff: {distance_to_target * 100:.2f}"],
        )
        lines.extend([f"Candles: {self.candles[0].name} | Interval: {self.candles[0].interval}\n"])
        lines.extend(self.candles_formatted_list(candles_df, columns_to_show))
        return lines

    def get_unrealized_pnl(self):
        cum_pnl = 0
        for executor in self.active_executors:
            cum_pnl += executor.net_pnl
        return cum_pnl

    def get_realized_pnl(self):
        cum_pnl = 0
        for executor in self.stored_executors:
            cum_pnl += executor.net_pnl
        return cum_pnl

    def check_and_send_report(self):
        if self.current_timestamp > self.next_report_time:
            self.notify_hb_app_with_timestamp(f"""
Closed Positions: {len(self.stored_executors)} | Realized PNL (%): {self.get_realized_pnl() * 100:.2f}
Open Positions: {len(self.active_executors)} | Unrealized PNL (%): {self.get_unrealized_pnl() * 100:.2f}
"""
            )
            self.next_report_time = self.current_timestamp + 60 * 60 * self.report_frequency_in_hours
