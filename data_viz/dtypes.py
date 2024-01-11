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


class IndicatorsConfigBase(BaseModel):
    bollinger_bands: IndicatorConfig = None
    ema: IndicatorConfig = None
    macd: IndicatorConfig = None
    rsi: IndicatorConfig = None


class PositionsVisualConfig(BaseModel):
    show: bool = True
    color: str = 'black'
    size: int = 20
    line_width: float = 0.7
    buy_symbol: str = 'triangle-up'
    sell_symbol: str = 'triangle-down'
    profitable_color: str = 'green'
    non_profitable_color: str = 'red'
