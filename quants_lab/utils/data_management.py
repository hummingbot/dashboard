import os

import pandas as pd


def get_dataframe(exchange: str, trading_pair: str, interval: str) -> pd.DataFrame:
    """
    Get a dataframe of market data from the database.
    :param exchange: Exchange name
    :param trading_pair: Trading pair
    :param interval: Interval of the data
    :return: Dataframe of market data
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "../../data/candles")
    filename = f"candles_{exchange}_{trading_pair.upper()}_{interval}.csv"
    file_path = os.path.join(data_dir, filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' does not exist.")
    df = pd.read_csv(file_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df
