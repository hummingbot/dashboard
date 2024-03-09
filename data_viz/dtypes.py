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

    # TODO: throw error if indicator is not available
    # @validator("title")
    # def indicator_is_available(cls, value):
    #     if value not in ["bbands, ema, macd, rsi"]:
    #         raise ValueError(f"{value} is not a valid indicator. Choose from bbands, ema, macd, rsi")
    #     return value


class PositionsVisualConfig(BaseModel):
    show: bool = True
    color: str = 'black'
    size: int = 20
    line_width: float = 0.7
    buy_symbol: str = 'triangle-up'
    sell_symbol: str = 'triangle-down'
    profitable_color: str = 'green'
    non_profitable_color: str = 'red'
