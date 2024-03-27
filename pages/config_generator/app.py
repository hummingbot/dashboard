import os
import pandas as pd
import streamlit as st
from typing import List
from hummingbot.data_feed.candles_feed.candles_factory import CandlesConfig

import constants
from utils.st_utils import initialize_st_page

initialize_st_page(title="Config Generator", icon="🎛️", initial_sidebar_state="collapsed")


def get_available_candles() -> List[CandlesConfig]:
    """Retrieve the available candles from the candles folder."""
    try:
        candles_config = []
        # Listing all CSV files in the specified directory
        csv_files = [f for f in os.listdir(constants.CANDLES_DATA_PATH) if f.endswith('.csv')]
        for file in csv_files:
            file_splitted = file.replace('.csv', '').split("_")
            interval = file_splitted.pop(-1)
            trading_pair = file_splitted.pop(-1)
            if len(file_splitted) == 2:
                connector = file_splitted.pop(-1)
            elif len(file_splitted) == 3:
                connector = file_splitted.pop(-2) + "_" + file_splitted.pop(-1)
            else:
                raise ValueError(f"Invalid file name: {file}")
            candles_config.append(CandlesConfig(connector=connector, trading_pair=trading_pair, interval=interval))
        return candles_config
    except Exception as e:
        st.warning("An error occurred:", e)

def get_candles_df(candles_config: CandlesConfig):
    """Retrieve the candles DataFrame from the specified candles config."""
    try:
        candles_df = pd.read_csv(constants.CANDLES_DATA_PATH + f"/candles_{candles_config.connector}_{candles_config.trading_pair}_{candles_config.interval}.csv")
        return candles_df
    except Exception as e:
        st.warning("An error occurred:", e)

# Start content here
st.text("This tool will let you analyze and generate a config for market making controllers.")
st.write("---")

st.write("## 📊 Market Data")
st.write("### Candlestick Available")
available_candles = get_available_candles()

if available_candles:
    df = pd.DataFrame([candles.dict() for candles in available_candles])
    df = df[['connector', 'trading_pair', 'interval']].copy()

    # Initialize selection options
    connectors = ['All'] + sorted(set(df['connector']))
    trading_pairs = ['All'] + sorted(set(df['trading_pair']))
    intervals = ['All'] + sorted(set(df['interval']))

    # Select boxes
    c1, c2, c3 = st.columns(3)
    with c1:
        selected_connector = st.selectbox("Select Connector", connectors, index=0)

    # Filter trading pairs and intervals based on selected connector
    if selected_connector != 'All':
        filtered_pairs = sorted(set(df[df['connector'] == selected_connector]['trading_pair']))
        filtered_intervals = sorted(set(df[df['connector'] == selected_connector]['interval']))
    else:
        filtered_pairs = trading_pairs
        filtered_intervals = intervals

    with c2:
        selected_trading_pair = st.selectbox("Select Trading Pair", ['All'] + filtered_pairs, index=0, disabled=(selected_connector == 'All'))
    with c3:
        selected_interval = st.selectbox("Select Interval", ['All'] + filtered_intervals, index=0, disabled=(selected_connector == 'All'))

    # Further filter DataFrame based on selections
    if selected_connector != 'All':
        df = df[df['connector'] == selected_connector]
    if selected_trading_pair != 'All':
        df = df[df['trading_pair'] == selected_trading_pair]
    if selected_interval != 'All':
        df = df[df['interval'] == selected_interval]

    c1, c2 = st.columns(2)
    with c1:
        st.write("### Candlestick Data")
        st.data_editor(df)
    # Check the length of the filtered DataFrame
    with c2:
        if len(df) == 1:
            # Show 'Render Candles' button
            if st.button('Render Candles'):
                st.write("Rendering Candles...")
                candles_config_data = df.iloc[0].to_dict()
                candles_config = CandlesConfig(connector=candles_config_data['connector'],
                                               trading_pair=candles_config_data['trading_pair'],
                                               interval=candles_config_data['interval'])
                st.write(candles_config)
                candles_df = get_candles_df(candles_config)
                st.data_editor(candles_df)
        elif df.empty:
            # Show 'Download Candles' button
            if st.button('Download Candles'):
                st.write("Downloading Candles...")
