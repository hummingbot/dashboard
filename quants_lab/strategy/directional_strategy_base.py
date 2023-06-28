from datetime import datetime
from typing import Optional


class DirectionalStrategyBase:

    def get_data(self, start: Optional[str] = None, end: Optional[str] = None):
        df = self.get_raw_data()
        return self.filter_df_by_time(df, start, end)

    def get_raw_data(self):
        raise NotImplemented

    def add_indicators(self, df):
        raise NotImplemented

    def add_signals(self, df):
        raise NotImplemented

    @staticmethod
    def filter_df_by_time(df, start: Optional[str] = None, end: Optional[str] = None):
        timeframe_conditions = []
        if start is not None:
            timeframe_conditions.append(df["timestamp"] >= datetime.strptime(start, "%Y-%m-%d"))
        if end is not None:
            timeframe_conditions.append(df["timestamp"] <= datetime.strptime(end, "%Y-%m-%d"))
        if len(timeframe_conditions) > 0:
            df = df.loc[timeframe_conditions[0] & timeframe_conditions[1]]
        else:
            df = df.copy()
        return df