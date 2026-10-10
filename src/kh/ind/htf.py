"""Bộ lọc khung lớn (HTF) đã chốt trong spec §3 — chỉ dùng nến M15/H1 ĐÃ ĐÓNG.

Hướng khung = Tăng nếu close > EMA50 và EMA50 > EMA50 cách 3 nến; Giảm nếu ngược lại cả hai; còn lại Trung tính.
Long chỉ được phép khi không khung nào Giảm; Short chỉ được phép khi không khung nào Tăng.
Không import module nhãn.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from kh.ind.indicators import core as K


def htf_direction(t: np.ndarray, c: np.ndarray, minutes: int, ema_len: int = 50, lookback: int = 3,
                  base: int = 1) -> np.ndarray:
    """Hướng khung `minutes` (+1/−1/0) gắn vào từng nến khung `base` phút (M1 hoặc M15), chỉ từ khi nến khung lớn
    đã đóng. Nến khung lớn phải đủ minutes/base nến con."""
    step = minutes * 60_000
    b = (t // step) * step
    g = pd.DataFrame({"b": b, "c": c, "n": 1}).groupby("b").agg(c=("c", "last"), n=("n", "sum"))
    g = g[g.n == minutes // base]
    cc = g.c.to_numpy(np.float64)
    e = K.ema(cc, ema_len)
    ep = K.shift(e, lookback)
    with np.errstate(invalid="ignore"):
        d = np.where((cc > e) & (e > ep), 1, np.where((cc < e) & (e < ep), -1, 0)).astype(np.int8)
    avail = g.index.to_numpy() + step
    pos = np.searchsorted(avail, t + base * 60_000, side="right") - 1
    return np.where(pos >= 0, d[np.maximum(pos, 0)], 0).astype(np.int8)


def htf_permissions(t: np.ndarray, c: np.ndarray, frames: tuple = (15, 60), base: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """M1: frames (15, 60); M15: frames (60, 240), base 15. Long khi không khung nào Giảm; Short khi không khung nào Tăng."""
    d = [htf_direction(t, c, m, base=base) for m in frames]
    long_ok = np.logical_and.reduce([x != -1 for x in d])
    short_ok = np.logical_and.reduce([x != 1 for x in d])
    return long_ok, short_ok
