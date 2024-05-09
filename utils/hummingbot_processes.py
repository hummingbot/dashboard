import asyncio
from typing import List

from tqdm import tqdm

from hummingbot.data_feed.candles_feed.candles_factory import CandlesFactory, CandlesConfig


async def aget_candles_list(candles_configs: List[CandlesConfig]):
    tasks = [aget_candles(config.connector, config.trading_pair, config.interval, config.max_records) for config in candles_configs]
    return await asyncio.gather(*tasks)


async def aget_candles(connector_name: str, trading_pair: str, interval: str, max_records: int):
    candles = CandlesFactory.get_candle(CandlesConfig(connector=connector_name,
                                                      trading_pair=trading_pair,
                                                      interval=interval, max_records=max_records))
    candles.start()

    pbar = tqdm(total=candles._candles.maxlen)
    while not candles.ready:
        await asyncio.sleep(1)
        awaited_records = candles._candles.maxlen - len(candles._candles)
        pbar.update(candles._candles.maxlen - awaited_records - pbar.n)

    pbar.close()
    df = candles.candles_df
    candles.stop()
    return df


async def adownload_candles(connector_name: str, trading_pair: str, interval: str, max_records: int, download_path: str):
    candles = CandlesFactory.get_candle(CandlesConfig(connector_name, trading_pair, interval, max_records))
    candles.start()
    while not candles.ready:
        print(f"Candles not ready yet! Missing {candles._candles.maxlen - len(candles._candles)}")
        await asyncio.sleep(1)
    df = candles.candles_df
    df.to_csv(download_path, index=False)
    candles.stop()

