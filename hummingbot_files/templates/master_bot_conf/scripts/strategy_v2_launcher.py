import inspect
import os
import importlib.util

from hummingbot.core.data_type.common import OrderType, PositionMode, TradeType, PositionSide, PositionAction
from hummingbot.smart_components.strategy_frameworks.data_types import (
    ExecutorHandlerStatus,
)
from hummingbot.smart_components.strategy_frameworks.directional_trading import DirectionalTradingControllerBase, \
    DirectionalTradingControllerConfigBase, DirectionalTradingExecutorHandler
from hummingbot.smart_components.utils.config_encoder_decoder import ConfigEncoderDecoder
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


def load_controllers(path):
    controllers = {}
    for filename in os.listdir(path):
        if filename.endswith('.py') and "__init__" not in filename:
            module_name = filename[:-3]  # strip the .py to get the module name
            controllers[module_name] = {"module": module_name}
            file_path = os.path.join(path, filename)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, DirectionalTradingControllerBase) and cls is not DirectionalTradingControllerBase:
                    controllers[module_name]["class"] = cls
                if issubclass(cls, DirectionalTradingControllerConfigBase) and cls is not DirectionalTradingControllerConfigBase:
                    controllers[module_name]["config"] = cls
    return controllers


def initialize_controller_from_config(encoder_decoder: ConfigEncoderDecoder,
                                      all_controllers_info: dict,
                                      controller_config_file: str):
    config = encoder_decoder.yaml_load(f"conf/controllers_config/{controller_config_file}")
    controller_info = all_controllers_info[config["strategy_name"]]
    config_instance = controller_info["config"](**config)
    controller_class = controller_info["class"](config_instance)
    return controller_class


class StrategyV2Launcher(ScriptStrategyBase):
    controller_configs = os.getenv("controller_configs", "bollinger_8044.yml,bollinger_8546.yml,bollinger_8883.yml")
    controllers = {}
    markets = {}
    executor_handlers = {}
    encoder_decoder = ConfigEncoderDecoder(TradeType, PositionMode, OrderType)
    controllers_info = load_controllers("hummingbot/smart_components/controllers")

    for controller_config in controller_configs.split(","):
        controller = initialize_controller_from_config(encoder_decoder, controllers_info, controller_config)
        markets = controller.update_strategy_markets_dict(markets)
        controllers[controller_config] = controller

    def __init__(self, connectors):
        super().__init__(connectors)
        for controller_config, controller in self.controllers.items():
            self.executor_handlers[controller_config] = DirectionalTradingExecutorHandler(strategy=self, controller=controller)

    def on_stop(self):
        for connector in self.connectors.keys():
            if self.is_perpetual(connector):
                self.close_open_positions(connector)
        for executor_handler in self.executor_handlers.values():
            executor_handler.stop()

    @staticmethod
    def is_perpetual(exchange):
        """
        Checks if the exchange is a perpetual market.
        """
        return "perpetual" in exchange

    def close_open_positions(self, exchange):
        connector = self.connectors[exchange]
        for trading_pair, position in connector.account_positions.items():
            if position.position_side == PositionSide.LONG:
                self.sell(connector_name=exchange,
                          trading_pair=position.trading_pair,
                          amount=abs(position.amount),
                          order_type=OrderType.MARKET,
                          price=connector.get_mid_price(position.trading_pair),
                          position_action=PositionAction.CLOSE)
            elif position.position_side == PositionSide.SHORT:
                self.buy(connector_name=exchange,
                         trading_pair=position.trading_pair,
                         amount=abs(position.amount),
                         order_type=OrderType.MARKET,
                         price=connector.get_mid_price(position.trading_pair),
                         position_action=PositionAction.CLOSE)

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
        for controller_config, executor_handler in self.executor_handlers.items():
            lines.extend(["\n------------------------------------------------------------------------------------------"])
            lines.extend([f"Strategy: {executor_handler.controller.config.strategy_name} | Config: {controller_config}",
            executor_handler.to_format_status()])
        return "\n".join(lines)
