from decimal import Decimal

from hummingbot.core.data_type.common import OrderType
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class MarketBuyExample(ScriptStrategyBase):
    order_amount = Decimal("0.001")
    buy_executed = False
    exchange = "mexc"
    trading_pair = "BTC-USDT"
    markets = {exchange: {trading_pair}}

    def on_tick(self):
        if not self.buy_executed:
            self.buy_executed = True
            self.buy(connector_name=self.exchange, trading_pair=self.trading_pair, amount=self.order_amount,
                     order_type=OrderType.MARKET)
