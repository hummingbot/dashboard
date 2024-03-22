import os
import pandas as pd
import json
from typing import List
import streamlit as st
import plotly.graph_objs as go
from data_viz.dtypes import IndicatorConfig
import data_viz.utils as utils
import data_viz.dtypes as dtypes
from data_viz.candles import CandlesBase


def get_input_types(indicator_name: str):
    if indicator_name == "bbands":
        base_indicator_config = dtypes.BBANDS_EXAMPLE_CONFIG
    elif indicator_name == "ema":
        base_indicator_config = dtypes.EMA_EXAMPLE_CONFIG
    elif indicator_name == "macd":
        base_indicator_config = dtypes.MACD_EXAMPLE_CONFIG
    elif indicator_name == "rsi":
        base_indicator_config = dtypes.RSI_EXAMPLE_CONFIG
    else:
        raise ValueError(f"{indicator_name} is not a valid indicator. Choose from bbands, ema, macd, rsi")

    base_indicator_config_dict = vars(base_indicator_config)
    indicator_config_dict = {}
    st.markdown("### Customize your indicator")
    for attr, value in base_indicator_config_dict.items():
        if attr in ["title", "col"] or value is None:
            indicator_config_dict[attr] = value
        elif attr == "color":
            indicator_config_dict[attr] = st.color_picker(attr)
        elif isinstance(value, bool):
            indicator_config_dict[attr] = st.checkbox(attr, value=base_indicator_config_dict[attr])
        elif isinstance(value, int):
            indicator_config_dict[attr] = st.number_input(attr, value=base_indicator_config_dict[attr])
        elif isinstance(value, str):
            indicator_config_dict[attr] = st.text_input(attr, value=base_indicator_config_dict[attr])
        elif isinstance(value, float):
            indicator_config_dict[attr] = st.number_input(attr, value=base_indicator_config_dict[attr])
        else:
            raise ValueError(f"Type {value} not supported")
    return indicator_config_dict


st.set_page_config(layout="wide")
if "indicator_config_list" not in st.session_state:
    st.session_state.indicator_config_list = []

# Streamlit app
st.title("Viz Lab")

tabs = st.tabs(["Technical Indicators"])

with tabs[0]:
    st.subheader("Data Source")
    if not bool(os.listdir("data/candles")):
        st.info("No candles found in data/candles folder. Start generating a file from candles downloader page.")
    else:
        file = st.selectbox("Select candles to test:",
                            [file for file in os.listdir("data/candles") if file != ".gitignore" and file.endswith(".csv")])
        candles_df = pd.read_csv(f"data/candles/{file}")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Indicators")
            name = st.selectbox("Select an indicator", ["bbands", "ema", "macd", "rsi"])
            indicator_config = get_input_types(name)
            indicator = IndicatorConfig(**indicator_config)
            print(st.session_state.indicator_config_list)
            col1_a, col1_b = st.columns(2)
            with col1_a:
                if st.button("Add Indicator"):
                    st.session_state.indicator_config_list.append(indicator)
                    st.rerun()
            with col1_b:
                if st.button("Clear"):
                    st.session_state.indicator_config_list = []
                    st.rerun()
        with col2:
            st.subheader("Preview")
            if len(candles_df) > 0 and bool(st.session_state.indicator_config_list):
                candles = CandlesBase(candles_df.tail(300), indicators_config=st.session_state.indicator_config_list, annotations=False, max_height=600, show_indicators=True)
                st.plotly_chart(candles.figure(), use_container_width=True)
            else:
                st.info("Start adding one indicator!")
        st.subheader("Save progress")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            file_name = st.text_input("Save as:", value="example_case", label_visibility="collapsed")
        with col2:
            if st.button("Save"):
                utils.dump_indicators_config(st.session_state.indicator_config_list, file_name)
