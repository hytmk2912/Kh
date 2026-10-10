"""Hàm nền cho chỉ báo (float64 khi tính, causal: giá trị tại t chỉ dùng dữ liệu ≤ t).

Không import module nhãn.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from numba import njit
except ImportError:
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]


# Số nến trong 1 ngày của khung đang tính (M1: 1.440; M15: 96). Đổi qua kh.ind.indicators.impl.timeframe().
BARS_PER_DAY = 1440


def S(x) -> pd.Series:
    return pd.Series(np.asarray(x, dtype=np.float64))


def sma(x, n):
    return S(x).rolling(n, min_periods=n).mean().to_numpy()


def rsum(x, n):
    return S(x).rolling(n, min_periods=n).sum().to_numpy()


def stdev(x, n, ddof=0):
    return S(x).rolling(n, min_periods=n).std(ddof=ddof).to_numpy()


def highest(x, n):
    return S(x).rolling(n, min_periods=n).max().to_numpy()


def lowest(x, n):
    return S(x).rolling(n, min_periods=n).min().to_numpy()


def shift(x, k):
    x = np.asarray(x, dtype=np.float64)
    out = np.full_like(x, np.nan)
    if k > 0:
        out[k:] = x[:-k]
    elif k == 0:
        out[:] = x
    return out


def change(x, k=1):
    return np.asarray(x, dtype=np.float64) - shift(x, k)


@njit(cache=True)
def _ema(x, alpha, n):
    """EMA khởi tạo bằng SMA của n giá trị hợp lệ đầu tiên (như TradingView ta.ema / ta.rma)."""
    out = np.full(len(x), np.nan)
    cnt = 0
    acc = 0.0
    prev = np.nan
    for i in range(len(x)):
        v = x[i]
        if np.isnan(prev):
            if np.isnan(v):
                cnt = 0
                acc = 0.0
                continue
            acc += v
            cnt += 1
            if cnt == n:
                prev = acc / n
                out[i] = prev
        else:
            if np.isnan(v):
                out[i] = prev
                continue
            prev = alpha * v + (1.0 - alpha) * prev
            out[i] = prev
    return out


def ema(x, n):
    return _ema(np.asarray(x, dtype=np.float64), 2.0 / (n + 1.0), int(n))


def rma(x, n):
    return _ema(np.asarray(x, dtype=np.float64), 1.0 / n, int(n))


@njit(cache=True)
def _wma(x, w):
    n = len(w)
    out = np.full(len(x), np.nan)
    sw = w.sum()
    for i in range(n - 1, len(x)):
        acc = 0.0
        ok = True
        for k in range(n):
            v = x[i - n + 1 + k]
            if np.isnan(v):
                ok = False
                break
            acc += w[k] * v
        if ok:
            out[i] = acc / sw
    return out


def wma(x, n):
    return _wma(np.asarray(x, dtype=np.float64), np.arange(1, n + 1, dtype=np.float64))


def weighted(x, w):
    return _wma(np.asarray(x, dtype=np.float64), np.asarray(w, dtype=np.float64))


@njit(cache=True)
def _linreg(y, n):
    """Hồi quy tuyến tính y theo x = 0..n−1 trên cửa sổ trượt: (giá trị tại nến cuối, hệ số góc, sai số chuẩn)."""
    m = len(y)
    val = np.full(m, np.nan)
    slope = np.full(m, np.nan)
    se = np.full(m, np.nan)
    xm = (n - 1) / 2.0
    sxx = 0.0
    for k in range(n):
        sxx += (k - xm) ** 2
    for i in range(n - 1, m):
        ym = 0.0
        ok = True
        for k in range(n):
            v = y[i - n + 1 + k]
            if np.isnan(v):
                ok = False
                break
            ym += v
        if not ok:
            continue
        ym /= n
        sxy = 0.0
        for k in range(n):
            sxy += (k - xm) * (y[i - n + 1 + k] - ym)
        b = sxy / sxx
        a = ym - b * xm
        val[i] = a + b * (n - 1)
        slope[i] = b
        if n > 2:
            ss = 0.0
            for k in range(n):
                r = y[i - n + 1 + k] - (a + b * k)
                ss += r * r
            se[i] = np.sqrt(ss / (n - 2))
    return val, slope, se


def linreg(y, n):
    return _linreg(np.asarray(y, dtype=np.float64), int(n))


@njit(cache=True)
def _rolling_corr(a, b, n):
    m = len(a)
    out = np.full(m, np.nan)
    for i in range(n - 1, m):
        sa = sb = 0.0
        ok = True
        for k in range(i - n + 1, i + 1):
            if np.isnan(a[k]) or np.isnan(b[k]):
                ok = False
                break
            sa += a[k]
            sb += b[k]
        if not ok:
            continue
        ma, mb = sa / n, sb / n
        cov = va = vb = 0.0
        for k in range(i - n + 1, i + 1):
            da, db = a[k] - ma, b[k] - mb
            cov += da * db
            va += da * da
            vb += db * db
        if va > 0 and vb > 0:
            out[i] = cov / np.sqrt(va * vb)
    return out


def corr(a, b, n):
    return _rolling_corr(np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64), int(n))


@njit(cache=True)
def _rank_window(x, n):
    """Hạng (1..n, trung bình khi trùng) của từng phần tử trong cửa sổ — dùng cho tương quan hạng."""
    m = len(x)
    out = np.full((m, n), np.nan)
    for i in range(n - 1, m):
        for a in range(n):
            va = x[i - n + 1 + a]
            less = 0.0
            eq = 0.0
            for b in range(n):
                vb = x[i - n + 1 + b]
                if vb < va:
                    less += 1
                elif vb == va:
                    eq += 1
            out[i, a] = less + (eq + 1) / 2.0
    return out


@njit(cache=True)
def _rank_corr(ra, rb, n):
    m = ra.shape[0]
    out = np.full(m, np.nan)
    mean = (n + 1) / 2.0
    for i in range(n - 1, m):
        cov = va = vb = 0.0
        ok = True
        for k in range(n):
            if np.isnan(ra[i, k]) or np.isnan(rb[i, k]):
                ok = False
                break
            da, db = ra[i, k] - mean, rb[i, k] - mean
            cov += da * db
            va += da * da
            vb += db * db
        if ok and va > 0 and vb > 0:
            out[i] = cov / np.sqrt(va * vb)
    return out


def rank_corr(a, b, n):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return _rank_corr(_rank_window(a, n), _rank_window(b, n), n)


@njit(cache=True)
def _percentrank(x, n):
    """% số giá trị trong n nến TRƯỚC nhỏ hơn hoặc bằng giá trị hiện tại (như ta.percentrank)."""
    m = len(x)
    out = np.full(m, np.nan)
    for i in range(n, m):
        if np.isnan(x[i]):
            continue
        c = 0
        ok = True
        for k in range(i - n, i):
            if np.isnan(x[k]):
                ok = False
                break
            if x[k] <= x[i]:
                c += 1
        if ok:
            out[i] = 100.0 * c / n
    return out


def percentrank(x, n):
    return _percentrank(np.asarray(x, dtype=np.float64), int(n))


def true_range(h, l, c):
    pc = shift(c, 1)
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    tr[0] = h[0] - l[0]
    return tr


def atr(h, l, c, n):
    return rma(true_range(h, l, c), n)


def rsi(x, n):
    d = change(x)
    up = rma(np.where(np.isnan(d), np.nan, np.maximum(d, 0)), n)
    dn = rma(np.where(np.isnan(d), np.nan, np.maximum(-d, 0)), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(dn == 0, 100.0, np.where(up == 0, 0.0, 100 - 100 / (1 + up / dn)))
    return np.where(np.isnan(up) | np.isnan(dn), np.nan, r)


def safe_div(a, b):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(b == 0, np.nan, np.asarray(a, dtype=np.float64) / b)


# ---------------------------------------------------------------- sự kiện / trạng thái
def cross_up(a, b) -> np.ndarray:
    a, b = np.asarray(a, np.float64), np.broadcast_to(np.asarray(b, np.float64), np.shape(a))
    pa, pb = shift(a, 1), shift(b, 1)
    with np.errstate(invalid="ignore"):
        return (a > b) & (pa <= pb)


def cross_dn(a, b) -> np.ndarray:
    a, b = np.asarray(a, np.float64), np.broadcast_to(np.asarray(b, np.float64), np.shape(a))
    pa, pb = shift(a, 1), shift(b, 1)
    with np.errstate(invalid="ignore"):
        return (a < b) & (pa >= pb)


def became(cond) -> np.ndarray:
    cond = np.asarray(cond, bool)
    prev = np.concatenate([[False], cond[:-1]])
    return cond & ~prev


def events(long_ev, short_ev) -> np.ndarray:
    """Gộp sự kiện Long/Short thành mảng int8 (+1/−1/0). Trùng cả hai trong một nến → 0."""
    sig = np.zeros(len(long_ev), np.int8)
    sig[np.asarray(long_ev, bool)] = 1
    sig[np.asarray(short_ev, bool)] = np.where(sig[np.asarray(short_ev, bool)] == 1, 0, -1)
    return sig


def cross_signal(a, b) -> np.ndarray:
    return events(cross_up(a, b), cross_dn(a, b))


def median_filter(x, window=None) -> np.ndarray:
    """Filter mặc định [A]: bật khi x > trung vị của x trong `window` nến TRƯỚC (không gồm nến hiện tại).
    Mặc định window = 1 ngày (BARS_PER_DAY nến)."""
    window = window or BARS_PER_DAY
    med = S(x).shift(1).rolling(window, min_periods=window).median().to_numpy()
    with np.errstate(invalid="ignore"):
        return np.asarray(x, np.float64) > med
