import pandas_ta as ta  # noqa: F401


def get_pmm_dynamic_multipliers(df, macd_fast, macd_slow, macd_signal, natr_length):
    """
    Get the spread and price multipliers for PMM Dynamic
    """
    natr = ta.natr(df["high"], df["low"], df["close"], length=natr_length) / 100
    macd_output = ta.macd(df["close"], fast=macd_fast,
                          slow=macd_slow, signal=macd_signal)
    macd = macd_output[f"MACD_{macd_fast}_{macd_slow}_{macd_signal}"]
    macdh = macd_output[f"MACDh_{macd_fast}_{macd_slow}_{macd_signal}"]
    macd_signal = - (macd - macd.mean()) / macd.std()
    macdh_signal = macdh.apply(lambda x: 1 if x > 0 else -1)
    max_price_shift = natr / 2
    price_multiplier = ((0.5 * macd_signal + 0.5 * macdh_signal) * max_price_shift)
    return price_multiplier, natr
