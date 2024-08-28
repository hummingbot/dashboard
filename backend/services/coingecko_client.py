import re
import time

import pandas as pd
from pycoingecko import CoinGeckoAPI


class CoinGeckoClient:
    def __init__(self):
        self.connector = CoinGeckoAPI()

    def get_all_coins_df(self):
        coin_list = self.connector.get_coins_list()
        return pd.DataFrame(coin_list)

    def get_all_coins_markets_df(self):
        coin_list = self.connector.get_coins_markets(vs_currency="USD")
        return pd.DataFrame(coin_list)

    def get_coin_tickers_by_id(self, coin_id: str):
        coin_tickers = self.connector.get_coin_ticker_by_id(id=coin_id)
        coin_tickers_df = pd.DataFrame(coin_tickers["tickers"])
        coin_tickers_df["token_id"] = coin_id
        return coin_tickers_df

    def get_coin_tickers_by_id_list(self, coins_id: list):
        dfs = []
        for coin_id in coins_id:
            df = self.get_coin_tickers_by_id(coin_id)
            dfs.append(df)
            time.sleep(1)

        coin_tickers_df = pd.concat(dfs)
        coin_tickers_df["exchange"] = coin_tickers_df["market"].apply(
            lambda x: re.sub("Exchange", "", x["name"]))
        coin_tickers_df.drop(columns="market", inplace=True)
        coin_tickers_df["trading_pair"] = coin_tickers_df.base + "-" + coin_tickers_df.target
        return coin_tickers_df

    def get_all_exchanges_df(self):
        exchanges_list = self.connector.get_exchanges_list()
        return pd.DataFrame(exchanges_list)

    def get_exchanges_markets_info_by_id_list(self, exchanges_id: list):
        dfs = []
        for exchange_id in exchanges_id:
            df = pd.DataFrame(self.connector.get_exchanges_by_id(exchange_id)["tickers"])
            dfs.append(df)
        exchanges_spreads_df = pd.concat(dfs)
        exchanges_spreads_df["exchange"] = exchanges_spreads_df["market"].apply(
            lambda x: re.sub("Exchange", "", x["name"]))
        exchanges_spreads_df.drop(columns="market", inplace=True)
        exchanges_spreads_df["trading_pair"] = exchanges_spreads_df.base + "-" + exchanges_spreads_df.target
        return exchanges_spreads_df
