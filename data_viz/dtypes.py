from pydantic import BaseModel


class IndicatorConfig(BaseModel):
    visible: bool = True
    title: str
    row: int
    col: int
    color: str = 'black'
    length: int = None
    std: float = None
    fast: int = None
    slow: int = None
    signal: int = None


class PositionsVisualConfig(BaseModel):
    show: bool = True
    color: str = 'black'
    size: int = 20
    line_width: float = 0.7
    buy_symbol: str = 'triangle-up'
    sell_symbol: str = 'triangle-down'
    profitable_color: str = 'green'
    non_profitable_color: str = 'red'


MACD_EXAMPLE_CONFIG = IndicatorConfig(visible=True, title="macd", row=1, col=1, color="red", fast=12, slow=26, signal=9)
RSI_EXAMPLE_CONFIG = IndicatorConfig(visible=True, title="rsi", row=2, col=3, color="green", length=14)
BBANDS_EXAMPLE_CONFIG = IndicatorConfig(visible=True, title="bbands", row=1, col=1, color="blue", length=20, std=2.0)
EMA_EXAMPLE_CONFIG = IndicatorConfig(visible=True, title="ema", row=1, col=1, color="yellow", length=20, culo="asd")
