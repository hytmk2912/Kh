"""Công cụ thống kê: IC theo ngày, Newey-West, FDR Benjamini–Yekutieli, bootstrap theo khối."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def ic_daily_products(df: pd.DataFrame, cols: list[str], y: str) -> pd.DataFrame:
    """Đóng góp theo ngày vào IC Spearman GỘP toàn tập.

    Hạng và chuẩn hóa tính trên toàn bộ tập (không trừ trung bình theo ngày — cách đó gây thiên lệch
    âm giả tạo cho đặc trưng có tính bền như return 1 ngày, đã kiểm chứng trên bước ngẫu nhiên).
    Trả về DataFrame (ngày × cột) của trung bình tích hạng chuẩn hóa; trung bình các ngày ≈ IC,
    và t-stat Newey-West trên chuỗi ngày đo bất định có tính tự tương quan / nhãn chồng lấn.
    """
    R = df[cols + [y]].rank(pct=True)
    U = (R - R.mean()) / R.std()
    prod = U[cols].mul(U[y], axis=0)
    return prod.groupby(df["day"].to_numpy()).mean()


def ecdf_transform(train_values: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Hạng phần trăm của x theo phân phối train (không dùng thông tin tương lai), trừ 0,5."""
    tv = np.sort(train_values[~np.isnan(train_values)])
    out = np.searchsorted(tv, x, side="right") / max(len(tv), 1) - 0.5
    return np.where(np.isnan(x), np.nan, out)


def nw_tstat(x: pd.Series | np.ndarray, lags: int = 5) -> tuple[float, float, int]:
    """Trung bình, t-stat Newey-West và số quan sát của chuỗi (bỏ NaN)."""
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    T = len(x)
    if T < 10:
        return np.nan, np.nan, T
    m = x.mean()
    d = x - m
    var = d @ d / T
    for l in range(1, min(lags, T - 1) + 1):
        var += 2 * (1 - l / (lags + 1)) * (d[l:] @ d[:-l]) / T
    se = np.sqrt(max(var, 1e-18) / T)
    return float(m), float(m / se), T


def p_two_sided(t: float) -> float:
    return float(2 * stats.norm.sf(abs(t))) if np.isfinite(t) else np.nan


def p_one_sided(t: float, sign: float) -> float:
    return float(stats.norm.sf(t * np.sign(sign))) if np.isfinite(t) else np.nan


def fdr_by(p: np.ndarray, q: float) -> np.ndarray:
    """Benjamini–Yekutieli (đúng dưới phụ thuộc tùy ý). Trả về mảng bool: bác bỏ H0."""
    p = np.asarray(p, float)
    ok = ~np.isnan(p)
    m = ok.sum()
    rej = np.zeros(len(p), bool)
    if m == 0:
        return rej
    cm = np.sum(1.0 / np.arange(1, m + 1))
    idx = np.flatnonzero(ok)[np.argsort(p[ok])]
    thr = q * np.arange(1, m + 1) / (m * cm)
    below = p[idx] <= thr
    if below.any():
        k = np.max(np.flatnonzero(below))
        rej[idx[: k + 1]] = True
    return rej


def bootstrap_diff_by_day(x: np.ndarray, mask: np.ndarray, day: np.ndarray, reps: int = 1000,
                          seed: int = 0) -> dict:
    """Chênh lệch trung bình x[mask] − x (toàn bộ), bootstrap theo ngày. p một phía H0: diff ≤ 0."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({"x": x, "m": mask.astype(float), "xm": x * mask, "d": day})
    g = df.groupby("d").agg(sx=("x", "sum"), n=("x", "size"), sxm=("xm", "sum"), nm=("m", "sum"))
    obs = g.sxm.sum() / max(g.nm.sum(), 1) - g.sx.sum() / g.n.sum()
    idx = rng.integers(0, len(g), (reps, len(g)))
    A = g.to_numpy()
    s = A[idx].sum(1)
    diffs = s[:, 2] / np.maximum(s[:, 3], 1) - s[:, 0] / s[:, 1]
    p = float(((diffs - diffs.mean()) >= obs).mean())
    return {"diff": float(obs), "ci90": [float(np.quantile(diffs, 0.05)), float(np.quantile(diffs, 0.95))],
            "p_one_sided": p, "n_event": int(g.nm.sum()), "n_days": int(len(g))}
