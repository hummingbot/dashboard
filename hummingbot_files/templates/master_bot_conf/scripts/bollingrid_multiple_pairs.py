from decimal import Decimal
from typing import Dict

from hummingbot.core.data_type.common import PositionSide, PositionAction, OrderType
from hummingbot.smart_components.controllers.bollinger_grid import BollingerGridConfig, BollingerGrid
from hummingbot.connector.connector_base import ConnectorBase, TradeType
from hummingbot.data_feed.candles_feed.candles_factory import CandlesConfig
from hummingbot.smart_components.strategy_frameworks.data_types import (
    ExecutorHandlerStatus,
    OrderLevel,
    TripleBarrierConf,
)
from hummingbot.smart_components.strategy_frameworks.market_making.market_making_executor_handler import (
    MarketMakingExecutorHandler,
)
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class BollingridMultiplePairs(ScriptStrategyBase):
    trading_pairs_v2 = ["RUNE-USDT", "AGLD-USDT", "WLD-USDT", "OMG-USDT", "PERP-USDT", "API3-USDT", "TOMO-USDT"]

    leverage_by_trading_pair = {
        "HBAR-USDT": 25,
        "CYBER-USDT": 20,
        "ETH-USDT": 100,
        "LPT-USDT": 10,
        "UNFI-USDT": 20,
        "BAKE-USDT": 20,
        "YGG-USDT": 20,
        "SUI-USDT": 50,
        "TOMO-USDT": 25,
        "RUNE-USDT": 25,
        "STX-USDT": 25,
        "API3-USDT": 20,
        "LIT-USDT": 20,
        "PERP-USDT": 16,
        "HOOK-USDT": 20,
        "AMB-USDT": 20,
        "ARKM-USDT": 20,
        "TRB-USDT": 10,
        "OMG-USDT": 25,
        "WLD-USDT": 50,
        "AGLD-USDT": 20
    }

    triple_barrier_conf_top = TripleBarrierConf(
        stop_loss=Decimal("0.15"), take_profit=Decimal("0.005"),
        time_limit=60 * 60 * 24,
        take_profit_order_type=OrderType.LIMIT,
    )
    triple_barrier_conf_bottom = TripleBarrierConf(
        stop_loss=Decimal("0.15"), take_profit=Decimal("0.04"),
        time_limit=60 * 60 * 24,
        trailing_stop_activation_price_delta=Decimal("0.015"),
        trailing_stop_trailing_delta=Decimal("0.005"),
    )
    order_amount_top = Decimal("35")
    order_levels = [
        OrderLevel(level=0, side=TradeType.BUY, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(0.5), order_refresh_time=60 * 30,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_top),
        OrderLevel(level=1, side=TradeType.BUY, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(1.5), order_refresh_time=60 * 30,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_top),
        OrderLevel(level=2, side=TradeType.BUY, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(2.5), order_refresh_time=60 * 30,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_top),
        OrderLevel(level=3, side=TradeType.BUY, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(3.5), order_refresh_time=60 * 30,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_top),
        OrderLevel(level=4, side=TradeType.BUY, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(4.5), order_refresh_time=60 * 30,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_top),
        OrderLevel(level=5, side=TradeType.BUY, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(5.5), order_refresh_time=60 * 45,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_top),
        OrderLevel(level=6, side=TradeType.BUY, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(6.5), order_refresh_time=60 * 45,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_bottom),
        OrderLevel(level=7, side=TradeType.BUY, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(7.5), order_refresh_time=60 * 45,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_bottom),
        OrderLevel(level=8, side=TradeType.BUY, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(8.5), order_refresh_time=60 * 45,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_bottom),
        OrderLevel(level=9, side=TradeType.BUY, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(9.5), order_refresh_time=60 * 45,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_bottom),

        OrderLevel(level=0, side=TradeType.SELL, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(0.5), order_refresh_time=60 * 30,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_top),
        OrderLevel(level=1, side=TradeType.SELL, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(1.5), order_refresh_time=60 * 30,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_top),
        OrderLevel(level=2, side=TradeType.SELL, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(2.5), order_refresh_time=60 * 30,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_top),
        OrderLevel(level=3, side=TradeType.SELL, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(3.5), order_refresh_time=60 * 30,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_top),
        OrderLevel(level=4, side=TradeType.SELL, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(4.5), order_refresh_time=60 * 30,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_top),
        OrderLevel(level=5, side=TradeType.SELL, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(5.5), order_refresh_time=60 * 45,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_top),
        OrderLevel(level=6, side=TradeType.SELL, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(6.5), order_refresh_time=60 * 45,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_bottom),
        OrderLevel(level=7, side=TradeType.SELL, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(7.5), order_refresh_time=60 * 45,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_bottom),
        OrderLevel(level=8, side=TradeType.SELL, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(8.5), order_refresh_time=60 * 45,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_bottom),
        OrderLevel(level=9, side=TradeType.SELL, order_amount_usd=Decimal(order_amount_top),
                   spread_factor=Decimal(9.5), order_refresh_time=60 * 45,
                   cooldown_time=15, triple_barrier_conf=triple_barrier_conf_bottom),
    ]
    controllers = {}
    markets = {}
    executor_handlers = {}

    for trading_pair in trading_pairs_v2:
        config = BollingerGridConfig(
            exchange="binance_perpetual",
            trading_pair=trading_pair,
            order_levels=order_levels,
            candles_config=[
                CandlesConfig(connector="binance_perpetual", trading_pair=trading_pair, interval="1h", max_records=300),
            ],
            leverage=leverage_by_trading_pair[trading_pair],
            bb_length=200,
            natr_length=200,
        )
        controller = BollingerGrid(config=config)
        markets = controller.update_strategy_markets_dict(markets)
        controllers[trading_pair] = controller

    def __init__(self, connectors: Dict[str, ConnectorBase]):
        super().__init__(connectors)
        for trading_pair, controller in self.controllers.items():
            self.executor_handlers[trading_pair] = MarketMakingExecutorHandler(strategy=self, controller=controller)

    def on_stop(self):
        self.close_open_positions()
        for executor_handler in self.executor_handlers.values():
            executor_handler.stop()

    def on_tick(self):
        """
        This shows you how you can start meta controllers. You can run more than one at the same time and based on the
        market conditions, you can orchestrate from this script when to stop or start them.
        """
        for executor_handler in self.executor_handlers.values():
            if executor_handler.status == ExecutorHandlerStatus.NOT_STARTED:
                executor_handler.start()

    def format_status(self) -> str:
        if not self.ready_to_trade:
            return "Market connectors are not ready."
        lines = []
        for trading_pair, executor_handler in self.executor_handlers.items():
            lines.extend([f"Strategy: {executor_handler.controller.config.strategy_name} | Trading Pair: {trading_pair}",
            executor_handler.to_format_status()])
        return "\n".join(lines)

    def close_open_positions(self):
        # we are going to close all the open positions when the bot stops
        for connector_name, connector in self.connectors.items():
            for trading_pair, position in connector.account_positions.items():
                if position.position_side == PositionSide.LONG:
                    self.sell(connector_name=connector_name,
                              trading_pair=position.trading_pair,
                              amount=abs(position.amount),
                              order_type=OrderType.MARKET,
                              price=connector.get_mid_price(position.trading_pair),
                              position_action=PositionAction.CLOSE)
                elif position.position_side == PositionSide.SHORT:
                    self.buy(connector_name=connector_name,
                             trading_pair=position.trading_pair,
                             amount=abs(position.amount),
                             order_type=OrderType.MARKET,
                             price=connector.get_mid_price(position.trading_pair),
                             position_action=PositionAction.CLOSE)
