import streamlit as st

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
st.title("📋 Data Available")

with st.spinner(text='In progress'):
    exchanges_df = get_all_exchanges_df()
    coins_df = get_all_coins_df()
    miner_stats_df = get_miner_stats_df()
miner_coins = coins_df.loc[coins_df["symbol"].isin(miner_stats_df["base"].str.lower().unique()), "name"]

default_miner_coins = ["Avalanche"]

st.write("---")
st.write("## Exchanges and coins data")

with st.expander('Coins data'):
    st.dataframe(coins_df)

with st.expander('Exchanges data'):
    st.dataframe(exchanges_df)

st.write("---")
st.write("## Tickers filtered")


st.write("### Coins filter 🦅")
tokens = st.multiselect(
    "Select the tokens to analyze:",
    options=coins_df["name"],
    default=default_miner_coins)

coins_id = coins_df.loc[coins_df["name"].isin(tokens), "id"].tolist()

coin_tickers_df = get_coin_tickers_by_id_list(coins_id)
coin_tickers_df["coin_name"] = coin_tickers_df.apply(lambda x: coins_df.loc[coins_df["id"] == x.token_id, "name"].item(), axis=1)
st.write("### Exchanges filter 🦅")
exchanges = st.multiselect(
    "Select the exchanges to analyze:",
    options=exchanges_df["name"],
    default=CONFIG.MINER_EXCHANGES)


with st.expander('Coins Tickers Data'):
    st.dataframe(coin_tickers_df)

