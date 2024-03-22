from typing import List
import json
import os

from data_viz.dtypes import IndicatorConfig

example_case = [
    IndicatorConfig(visible=True, title="bbands", row=1, col=1, color="blue", length=20, std=2.0),
    IndicatorConfig(visible=True, title="ema", row=1, col=1, color="yellow", length=20),
    IndicatorConfig(visible=True, title="ema", row=1, col=1, color="yellow", length=40),
    IndicatorConfig(visible=True, title="ema", row=1, col=1, color="yellow", length=60),
    IndicatorConfig(visible=True, title="ema", row=1, col=1, color="yellow", length=80),
    IndicatorConfig(visible=True, title="macd", row=2, col=1, color="red", fast=12, slow=26, signal=9),
    IndicatorConfig(visible=True, title="rsi", row=3, col=1, color="green", length=14)
]
INDICATORS_CONFIG_PATH = "data_viz/config"


def dump_indicators_config(indicators_config: List[IndicatorConfig], name: str):
    dump = [config.dict() for config in indicators_config]
    path = os.path.join(INDICATORS_CONFIG_PATH, f"{name}.json")
    with open(path, "w") as f:
        json.dump(dump, f)


def load_indicators_config(path: str):
    with open(path, "r") as f:
        data = json.load(f)
    return [IndicatorConfig.parse_obj(config) for config in data]


def get_indicators_config_paths():
    return [os.path.join(INDICATORS_CONFIG_PATH, file) for file in os.listdir(INDICATORS_CONFIG_PATH) if file != ".gitignore"]


if __name__ == "__main__":
    dump_indicators_config(example_case, "config/example_case.json")
