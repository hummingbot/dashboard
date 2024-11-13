import os

from dotenv import load_dotenv

load_dotenv()

MINER_COINS = ["Algorand", "Avalanche", "DAO Maker", "Faith Tribe", "Fear", "Frontier",
               "Harmony", "Hot Cross", "HUMAN Protocol", "Oddz", "Shera", "Firo",
               "Vesper Finance", "Youclout", "Nimiq"]
MINER_EXCHANGES = ["Binance", "FTX", "Coinbase Exchange", "Huobi Global", "OKX", "KuCoin",
                   "Kraken", "Bybit (Spot)", "FTX.US", "Crypto.com Exchange", "Binance US",
                   "MEXC Global", "Gate.io", "BitMart", "Bitfinex", "AscendEX (BitMax)",
                   "Bittrex", "CoinFLEX", "Digifinex", "HitBTC", "Kraken", "Liquid", ]

DEFAULT_MINER_COINS = ["Avalanche"]

CERTIFIED_EXCHANGES = ["ascendex", "binance", "bybit", "gate.io", "hitbtc", "huobi", "kucoin", "okx", "gateway"]
CERTIFIED_STRATEGIES = ["xemm", "cross exchange market making", "pmm", "pure market making"]

AUTH_SYSTEM_ENABLED = os.getenv("AUTH_SYSTEM_ENABLED", "False").lower() in ("true", "1", "t")

BACKEND_API_HOST = os.getenv("BACKEND_API_HOST", "127.0.0.1")
BACKEND_API_PORT = os.getenv("BACKEND_API_PORT", 8000)
BACKEND_API_USERNAME = os.getenv("BACKEND_API_USERNAME", "admin")
BACKEND_API_PASSWORD = os.getenv("BACKEND_API_PASSWORD", "admin")
