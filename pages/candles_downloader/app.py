import time
from subprocess import CalledProcessError

import streamlit as st

import constants
from utils import os_utils
from docker_manager import DockerManager

from utils.st_utils import initialize_st_page


initialize_st_page(title="Candles Downloader", icon="🗂️")

# Start content here
docker_manager = DockerManager()

c1, c2, c3 = st.columns([2, 2, 0.5])
with c1:
    exchange = st.selectbox("Exchange", ["binance_perpetual", "binance"], index=0)
    trading_pairs = st.text_input("Trading Pairs (separated with commas)", value="BTC-USDT,ETH-USDT")
with c2:
    intervals = st.multiselect("Intervals", options=["1m", "3m", "5m", "15m", "1h", "4h", "1d"], default=["1m", "3m", "1h"])
    days_to_download = st.number_input("Days to Download", value=30, min_value=1, max_value=365, step=1)
with c3:
    get_data_button = st.button("Download Candles!")
    clean_container_folder_button = st.button("Clean Candles Folder")

if clean_container_folder_button:
    st.warning("Cleaning Candles Data folder...", icon="⚠️")
    st.write("---")
    os_utils.remove_files_from_directory(constants.CANDLES_DATA_PATH)
    st.write("### Container folder cleaned.")
    st.write("---")

if get_data_button:
    candles_container_config = {
        "EXCHANGE": exchange,
        "TRADING_PAIRS": trading_pairs,
        "INTERVALS": ",".join(intervals),
        "DAYS_TO_DOWNLOAD": days_to_download,
    }
    time.sleep(0.5)
    docker_manager.create_download_candles_container(candles_config=candles_container_config,
                                                     yml_path=constants.DOWNLOAD_CANDLES_CONFIG_YML)
    st.info("Downloading candles with a Docker container in the background. "
            "When this process is ready you will see the candles inside data/candles", icon="🕓")

st.write("---")
st.write("## ⚙️Containers Management")
try:
    active_containers = docker_manager.get_active_containers()
    c1, c2 = st.columns([0.9, 0.1])
    with c1:
        if "candles_downloader" in active_containers:
            st.success("Hummingbot Candles Downloader is running")
        st.write("Exited Containers:")
        st.warning(docker_manager.get_exited_containers())
    with c2:
        if "candles_downloader" in active_containers:
            stop_containers_button = st.button("Stop Candles Downloader")
            if stop_containers_button:
                docker_manager.stop_container("candles_downloader")
        clean_exited_containers_button = st.button("Clean Containers")
        if clean_exited_containers_button:
            docker_manager.clean_exited_containers()

except CalledProcessError as error:
    st.write("### Docker is not running. Please start docker in your machine.")

