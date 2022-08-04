import time

import pandas as pd
import streamlit as st
import plotly.express as px
import CONFIG
from utils.coingecko_utils import CoinGeckoUtils
from utils.miner_utils import MinerUtils

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def get_all_coins_df():
    return CoinGeckoUtils().get_all_coins_df()

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def get_all_exchanges_df():
    return CoinGeckoUtils().get_all_exchanges_df()

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def get_miner_stats_df():
    return MinerUtils().get_miner_stats_df()

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def get_coin_tickers_by_id_list(coins_id: list):
    return CoinGeckoUtils().get_coin_tickers_by_id_list(coins_id)

st.set_page_config(layout='wide')
st.title("🧙‍Cross Exchange Token Analyzer")
st.write("---")
with st.spinner(text='In progress'):
    exchanges_df = get_all_exchanges_df()
    coins_df = get_all_coins_df()
    miner_stats_df = get_miner_stats_df()
miner_coins = coins_df.loc[coins_df["symbol"].isin(miner_stats_df["base"].str.lower().unique()), "name"]


st.write("### Coins filter 🦅")
tokens = st.multiselect(
    "Select the tokens to analyze:",
    options=coins_df["name"],
    default=CONFIG.DEFAULT_MINER_COINS)

coins_id = coins_df.loc[coins_df["name"].isin(tokens), "id"].tolist()

coin_tickers_df = get_coin_tickers_by_id_list(coins_id)
coin_tickers_df["coin_name"] = coin_tickers_df.apply(lambda x: coins_df.loc[coins_df["id"] == x.token_id, "name"].item(), axis=1)

st.sidebar.write("### Exchanges filter 🦅")
exchanges = st.sidebar.multiselect(
    "Select the exchanges to analyze:",
    options=exchanges_df["name"],
    default=[exchange for exchange in CONFIG.MINER_EXCHANGES if exchange in exchanges_df["name"].unique()])

height = len(coin_tickers_df["coin_name"].unique()) * 500
fig = px.scatter(
    data_frame=coin_tickers_df[coin_tickers_df["exchange"].isin(exchanges)],
    x="volume",
    y="bid_ask_spread_percentage",
    color="exchange",
    log_x=True,
    log_y=True,
    facet_col="coin_name",
    hover_data=["trading_pair"],
    facet_col_wrap=1,
    height=height,
    template="plotly_dark",
    title="Spread and Volume Chart",
    labels={
        "volume": 'Volume (USD)',
        'bid_ask_spread_percentage': 'Bid Ask Spread (%)'
    })

st.sidebar.write("# Data filters 🏷")
st.sidebar.code("🧳 New filters coming. \nReach us on discord \nif you want to propose one!")
st.plotly_chart(fig, use_container_width=True)

