"""Nhãn chế độ thị trường (causal — chỉ dùng dữ liệu đến hết nến hiện tại).

- trend_regime: z = log(close_t / close_{t-1440}) / (sigma_1m * sqrt(1440));
  "up" nếu z > 1, "down" nếu z < -1, ngược lại "range" (đi ngang).
- vol_regime: sigma_1m so với trung vị 30 ngày trước đó; "high" > 1,25×, "low" < 0,8×.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from kh.waves.dc import sigma_1m


def regimes(df: pd.DataFrame, halflife_min: int = 1440) -> pd.DataFrame:
    c = df.close
    sig = sigma_1m(c, halflife_min)
    z = np.log(c / c.shift(1440)) / (sig * np.sqrt(1440))
    trend = np.where(z > 1, "up", np.where(z < -1, "down", "range"))
    trend = np.where(z.isna(), "na", trend)
    # Trung vị 30 ngày, lấy mẫu mỗi giờ để nhanh (vẫn chỉ dùng quá khứ)
    hourly = sig.iloc[::60]
    med = hourly.rolling(30 * 24, min_periods=7 * 24).median().reindex(sig.index).ffill().shift(1)
    ratio = sig / med
    vol = np.where(ratio > 1.25, "high", np.where(ratio < 0.8, "low", "normal"))
    vol = np.where(ratio.isna(), "na", vol)
    return pd.DataFrame({"sigma_1m": sig, "trend_z_1d": z, "trend_regime": trend,
                         "vol_ratio_30d": ratio, "vol_regime": vol}, index=df.index)
