"""Chia fold walk-forward: train mở rộng, kiểm tra theo tháng dương lịch, embargo giữa train và test."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

DAY = 86_400_000


@dataclass(frozen=True)
class Fold:
    no: int
    train_lo: int   # ms, gồm
    train_hi: int   # ms, không gồm (đã trừ embargo)
    test_lo: int    # ms, gồm
    test_hi: int    # ms, không gồm

    @property
    def label(self) -> str:
        return pd.Timestamp(self.test_lo, unit="ms").strftime("%Y-%m")


def monthly_folds(start: str, end_inclusive: str, min_train_months: int = 6, embargo_days: int = 1) -> list[Fold]:
    """Train [start, đầu tháng kiểm tra − embargo); kiểm tra = cả tháng dương lịch (tháng cuối có thể không đủ).
    Tháng kiểm tra đầu tiên = tháng đầu tiên bắt đầu sau start + min_train_months."""
    s = pd.Timestamp(start, tz="UTC")
    e = pd.Timestamp(end_inclusive, tz="UTC") + pd.Timedelta(days=1)
    m = (s + pd.DateOffset(months=min_train_months)).normalize()
    m = m if m.day == 1 else (m + pd.offsets.MonthBegin(1))
    folds, k = [], 0
    ms = lambda ts: int(ts.value // 1_000_000)
    while m < e:
        nxt = min(m + pd.offsets.MonthBegin(1), e)
        folds.append(Fold(k, ms(s), ms(m - pd.Timedelta(days=embargo_days)), ms(m), ms(nxt)))
        k += 1
        m = nxt
    return folds
