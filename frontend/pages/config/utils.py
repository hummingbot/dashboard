def get_max_records(days_to_download: int, interval: str) -> int:
    conversion = {"s": 1 / 60, "m": 1, "h": 60, "d": 1440}
    unit = interval[-1]
    quantity = int(interval[:-1])
    return int(days_to_download * 24 * 60 / (quantity * conversion[unit]))
