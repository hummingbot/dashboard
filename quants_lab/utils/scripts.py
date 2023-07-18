import os
import glob
from typing import Union
import inspect
import importlib.util


# TODO: Find a nice library to do this
def check_code(code: str = "") -> Union[str, None]:
    """
    Check code for PEP errors, warnings, and syntax errors.

    Args:
        code (str, optional): Code string to be checked. Defaults to "".

    Returns:
        Union[str, None]: A list of PEP errors/warnings and syntax errors, or None if no errors are found.
    """
    return None


def save_script(name: str, content: str, path: str = "quants_lab/strategy/custom_scripts"):
    complete_file_path = os.path.join(path, name)
    os.makedirs(path, exist_ok=True)
    with open(complete_file_path, "w") as file:
        file.write(content)


def load_candles(directory: str) -> list:
    candles_files = glob.glob(directory + "/**/*.csv", recursive=True)
    return candles_files


def load_scripts(directory: str) -> list:
    py_files = glob.glob(directory + "/**/*.py", recursive=True)
    py_files = [path for path in py_files if not path.endswith("__init__.py")]
    return py_files


def open_and_read_file(path: str) -> str:
    try:
        with open(path, 'r') as file:
            contents = file.read()
        return contents
    except FileNotFoundError:
        print(f"File '{path}' not found.")
        return ""
    except IOError:
        print(f"Error reading file '{path}'.")
        return ""


def load_classes_from_file(file_path):
    # module_name = inspect.getmodulename(file_path)
    module_name = "Drupman"
    file_path = "quants_lab/strategy/custom_scripts/Drupman.py"
    # Load the module
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Get all the classes from the module
    classes = []
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj):
            classes.append((name, obj))

    return [(name, cls) for name, cls in classes if name != 'DirectionalStrategyBase']


def directional_strategy_template(strategy_name: str,
                                  exchange: str,
                                  trading_pair: str,
                                  interval: str) -> str:
    return f"""import pandas_ta as ta
import pandas as pd
import numpy as np

from quants_lab.strategy.directional_strategy_base import DirectionalStrategyBase
from quants_lab.utils import data_management



class {strategy_name}(DirectionalStrategyBase):
    def __init__(self,
                 exchange="{exchange}",
                 trading_pair="{trading_pair}",
                 interval="{interval}"):
        self.exchange = exchange
        self.trading_pair = trading_pair
        self.interval = interval
        # ... Define other class attributes here

    def get_raw_data(self):
        df = data_management.get_dataframe(
            exchange=self.exchange,
            trading_pair=self.trading_pair,
            interval=self.interval,
        )
        return df

    def add_indicators(self, df):
        df.ta.sma(length=20, append=True)
        # ... Add more indicators here
        # ... Check https://github.com/twopirllc/pandas-ta#indicators-by-category for more indicators
        # ... Use help(ta.indicator_name) to get more info
        return df

    def add_signals(self, df):
        # ... Do your own logic
        random_series = pd.Series(np.random.randint(low=0, high=101, size=100))
        random_series_2 = pd.Series(np.random.randint(low=0, high=101, size=100))
        random_thold = np.random.randint(low=45, high=65)
        random_thold_2 = np.random.randint(low=45, high=65)
        
        # Generate long and short conditions
        macd_long_cond = (random_series > random_thold) & (random_series_2 > random_thold_2)
        macd_short_cond = (random_series < random_thold) & (random_series_2 > random_thold_2)

        # Choose side
        df['side'] = 0
        df.loc[macd_long_cond, 'side'] = 1
        df.loc[macd_short_cond, 'side'] = -1
        return df
"""
