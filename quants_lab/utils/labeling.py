from typing import Optional

import numpy as np
import pandas as pd


def triple_barrier_method(df, tp=1.0, sl=1.0, tl=5, std_span: Optional[int] = 100, trade_cost=0.0006,  max_executors: int = 1):
    df.index = pd.to_datetime(df.timestamp, unit="s")
    if std_span:
        df["target"] = df["close"].rolling(std_span).std() / df["close"]
    else:
        df["target"] = 1 / 100
    df["tl"] = df.index + pd.Timedelta(seconds=tl)
    df.dropna(subset="target", inplace=True)

    df = apply_tp_sl_on_tl(df, tp=tp, sl=sl)

    df = get_bins(df, trade_cost)

    df['tp'] = df['close'] * (1 + df['target'] * tp * df["side"])
    df['sl'] = df['close'] * (1 - df['target'] * sl * df["side"])

    df = add_active_signals(df, max_executors)
    return df


def add_active_signals(df, max_executors):
    close_times = [pd.Timestamp.min] * max_executors
    df["active_signal"] = 0
    for index, row in df[(df["side"] != 0)].iterrows():
        for close_time in close_times:
            if row["timestamp"] > close_time:
                df.loc[df.index == index, "active_signal"] = 1
                close_times.remove(close_time)
                close_times.append(row["close_time"])
                break
    return df


def get_bins(df, trade_cost):
    # 1) prices aligned with events
    px = df.index.union(df['tl'].values).drop_duplicates()
    px = df.close.reindex(px, method='ffill')

    # 2) create out object
    df['ret'] = (px.loc[df['close_time'].values].values / px.loc[df.index] - 1) * df['side']
    df['real_class'] = np.sign(df['ret'] - trade_cost)
    return df


def apply_tp_sl_on_tl(df: pd.DataFrame, tp: float, sl: float):
    events = df[df["side"] != 0].copy()
    if tp > 0:
        take_profit = tp * events['target']
    else:
        take_profit = pd.Series(index=df.index)  # NaNs
    if sl > 0:
        stop_loss = - sl * events['target']
    else:
        stop_loss = pd.Series(index=df.index)  # NaNs

    for loc, tl in events['tl'].fillna(df.index[-1]).items():
        df0 = df.close[loc:tl]  # path prices
        df0 = (df0 / df.close[loc] - 1) * events.at[loc, 'side']  # path returns
        df.loc[loc, 'stop_loss_time'] = df0[df0 < stop_loss[loc]].index.min()  # earliest stop loss.
        df.loc[loc, 'take_profit_time'] = df0[df0 > take_profit[loc]].index.min()  # earliest profit taking.
    df["close_time"] = df[["tl", "take_profit_time", "stop_loss_time"]].dropna(how='all').min(axis=1)
    df['close_type'] = df[['take_profit_time', 'stop_loss_time', 'tl']].dropna(how='all').idxmin(axis=1)
    df['close_type'].replace({'take_profit_time': 'tp', 'stop_loss_time': 'sl'}, inplace=True)
    return df
