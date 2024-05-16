import pandas as pd
import requests
from glom import *


class MinerClient:
    MARKETS_ENDPOINT = "https://api.hummingbot.io/bounty/markets"

    @staticmethod
    def reward_splitter(base, reward_dict):
        tmp = {"rewards_HBOT": 0, "rewards_STABLE": 0, "rewards_base": 0, }
        if "HBOT" in reward_dict:
            tmp["rewards_HBOT"] += reward_dict["HBOT"]
        if "USDC" in reward_dict:
            tmp["rewards_STABLE"] += reward_dict["USDC"]
        if "USDT" in reward_dict:
            tmp["rewards_STABLE"] += reward_dict["USDT"]
        if base in reward_dict:
            tmp["rewards_base"] += reward_dict[base]

        return pd.Series(tmp, dtype=float)

    @staticmethod
    def exchange_coingecko_id(exchange: str):
        converter = {
            "kucoin": "kucoin",
            "binance": "binance",
            "gateio": "gate",
            "ascendex": "bitmax"
        }
        return converter.get(exchange, None)

    def get_miner_stats_df(self):
        miner_data = requests.get(self.MARKETS_ENDPOINT).json()
        spec = {
            'market_id': ('markets', ['market_id']),
            'trading_pair': ('markets', ['trading_pair']),
            'exchange': ('markets', ['exchange_name']),
            'base': ('markets', ['base_asset']),
            'quote': ('markets', ['quote_asset']),
            'start_timestamp': ('markets', [("active_bounty_periods", ['start_timestamp'])]),
            'end_timestamp': ('markets', [("active_bounty_periods", ['end_timestamp'])]),
            'budget': ('markets', [("active_bounty_periods", ['budget'])]),
            'spread_max': ('markets', [("active_bounty_periods", ['spread_max'])]),
            'payout_asset': ('markets', [("active_bounty_periods", ['payout_asset'])]),
            'return': ('markets', ['return']),
            'last_snapshot_ts': ('markets', ['last_snapshot_ts']),
            'hourly_payout_usd': ('markets', ['hourly_payout_usd']),
            'bots': ('markets', ['bots']),
            'last_hour_bots': ('markets', ['last_hour_bots']),
            'filled_24h_volume': ('markets', ['filled_24h_volume']),
            # 'weekly_reward_in_usd': ('markets', ['weekly_reward_in_usd']),
            # 'weekly_reward': ('markets', ['weekly_reward']),
            'market_24h_usd_volume': ('markets', ['market_24h_usd_volume'])
        }

        r = glom(miner_data, spec)
        df = pd.DataFrame(r)
        # df = pd.concat([df, df.apply(lambda x: self.reward_splitter(x.base, x.weekly_reward), axis=1)], axis=1)
        df["trading_pair"] = df.apply(lambda x: x.base + "-" + x.quote, axis=1)
        df["exchange_coingecko_id"] = df.apply(lambda x: self.exchange_coingecko_id(x.exchange), axis=1)
        return df
