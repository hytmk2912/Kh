"""Bộ lọc khung lớn (HTF) đã chốt trong spec §3 — chỉ dùng nến M15/H1 ĐÃ ĐÓNG.

Hướng khung = Tăng nếu close > EMA50 và EMA50 > EMA50 cách 3 nến; Giảm nếu ngược lại cả hai; còn lại Trung tính.
Long chỉ được phép khi không khung nào Giảm; Short chỉ được phép khi không khung nào Tăng.
Không import module nhãn.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from kh.ind.indicators import core as K


def htf_direction(t: np.ndarray, c: np.ndarray, minutes: int, ema_len: int = 50, lookback: int = 3) -> np.ndarray:
    """Hướng khung `minutes` (+1/−1/0) gắn vào từng nến M1, chỉ từ khi nến khung lớn đã đóng."""
    step = minutes * 60_000
    b = (t // step) * step
    g = pd.DataFrame({"b": b, "c": c, "n": 1}).groupby("b").agg(c=("c", "last"), n=("n", "sum"))
    g = g[g.n == minutes]
    cc = g.c.to_numpy(np.float64)
    e = K.ema(cc, ema_len)
    ep = K.shift(e, lookback)
    with np.errstate(invalid="ignore"):
        d = np.where((cc > e) & (e > ep), 1, np.where((cc < e) & (e < ep), -1, 0)).astype(np.int8)
    avail = g.index.to_numpy() + step
    pos = np.searchsorted(avail, t + 60_000, side="right") - 1
    return np.where(pos >= 0, d[np.maximum(pos, 0)], 0).astype(np.int8)


def htf_permissions(t: np.ndarray, c: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    d15, d60 = htf_direction(t, c, 15), htf_direction(t, c, 60)
    long_ok = (d15 != -1) & (d60 != -1)
    short_ok = (d15 != 1) & (d60 != 1)
    return long_ok, short_ok
