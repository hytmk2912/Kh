"""Tham số khung thời gian của từng track (spec M1: docs/ind/spec.md; spec M15: docs/ind15/spec.md).

Code track M1 nhận một `Track`; mặc định là `M1` nên kết quả M1 đã commit giữ nguyên.
Mọi độ dài tính theo số NẾN của khung tín hiệu (M1: 1 nến = 1 phút; M15: 1 nến = 15 phút).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

KLINE_KIND = {1: "klines_1m", 15: "klines_15m", 60: "klines_1h", 240: "klines_4h"}


@dataclass(frozen=True)
class Track:
    name: str                  # thư mục reports/<name>, data/<name>
    tf: int                    # phút mỗi nến tín hiệu
    htf: tuple                 # khung lọc hướng (phút)
    bars_per_day: int
    wave_pct: float            # ngưỡng sóng ZigZag chính
    wave_sens: tuple           # các ngưỡng báo cáo (gồm ngưỡng chính)
    pullback_pct: float        # ZigZag nhịp hồi
    fast_bars: int             # sóng nhanh: đi được ngưỡng trong ≤ fast_bars nến
    flat_bars: int             # đi ngang: cửa sổ ≥ flat_bars nến có biên độ < ngưỡng
    unknown_after_filler: int  # số nến sau filler gán UNKNOWN / chặn vào lệnh
    min_remaining: float       # "bắt được sóng": phần còn lại từ giá vào ≥ ngưỡng này
    tp: float
    sl: float
    max_hold_bars: int         # giữ lệnh tối đa (nến tín hiệu)
    param_overrides: dict = field(default_factory=dict)  # {tên chỉ báo: {tham số: giá trị}}

    def reports(self, P) -> Path:
        return Path(P.reports) / self.name

    def data(self, P) -> Path:
        return Path(P.data) / self.name

    @property
    def kline_kind(self) -> str:
        return KLINE_KIND[self.tf]

    @property
    def minutes_per_bar(self) -> int:
        return self.tf

    def __hash__(self):
        return hash(self.name)


M1 = Track(name="ind", tf=1, htf=(15, 60), bars_per_day=1440, wave_pct=0.005, wave_sens=(0.004, 0.005, 0.007),
           pullback_pct=0.002, fast_bars=15, flat_bars=30, unknown_after_filler=30, min_remaining=0.003,
           tp=0.0045, sl=0.0030, max_hold_bars=15)

# Spec M15 §1–§3 (CHANGELOG 2026-10-10)
M15 = Track(name="ind15", tf=15, htf=(60, 240), bars_per_day=96, wave_pct=0.015, wave_sens=(0.010, 0.015, 0.020),
            pullback_pct=0.006, fast_bars=32, flat_bars=32, unknown_after_filler=2, min_remaining=0.009,
            tp=0.012, sl=0.008, max_hold_bars=32,
            param_overrides={"52-Week High/Low": {"length": 96}, "Zig Zag": {"deviation": 0.015}})

TRACKS = {t.name: t for t in (M1, M15)}
