"""Nhãn dự báo triple-barrier (rào đối xứng) — đã đăng ký trước trong docs/hypotheses.md.

Tại nến t (đóng cửa): vào lệnh giả định ở giá mở cửa nến t+1 = e.
Rào trên/dưới: e·(1 ± b), b = mult · σ_1m(t) · √H. Duyệt các nến t+1 … t+H:
- chỉ chạm rào trên → +1; chỉ chạm rào dưới → −1;
- chạm cả hai trong cùng một nến → "ambiguous" (không biết thứ tự trong nến);
- không chạm → dấu của log(close_{t+H} / e).
Nhãn hoàn chỉnh tại đóng cửa nến t+H (`label_end_ms`) — dùng cho purge/embargo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from kh.config import MS_PER_MIN

try:
    from numba import njit
except ImportError:
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]


@njit(cache=True)
def _barrier(open_, high, low, close, filler, b, H):
    n = len(close)
    touch = np.zeros(n, np.int8)      # +1 trên, −1 dưới, 0 không chạm, 2 cả hai cùng nến
    t_hit = np.full(n, -1, np.int32)
    fwd = np.full(n, np.nan)
    has_filler = np.zeros(n, np.bool_)
    for i in range(n):
        e = i + 1
        if e + H - 1 >= n or np.isnan(b[i]):
            touch[i] = -9
            continue
        px = open_[e]
        up, dn = px * (1.0 + b[i]), px * (1.0 - b[i])
        for j in range(e, e + H):
            hu, hd = high[j] >= up, low[j] <= dn
            if hu and hd:
                touch[i] = 2
                t_hit[i] = j - e + 1
                break
            if hu:
                touch[i] = 1
                t_hit[i] = j - e + 1
                break
            if hd:
                touch[i] = -1
                t_hit[i] = j - e + 1
                break
        for j in range(e, e + H):
            if filler[j]:
                has_filler[i] = True
        fwd[i] = np.log(close[e + H - 1] / px)
    return touch, t_hit, fwd, has_filler


def make_labels(k: pd.DataFrame, F: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    sig = F["sigma_1m_bps"].astype("float64") / 1e4
    out = {}
    o, h, l, c = (k[x].to_numpy(np.float64) for x in ("open", "high", "low", "close"))
    fil = k.is_filler.to_numpy()
    for H in cfg["labels"]["horizons_min"]:
        b = (cfg["labels"]["barrier_sigma_mult"] * sig * np.sqrt(H)).to_numpy()
        touch, t_hit, fwd, hf = _barrier(o, h, l, c, fil, b, H)
        lab = np.where(np.isin(touch, [1, -1]), touch, np.sign(fwd)).astype(float)
        lab[(touch == 2) | (touch == -9) | (lab == 0)] = np.nan
        out[f"barrier_{H}"] = b
        out[f"touch_{H}"] = touch
        out[f"t_hit_{H}"] = t_hit
        out[f"fwd_logret_{H}"] = fwd
        out[f"label_{H}"] = lab
        out[f"filler_in_h_{H}"] = hf
        out[f"label_end_ms_{H}"] = k.open_time_ms.to_numpy() + (H + 1) * MS_PER_MIN
    return pd.DataFrame(out, index=k.index)


def breakeven_prob(barrier: float, cost_round_trip: float) -> float:
    """Xác suất thắng tối thiểu để kỳ vọng ≥ 0 khi TP = SL = barrier: p* = 0,5 + c/(2b)."""
    return 0.5 + cost_round_trip / (2 * barrier)
