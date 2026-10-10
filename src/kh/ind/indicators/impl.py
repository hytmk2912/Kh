"""Cài đặt chỉ báo (việc I2). Mỗi hàm nhận ngữ cảnh X (mảng M1 của MỘT symbol, causal) và trả về
(outputs: dict tên → mảng float64, signal: int8 cho D / bool cho F).

Tham số lấy từ phiếu trong registry.py. Không import module nhãn.
"""
from __future__ import annotations

import contextlib
import copy
from dataclasses import dataclass

import numpy as np
import pandas as pd

from kh.ind.indicators import core as K
from kh.ind.indicators.core import njit
from kh.ind.indicators.registry import BY_NAME


@dataclass
class Ctx:
    t: np.ndarray        # open_time_ms
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    v: np.ndarray
    tb: np.ndarray       # taker buy base volume
    ref: np.ndarray      # close cặp tham chiếu (BTCUSDT; với BTCUSDT là ETHUSDT), cùng lưới thời gian

    @classmethod
    def from_frame(cls, m1: pd.DataFrame, ref_close: np.ndarray) -> "Ctx":
        f = lambda col: m1[col].to_numpy(np.float64)
        return cls(m1.open_time_ms.to_numpy(np.int64), f("open"), f("high"), f("low"), f("close"), f("volume"),
                   f("taker_buy_base_volume"), np.asarray(ref_close, np.float64))

    def __len__(self):
        return len(self.c)

    @property
    def hl2(self):
        return (self.h + self.l) / 2

    @property
    def hlc3(self):
        return (self.h + self.l + self.c) / 3

    @property
    def ohlc4(self):
        return (self.o + self.h + self.l + self.c) / 4


IMPL: dict = {}


@contextlib.contextmanager
def timeframe(tr):
    """Tính chỉ báo cho khung của track `tr`: đặt số nến/ngày và tham số đã quy đổi (spec M15 §3).
    Track M1 không đổi gì. Khôi phục giá trị cũ khi thoát."""
    old_bpd, old = K.BARS_PER_DAY, {n: copy.deepcopy(BY_NAME[n].params) for n in tr.param_overrides}
    try:
        K.BARS_PER_DAY = tr.bars_per_day
        for n, kv in tr.param_overrides.items():
            BY_NAME[n].params = {**BY_NAME[n].params, **kv}
        yield
    finally:
        K.BARS_PER_DAY = old_bpd
        for n, p in old.items():
            BY_NAME[n].params = p


def reg(name):
    assert name in BY_NAME, name

    def deco(f):
        IMPL[name] = f
        return f
    return deco


def P(name):
    return BY_NAME[name].params


def price_cross(X, line):
    return {"line": line}, K.cross_signal(X.c, line)


def zero_cross(val):
    return {"value": val}, K.cross_signal(val, 0.0)


def filt(val):
    return {"value": val}, K.median_filter(val)


# ======================================================================= A1. MA
@reg("SMA")
def _(X): return price_cross(X, K.sma(X.c, P("SMA")["length"]))


@reg("EMA")
def _(X): return price_cross(X, K.ema(X.c, P("EMA")["length"]))


@reg("DEMA")
def _(X):
    n = P("DEMA")["length"]
    e1 = K.ema(X.c, n)
    return price_cross(X, 2 * e1 - K.ema(e1, n))


@reg("TEMA")
def _(X):
    n = P("TEMA")["length"]
    e1 = K.ema(X.c, n)
    e2 = K.ema(e1, n)
    return price_cross(X, 3 * e1 - 3 * e2 + K.ema(e2, n))


@reg("Hull MA")
def _(X):
    n = P("Hull MA")["length"]
    return price_cross(X, K.wma(2 * K.wma(X.c, n // 2) - K.wma(X.c, n), int(np.floor(np.sqrt(n)))))


@reg("Hamming MA")
def _(X):
    n = P("Hamming MA")["length"]
    w = 0.54 - 0.46 * np.cos(2 * np.pi * np.arange(n) / (n - 1))
    return price_cross(X, K.weighted(X.c, w))


@reg("Arnaud Legoux MA")
def _(X):
    p = P("Arnaud Legoux MA")
    n = p["length"]
    m = p["offset"] * (n - 1)
    s = n / p["sigma"]
    w = np.exp(-((np.arange(n) - m) ** 2) / (2 * s * s))
    return price_cross(X, K.weighted(X.c, w))


@reg("Least Squares MA")
def _(X): return price_cross(X, K.linreg(X.c, P("Least Squares MA")["length"])[0])


@reg("Smoothed MA")
def _(X): return price_cross(X, K.rma(X.c, P("Smoothed MA")["length"]))


@njit(cache=True)
def _kama(c, n, fast, slow):
    m = len(c)
    out = np.full(m, np.nan)
    fsc, ssc = 2.0 / (fast + 1), 2.0 / (slow + 1)
    for i in range(n, m):
        vol = 0.0
        for k in range(i - n + 1, i + 1):
            vol += abs(c[k] - c[k - 1])
        ch = abs(c[i] - c[i - n])
        er = 1.0 if vol <= ch else ch / vol  # quy ước TA-Lib: không có nhiễu → hiệu quả tối đa
        sc = (er * (fsc - ssc) + ssc) ** 2
        prev = out[i - 1] if not np.isnan(out[i - 1]) else c[i - 1]
        out[i] = prev + sc * (c[i] - prev)
    return out


@reg("Adaptive MA")
def _(X):
    p = P("Adaptive MA")
    return price_cross(X, _kama(X.c, p["length"], p["fast"], p["slow"]))


def htf_closed(X, minutes):
    """Nến khung lớn đã ĐÓNG ánh xạ về từng nến M1: giá trị tại t là của nến HTF gần nhất có
    thời điểm đóng ≤ thời điểm đóng của nến M1 t. Trả về (close_htf_series_index, df_htf)."""
    step = minutes * 60_000
    b = (X.t // step) * step
    df = pd.DataFrame({"b": b, "c": X.c, "n": 1}).groupby("b").agg(c=("c", "last"), n=("n", "sum"))
    df = df[df.n == minutes]  # chỉ nến khung lớn đủ phút (đã đóng)
    avail = df.index.to_numpy() + step
    pos = np.searchsorted(avail, X.t + 60_000, side="right") - 1
    return df, pos


@reg("Multi-Timeframe MA")
def _(X):
    df, pos = htf_closed(X, 15)
    ma = K.sma(df.c.to_numpy(), P("Multi-Timeframe MA")["length"])
    line = np.where(pos >= 0, ma[np.maximum(pos, 0)], np.nan)
    return price_cross(X, line)


@reg("WMA")
def _(X): return price_cross(X, K.wma(X.c, P("WMA")["length"]))


@njit(cache=True)
def _mcginley(c, n):
    m = len(c)
    out = np.full(m, np.nan)
    if m < n:
        return out
    acc = 0.0
    for k in range(n):
        acc += c[k]
    out[n - 1] = acc / n
    for i in range(n, m):
        prev = out[i - 1]
        out[i] = prev + (c[i] - prev) / (n * (c[i] / prev) ** 4)
    return out


@reg("McGinley Dynamic")
def _(X): return price_cross(X, _mcginley(X.c, P("McGinley Dynamic")["length"]))


@reg("Guppy MMA")
def _(X):
    p = P("Guppy MMA")
    S = np.vstack([K.ema(X.c, n) for n in p["short"]])
    L = np.vstack([K.ema(X.c, n) for n in p["long"]])
    with np.errstate(invalid="ignore"):
        bull = S.min(0) > L.max(0)
        bear = S.max(0) < L.min(0)
    return {"short_min": S.min(0), "long_max": L.max(0)}, K.events(K.became(bull), K.became(bear))


@reg("MA Cross")
def _(X):
    p = P("MA Cross")
    f, s = K.sma(X.c, p["fast"]), K.sma(X.c, p["slow"])
    return {"fast": f, "slow": s}, K.cross_signal(f, s)


@reg("EMA Cross")
def _(X):
    p = P("EMA Cross")
    f, s = K.ema(X.c, p["fast"]), K.ema(X.c, p["slow"])
    return {"fast": f, "slow": s}, K.cross_signal(f, s)


@reg("MA-EMA Cross")
def _(X):
    p = P("MA-EMA Cross")
    s, e = K.sma(X.c, p["sma"]), K.ema(X.c, p["ema"])
    return {"sma": s, "ema": e}, K.cross_signal(e, s)


# ======================================================================= A2. Xu hướng
@njit(cache=True)
def _supertrend(h, l, c, atr, f):
    """Chép theo mã tham chiếu Pine `pine_supertrend` của TradingView. Trả về (line, hướng +1 tăng/−1 giảm)."""
    m = len(c)
    ub = np.full(m, np.nan)
    lb = np.full(m, np.nan)
    st = np.full(m, np.nan)
    d = np.zeros(m, np.int8)       # theo Pine: −1 = tăng, 1 = giảm
    for i in range(m):
        if np.isnan(atr[i]):
            continue
        src = (h[i] + l[i]) / 2
        u, lo = src + f * atr[i], src - f * atr[i]
        plb = lb[i - 1] if i > 0 and not np.isnan(lb[i - 1]) else 0.0
        pub = ub[i - 1] if i > 0 and not np.isnan(ub[i - 1]) else 0.0
        pc = c[i - 1] if i > 0 else np.nan
        lo = lo if (lo > plb or pc < plb) else plb
        u = u if (u < pub or pc > pub) else pub
        lb[i], ub[i] = lo, u
        if i == 0 or np.isnan(atr[i - 1]):
            d[i] = 1
        elif st[i - 1] == pub:
            d[i] = -1 if c[i] > u else 1
        else:
            d[i] = 1 if c[i] < lo else -1
        st[i] = lo if d[i] == -1 else u
    return st, -d


@reg("SuperTrend")
def _(X):
    p = P("SuperTrend")
    line, tr = _supertrend(X.h, X.l, X.c, K.atr(X.h, X.l, X.c, p["atr"]), p["factor"])
    tr = tr.astype(np.int8)
    prev = np.concatenate([[0], tr[:-1]])
    return {"line": line, "direction": tr.astype(np.float64)}, K.events((tr == 1) & (prev == -1), (tr == -1) & (prev == 1))


@reg("Ichimoku Cloud")
def _(X):
    p = P("Ichimoku Cloud")
    mid = lambda n: (K.highest(X.h, n) + K.lowest(X.l, n)) / 2
    tenkan, kijun = mid(p["tenkan"]), mid(p["kijun"])
    a = K.shift((tenkan + kijun) / 2, p["displacement"])
    b = K.shift(mid(p["senkou_b"]), p["displacement"])
    top, bot = np.fmax(a, b), np.fmin(a, b)
    top[np.isnan(a) | np.isnan(b)] = np.nan
    bot[np.isnan(a) | np.isnan(b)] = np.nan
    return {"cloud_top": top, "cloud_bottom": bot}, K.events(K.cross_up(X.c, top), K.cross_dn(X.c, bot))


@njit(cache=True)
def _psar(h, l, c, start, inc, mx):
    """Parabolic SAR theo định nghĩa gốc của Wilder (như TA-Lib/talipp): SAR cho nến kế tiếp được kẹp bởi
    low (khi long) / high (khi short) của nến hiện tại và nến trước TRƯỚC khi kiểm tra đảo chiều.
    Trả về (sar dùng cho nến i, hướng +1 SAR dưới giá / −1 trên giá)."""
    m = len(h)
    sar_out = np.full(m, np.nan)
    trend = np.zeros(m, np.int8)
    if m < 2:
        return sar_out, trend
    # khởi tạo theo hướng chuyển động của 2 nến đầu (giống TA-Lib dùng DM)
    up_move, dn_move = h[1] - h[0], l[0] - l[1]
    is_long = not (dn_move > 0 and dn_move > up_move)
    if is_long:
        ep, sar = h[1], l[0]
    else:
        ep, sar = l[1], h[0]
    af = start
    for i in range(1, m):
        nh, nl = h[i], l[i]
        ph, pl = h[i - 1], l[i - 1]
        if is_long:
            if nl <= sar:
                is_long = False
                sar = max(ep, ph, nh)
                sar_out[i], trend[i] = sar, -1
                af = start
                ep = nl
                sar = sar + af * (ep - sar)
                sar = max(sar, ph, nh)
            else:
                sar_out[i], trend[i] = sar, 1
                if nh > ep:
                    ep = nh
                    af = min(af + inc, mx)
                sar = sar + af * (ep - sar)
                sar = min(sar, pl, nl)
        else:
            if nh >= sar:
                is_long = True
                sar = min(ep, pl, nl)
                sar_out[i], trend[i] = sar, 1
                af = start
                ep = nh
                sar = sar + af * (ep - sar)
                sar = min(sar, pl, nl)
            else:
                sar_out[i], trend[i] = sar, -1
                if nl < ep:
                    ep = nl
                    af = min(af + inc, mx)
                sar = sar + af * (ep - sar)
                sar = max(sar, ph, nh)
    return sar_out, trend


@reg("Parabolic SAR")
def _(X):
    p = P("Parabolic SAR")
    sar, tr = _psar(X.h, X.l, X.c, p["start"], p["inc"], p["max"])
    prev = np.concatenate([[0], tr[:-1]])
    return {"sar": sar}, K.events((tr == 1) & (prev == -1), (tr == -1) & (prev == 1))


def dmi(X, n):
    up, dn = K.change(X.h), -K.change(X.l)
    pdm = np.where(np.isnan(up), np.nan, np.where((up > dn) & (up > 0), up, 0.0))
    mdm = np.where(np.isnan(dn), np.nan, np.where((dn > up) & (dn > 0), dn, 0.0))
    tr = K.true_range(X.h, X.l, X.c)
    tr[0] = np.nan
    trur = K.rma(tr, n)
    plus, minus = 100 * K.safe_div(K.rma(pdm, n), trur), 100 * K.safe_div(K.rma(mdm, n), trur)
    s = plus + minus
    adx = 100 * K.rma(np.where(s == 0, 0.0, np.abs(plus - minus) / np.where(s == 0, 1, s)), n)
    return plus, minus, adx


@reg("Directional Movement")
def _(X):
    plus, minus, _ = dmi(X, P("Directional Movement")["length"])
    return {"plus_di": plus, "minus_di": minus}, K.cross_signal(plus, minus)


@reg("Vortex")
def _(X):
    n = P("Vortex")["length"]
    vmp = K.rsum(np.abs(X.h - K.shift(X.l, 1)), n)
    vmm = K.rsum(np.abs(X.l - K.shift(X.h, 1)), n)
    tr = K.true_range(X.h, X.l, X.c)
    tr[0] = np.nan
    s = K.rsum(tr, n)
    vp, vm = K.safe_div(vmp, s), K.safe_div(vmm, s)
    return {"vi_plus": vp, "vi_minus": vm}, K.cross_signal(vp, vm)


@reg("Williams Alligator")
def _(X):
    p = P("Williams Alligator")
    jaw = K.shift(K.rma(X.hl2, p["jaw"][0]), p["jaw"][1])
    teeth = K.shift(K.rma(X.hl2, p["teeth"][0]), p["teeth"][1])
    lips = K.shift(K.rma(X.hl2, p["lips"][0]), p["lips"][1])
    with np.errstate(invalid="ignore"):
        bull = (lips > teeth) & (teeth > jaw)
        bear = (lips < teeth) & (teeth < jaw)
    return {"jaw": jaw, "teeth": teeth, "lips": lips}, K.events(K.became(bull), K.became(bear))


@reg("Williams Fractal")
def _(X):
    k = P("Williams Fractal")["periods"]
    h, l = X.h, X.l
    fwd = lambda x, j: np.concatenate([x[j:], np.full(j, np.nan)])  # giá trị j nến SAU (chỉ dùng sau khi dịch k nến)
    with np.errstate(invalid="ignore"):
        upf = np.ones(len(h), bool)
        dnf = np.ones(len(h), bool)
        for j in range(1, k + 1):
            upf &= (h > K.shift(h, j)) & (h > fwd(h, j))
            dnf &= (l < K.shift(l, j)) & (l < fwd(l, j))
    # xác nhận tại nến i + k (khi k nến bên phải đã đóng)
    up_lvl = pd.Series(np.where(upf, h, np.nan)).shift(k).ffill().to_numpy()
    dn_lvl = pd.Series(np.where(dnf, l, np.nan)).shift(k).ffill().to_numpy()
    return {"up_fractal": up_lvl, "down_fractal": dn_lvl}, K.events(K.cross_up(X.c, up_lvl), K.cross_dn(X.c, dn_lvl))


@njit(cache=True)
def _bars_since_extreme(x, n, want_max):
    """Số nến từ cực trị (cao nhất/thấp nhất) trong n+1 nến gần nhất; trùng → lấy nến gần nhất."""
    m = len(x)
    out = np.full(m, np.nan)
    for i in range(n, m):
        best = x[i]
        bi = i
        for k in range(i - 1, i - n - 1, -1):
            v = x[k]
            if (want_max and v > best) or ((not want_max) and v < best):
                best = v
                bi = k
        out[i] = i - bi
    return out


@reg("Aroon")
def _(X):
    n = P("Aroon")["length"]
    up = 100 * (n - _bars_since_extreme(X.h, n, True)) / n
    dn = 100 * (n - _bars_since_extreme(X.l, n, False)) / n
    return {"aroon_up": up, "aroon_down": dn}, K.cross_signal(up, dn)


@reg("Trend Strength Index")
def _(X):
    n = P("Trend Strength Index")["length"]
    idx = np.arange(len(X), dtype=np.float64)
    return zero_cross(K.corr(X.c, idx, n))


@reg("Zig Zag")
def _(X):
    from kh.waves.dc import run_dc

    df = pd.DataFrame({"high": X.h, "low": X.l, "close": X.c})
    dc = run_dc(df, np.full(len(X), P("Zig Zag")["deviation"]))
    sig = np.zeros(len(X), np.int8)
    sig[dc["piv_conf"][dc["piv_type"] == -1]] = 1
    sig[dc["piv_conf"][dc["piv_type"] == 1]] = -1
    return {"mode": dc["st_mode"].astype(np.float64)}, sig


@reg("Linear Regression Curve")
def _(X): return price_cross(X, K.linreg(X.c, P("Linear Regression Curve")["length"])[0])


@reg("Linear Regression Slope")
def _(X): return zero_cross(K.linreg(X.c, P("Linear Regression Slope")["length"])[1])


@reg("Keltner Channels")
def _(X):
    p = P("Keltner Channels")
    mid = K.ema(X.c, p["length"])
    rng = K.atr(X.h, X.l, X.c, p["atr"])
    up, lo = mid + p["mult"] * rng, mid - p["mult"] * rng
    return {"upper": up, "lower": lo}, K.events(K.cross_up(X.c, up), K.cross_dn(X.c, lo))


@reg("Donchian Channels")
def _(X):
    n = P("Donchian Channels")["length"]
    up, lo = K.shift(K.highest(X.h, n), 1), K.shift(K.lowest(X.l, n), 1)
    return {"upper": up, "lower": lo}, K.events(K.cross_up(X.c, up), K.cross_dn(X.c, lo))


@reg("Price Channel")
def _(X):
    n = P("Price Channel")["length"]
    return price_cross(X, (K.shift(K.highest(X.h, n), 1) + K.shift(K.lowest(X.l, n), 1)) / 2)


@reg("MA Channel")
def _(X):
    n = P("MA Channel")["length"]
    up, lo = K.sma(X.h, n), K.sma(X.l, n)
    return {"upper": up, "lower": lo}, K.events(K.cross_up(X.c, up), K.cross_dn(X.c, lo))


@reg("Chande Kroll Stop")
def _(X):
    p = P("Chande Kroll Stop")
    a = K.atr(X.h, X.l, X.c, p["p"])
    fh = K.highest(X.h, p["p"]) - p["x"] * a
    fl = K.lowest(X.l, p["p"]) + p["x"] * a
    stop_short, stop_long = K.highest(fh, p["q"]), K.lowest(fl, p["q"])
    return {"stop_short": stop_short, "stop_long": stop_long}, K.events(K.cross_up(X.c, stop_short), K.cross_dn(X.c, stop_long))


@reg("52-Week High/Low")
def _(X):
    n = P("52-Week High/Low")["length"]
    up, lo = K.shift(K.highest(X.h, n), 1), K.shift(K.lowest(X.l, n), 1)
    return {"high": up, "low": lo}, K.events(K.cross_up(X.c, up), K.cross_dn(X.c, lo))


@reg("Majority Rule")
def _(X):
    n = P("Majority Rule")["length"]
    upbar = np.where(np.isnan(K.change(X.c)), np.nan, (K.change(X.c) > 0).astype(np.float64))
    pct = 100 * K.sma(upbar, n)
    return {"pct_up": pct}, K.cross_signal(pct, 50.0)


@reg("ADX")
def _(X): return filt(dmi(X, P("ADX")["length"])[2])


# ======================================================================= A3. Dao động
@reg("MACD")
def _(X):
    p = P("MACD")
    macd = K.ema(X.c, p["fast"]) - K.ema(X.c, p["slow"])
    sig = K.ema(macd, p["signal"])
    return {"macd": macd, "signal": sig, "hist": macd - sig}, K.cross_signal(macd, sig)


@reg("RSI")
def _(X):
    r = K.rsi(X.c, P("RSI")["length"])
    return {"rsi": r}, K.cross_signal(r, 50.0)


def stoch_k(src_c, src_h, src_l, n):
    hh, ll = K.highest(src_h, n), K.lowest(src_l, n)
    return 100 * K.safe_div(src_c - ll, hh - ll)


@reg("Stochastic")
def _(X):
    p = P("Stochastic")
    k = K.sma(stoch_k(X.c, X.h, X.l, p["k"]), p["smooth_k"])
    d = K.sma(k, p["d"])
    return {"k": k, "d": d}, K.cross_signal(k, d)


@reg("Stochastic RSI")
def _(X):
    p = P("Stochastic RSI")
    r = K.rsi(X.c, p["rsi"])
    k = K.sma(stoch_k(r, r, r, p["stoch"]), p["k"])
    d = K.sma(k, p["d"])
    return {"k": k, "d": d}, K.cross_signal(k, d)


@njit(cache=True)
def _streak(c):
    m = len(c)
    out = np.zeros(m)
    for i in range(1, m):
        if c[i] > c[i - 1]:
            out[i] = out[i - 1] + 1 if out[i - 1] > 0 else 1
        elif c[i] < c[i - 1]:
            out[i] = out[i - 1] - 1 if out[i - 1] < 0 else -1
    return out


@reg("Connors RSI")
def _(X):
    p = P("Connors RSI")
    crsi = (K.rsi(X.c, p["rsi"]) + K.rsi(_streak(X.c), p["streak"]) + K.percentrank(100 * K.safe_div(K.change(X.c), K.shift(X.c, 1)), p["rank"])) / 3
    return {"crsi": crsi}, K.cross_signal(crsi, 50.0)


def awesome(X, f, s):
    return K.sma(X.hl2, f) - K.sma(X.hl2, s)


@reg("Awesome Oscillator")
def _(X):
    p = P("Awesome Oscillator")
    return zero_cross(awesome(X, p["fast"], p["slow"]))


@reg("Accelerator Oscillator")
def _(X):
    p = P("Accelerator Oscillator")
    ao = awesome(X, p["fast"], p["slow"])
    return zero_cross(ao - K.sma(ao, p["smooth"]))


@reg("Momentum")
def _(X): return zero_cross(K.change(X.c, P("Momentum")["length"]))


@reg("Chande Momentum Oscillator")
def _(X):
    n = P("Chande Momentum Oscillator")["length"]
    d = K.change(X.c)
    m1 = K.rsum(np.where(np.isnan(d), np.nan, np.maximum(d, 0)), n)
    m2 = K.rsum(np.where(np.isnan(d), np.nan, np.maximum(-d, 0)), n)
    return zero_cross(100 * K.safe_div(m1 - m2, m1 + m2))


@reg("Price Oscillator")
def _(X):
    p = P("Price Oscillator")
    s = K.ema(X.c, p["slow"])
    return zero_cross(100 * K.safe_div(K.ema(X.c, p["fast"]) - s, s))


@reg("Detrended Price Oscillator")
def _(X):
    n = P("Detrended Price Oscillator")["length"]
    return zero_cross(X.c - K.shift(K.sma(X.c, n), n // 2 + 1))


@reg("TRIX")
def _(X):
    n = P("TRIX")["length"]
    e = K.ema(K.ema(K.ema(np.log(X.c), n), n), n)
    return zero_cross(10000 * K.change(e))


@njit(cache=True)
def _fisher(hl2, hh, ll):
    m = len(hl2)
    fish = np.full(m, np.nan)
    val = 0.0
    f = 0.0
    started = False
    for i in range(m):
        if np.isnan(hh[i]) or np.isnan(ll[i]):
            continue
        rng = hh[i] - ll[i]
        x = (hl2[i] - ll[i]) / rng - 0.5 if rng > 0 else 0.0
        val = 0.66 * x + 0.67 * (val if started else 0.0)
        val = min(max(val, -0.999), 0.999)
        f = 0.5 * np.log((1 + val) / (1 - val)) + 0.5 * (f if started else 0.0)
        fish[i] = f
        started = True
    return fish


@reg("Fisher Transform")
def _(X):
    n = P("Fisher Transform")["length"]
    hl2 = X.hl2
    fish = _fisher(hl2, K.highest(hl2, n), K.lowest(hl2, n))
    trig = K.shift(fish, 1)
    return {"fisher": fish, "trigger": trig}, K.cross_signal(fish, trig)


@reg("Ultimate Oscillator")
def _(X):
    p = P("Ultimate Oscillator")
    pc = K.shift(X.c, 1)
    bp = X.c - np.fmin(X.l, pc)
    tr = np.fmax(X.h, pc) - np.fmin(X.l, pc)
    bp[0] = tr[0] = np.nan
    avg = lambda n: K.safe_div(K.rsum(bp, n), K.rsum(tr, n))
    uo = 100 * (4 * avg(p["fast"]) + 2 * avg(p["mid"]) + avg(p["slow"])) / 7
    return {"uo": uo}, K.cross_signal(uo, 50.0)


@reg("Williams %R")
def _(X):
    n = P("Williams %R")["length"]
    hh, ll = K.highest(X.h, n), K.lowest(X.l, n)
    wr = 100 * K.safe_div(X.c - hh, hh - ll)
    return {"wr": wr}, K.cross_signal(wr, -50.0)


def tsi(c, long, short):
    pc = K.change(c)
    return 100 * K.safe_div(K.ema(K.ema(pc, long), short), K.ema(K.ema(np.abs(pc), long), short))


@reg("SMI Ergodic")
def _(X):
    p = P("SMI Ergodic")
    erg = tsi(X.c, p["long"], p["short"])
    sig = K.ema(erg, p["signal"])
    return {"smi": erg, "signal": sig}, K.cross_signal(erg, sig)


def swma(x):
    return K.weighted(x, [1, 2, 2, 1])


@reg("Relative Vigor Index")
def _(X):
    n = P("Relative Vigor Index")["length"]
    rvi = K.safe_div(K.rsum(swma(X.c - X.o), n), K.rsum(swma(X.h - X.l), n))
    sig = swma(rvi)
    return {"rvi": rvi, "signal": sig}, K.cross_signal(rvi, sig)


@reg("True Strength Index")
def _(X):
    p = P("True Strength Index")
    t = tsi(X.c, p["long"], p["short"])
    sig = K.ema(t, p["signal"])
    return {"tsi": t, "signal": sig}, K.cross_signal(t, sig)


@reg("Coppock Curve")
def _(X):
    p = P("Coppock Curve")
    roc = lambda n: 100 * K.safe_div(K.change(X.c, n), K.shift(X.c, n))
    return zero_cross(K.wma(roc(p["long"]) + roc(p["short"]), p["wma"]))


@reg("Rate of Change")
def _(X):
    n = P("Rate of Change")["length"]
    return zero_cross(100 * K.safe_div(K.change(X.c, n), K.shift(X.c, n)))


@reg("Klinger Oscillator")
def _(X):
    p = P("Klinger Oscillator")
    d = tp_change(X.hlc3)
    sv = np.where(np.isnan(d), np.nan, np.where(d >= 0, X.v, -X.v))
    kvo = K.ema(sv, p["fast"]) - K.ema(sv, p["slow"])
    sig = K.ema(kvo, p["signal"])
    return {"kvo": kvo, "signal": sig}, K.cross_signal(kvo, sig)


# ======================================================================= A4. Biến động
def bands(X, n, mult):
    mid = K.sma(X.c, n)
    dev = mult * K.stdev(X.c, n)
    return mid, mid + dev, mid - dev


@reg("Bollinger Bands")
def _(X):
    p = P("Bollinger Bands")
    mid, up, lo = bands(X, p["length"], p["mult"])
    return {"basis": mid, "upper": up, "lower": lo}, K.events(K.cross_up(X.c, up), K.cross_dn(X.c, lo))


@reg("BB %B")
def _(X):
    p = P("BB %B")
    _, up, lo = bands(X, p["length"], p["mult"])
    pb = K.safe_div(X.c - lo, up - lo)
    return {"pctb": pb}, K.cross_signal(pb, 0.5)


@reg("Standard Error Bands")
def _(X):
    p = P("Standard Error Bands")
    val, _, se = K.linreg(X.c, p["length"])
    mid = K.sma(val, p["smooth"])
    dev = K.sma(p["mult"] * se, p["smooth"])
    up, lo = mid + dev, mid - dev
    return {"upper": up, "lower": lo}, K.events(K.cross_up(X.c, up), K.cross_dn(X.c, lo))


@reg("Envelopes")
def _(X):
    p = P("Envelopes")
    mid = K.sma(X.c, p["length"])
    up, lo = mid * (1 + p["percent"] / 100), mid * (1 - p["percent"] / 100)
    return {"upper": up, "lower": lo}, K.events(K.cross_up(X.c, up), K.cross_dn(X.c, lo))


@reg("BB Width")
def _(X):
    p = P("BB Width")
    mid, up, lo = bands(X, p["length"], p["mult"])
    return filt(K.safe_div(up - lo, mid))


@reg("ATR")
def _(X): return filt(K.atr(X.h, X.l, X.c, P("ATR")["length"]) / X.c)


def logret(c):
    return np.log(c / K.shift(c, 1))


@reg("Historical Volatility")
def _(X): return filt(K.stdev(logret(X.c), P("Historical Volatility")["length"]) * np.sqrt(365 * K.BARS_PER_DAY))


@reg("Chaikin Volatility")
def _(X):
    p = P("Chaikin Volatility")
    e = K.ema(X.h - X.l, p["length"])
    return filt(100 * (K.safe_div(e, K.shift(e, p["roc"])) - 1))


@reg("Close-to-Close Volatility")
def _(X): return filt(K.stdev(logret(X.c), P("Close-to-Close Volatility")["length"], ddof=1))


@reg("Non-Directional Close-to-Close Volatility")
def _(X): return filt(np.sqrt(K.sma(logret(X.c) ** 2, P("Non-Directional Close-to-Close Volatility")["length"])))


@reg("O-H-L-C Volatility")
def _(X):
    n = P("O-H-L-C Volatility")["length"]
    gk = 0.5 * np.log(X.h / X.l) ** 2 - (2 * np.log(2) - 1) * np.log(X.c / X.o) ** 2
    return filt(np.sqrt(np.maximum(K.sma(gk, n), 0)))


@reg("Relative Volatility Index")
def _(X):
    p = P("Relative Volatility Index")
    sd = K.stdev(X.c, p["stdev"])
    d = K.change(X.c)
    u = np.where(np.isnan(d) | np.isnan(sd), np.nan, np.where(d <= 0, 0.0, sd))
    dn = np.where(np.isnan(d) | np.isnan(sd), np.nan, np.where(d > 0, 0.0, sd))
    up_e, dn_e = K.ema(u, p["smooth"]), K.ema(dn, p["smooth"])
    return filt(100 * K.safe_div(up_e, up_e + dn_e))


@reg("Standard Deviation")
def _(X): return filt(K.stdev(X.c, P("Standard Deviation")["length"]) / X.c)


@reg("Mass Index")
def _(X):
    p = P("Mass Index")
    e1 = K.ema(X.h - X.l, p["ema"])
    return filt(K.rsum(K.safe_div(e1, K.ema(e1, p["ema"])), p["sum"]))


# ======================================================================= A5. Khối lượng
def tp_change(src):
    """Thay đổi giá điển hình; |Δ| < 1e-10·giá coi là 0 (sai số làm tròn số thực khi (h+l+c)/3 bằng nhau về giá trị)."""
    d = K.change(src)
    return np.where(np.abs(d) < 1e-10 * np.abs(src), 0.0, d)


def signed_vol(X):
    d = K.change(X.c)
    return np.where(np.isnan(d), np.nan, np.sign(d) * X.v)


@reg("Net Volume")
def _(X): return zero_cross(K.rsum(signed_vol(X), P("Net Volume")["length"]))


def cum(x):
    x = np.asarray(x, np.float64)
    return np.nancumsum(x)


@reg("OBV")
def _(X):
    obv = cum(signed_vol(X))
    sig = K.ema(obv, P("OBV")["signal"])
    return {"obv": obv, "signal": sig}, K.cross_signal(obv, sig)


def mfm(X):
    r = X.h - X.l
    return np.where(r == 0, 0.0, ((X.c - X.l) - (X.h - X.c)) / np.where(r == 0, 1, r))


def accdist(X):
    return cum(mfm(X) * X.v)


@reg("Accumulation/Distribution")
def _(X):
    ad = accdist(X)
    sig = K.ema(ad, P("Accumulation/Distribution")["signal"])
    return {"ad": ad, "signal": sig}, K.cross_signal(ad, sig)


@reg("MFI")
def _(X):
    n = P("MFI")["length"]
    src = X.hlc3
    d = tp_change(src)
    up = K.rsum(np.where(np.isnan(d), np.nan, np.where(d <= 0, 0.0, src * X.v)), n)
    dn = K.rsum(np.where(np.isnan(d), np.nan, np.where(d >= 0, 0.0, src * X.v)), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        mfi = np.where(dn == 0, np.where(up == 0, np.nan, 100.0), 100 - 100 / (1 + up / dn))
    mfi[np.isnan(up) | np.isnan(dn)] = np.nan
    return {"mfi": mfi}, K.cross_signal(mfi, 50.0)


@reg("Chaikin Money Flow")
def _(X):
    n = P("Chaikin Money Flow")["length"]
    return zero_cross(K.safe_div(K.rsum(mfm(X) * X.v, n), K.rsum(X.v, n)))


@reg("Chaikin Oscillator")
def _(X):
    p = P("Chaikin Oscillator")
    ad = accdist(X)
    return zero_cross(K.ema(ad, p["fast"]) - K.ema(ad, p["slow"]))


@reg("Ease of Movement")
def _(X):
    p = P("Ease of Movement")
    raw = K.safe_div(p["divisor"] * K.change(X.hl2) * (X.h - X.l), X.v)
    return zero_cross(K.sma(raw, p["length"]))


@reg("Elder Force Index")
def _(X): return zero_cross(K.ema(K.change(X.c) * X.v, P("Elder Force Index")["length"]))


@reg("Price & Volume Trend")
def _(X):
    pvt = cum(K.safe_div(K.change(X.c), K.shift(X.c, 1)) * X.v)
    sig = K.ema(pvt, P("Price & Volume Trend")["signal"])
    return {"pvt": pvt, "signal": sig}, K.cross_signal(pvt, sig)


@reg("Volume")
def _(X): return filt(X.v)


@reg("Volume Oscillator")
def _(X):
    p = P("Volume Oscillator")
    s = K.ema(X.v, p["slow"])
    vo = 100 * K.safe_div(K.ema(X.v, p["fast"]) - s, s)
    with np.errstate(invalid="ignore"):
        return {"value": vo}, vo > 0


def day_index(t):
    return t // 86_400_000


@reg("Volume Profile Fixed Range")
def _(X):
    p = P("Volume Profile Fixed Range")
    d = day_index(X.t)
    days = np.unique(d)
    vah = np.full(len(X), np.nan)
    val = np.full(len(X), np.nan)
    tp = X.hlc3
    # chỉ dùng ngày đã kết thúc (đủ 1 ngày nến) để dựng hồ sơ cho ngày kế tiếp
    starts = np.searchsorted(d, days)
    ends = np.append(starts[1:], len(d))
    for k in range(len(days) - 1):
        a, b = starts[k], ends[k]
        if b - a != K.BARS_PER_DAY:
            continue
        lo, hi = X.l[a:b].min(), X.h[a:b].max()
        if hi <= lo:
            continue
        edges = np.linspace(lo, hi, p["bins"] + 1)
        hist, _ = np.histogram(tp[a:b], bins=edges, weights=X.v[a:b])
        poc = int(np.argmax(hist))
        lo_i = hi_i = poc
        tot, acc = hist.sum(), hist[poc]
        while tot > 0 and acc < p["value_area"] * tot:
            left = hist[lo_i - 1] if lo_i > 0 else -1
            right = hist[hi_i + 1] if hi_i < len(hist) - 1 else -1
            if right >= left:
                hi_i += 1
                acc += hist[hi_i]
            else:
                lo_i -= 1
                acc += hist[lo_i]
        na, nb = starts[k + 1], ends[k + 1]
        if days[k + 1] == days[k] + 1:
            vah[na:nb], val[na:nb] = edges[hi_i + 1], edges[lo_i]
    with np.errstate(invalid="ignore"):
        state = (X.c > vah) | (X.c < val)
    return {"vah": vah, "val": val}, state


# ======================================================================= A6. Khác
@reg("VWAP")
def _(X):
    d = day_index(X.t)
    pv = pd.Series(X.hlc3 * X.v).groupby(d).cumsum().to_numpy()
    vv = pd.Series(X.v).groupby(d).cumsum().to_numpy()
    return price_cross(X, K.safe_div(pv, vv))


@reg("VWMA")
def _(X):
    n = P("VWMA")["length"]
    return price_cross(X, K.safe_div(K.rsum(X.c * X.v, n), K.rsum(X.v, n)))


@reg("Pivot Points Standard")
def _(X):
    d = day_index(X.t)
    g = pd.DataFrame({"d": d, "h": X.h, "l": X.l, "c": X.c, "n": 1}).groupby("d").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"), n=("n", "sum"))
    piv = ((g.h + g.l + g.c) / 3).where(g.n == K.BARS_PER_DAY)
    prev = pd.Series(piv.to_numpy(), index=g.index + 1)  # pivot của ngày trước áp dụng cho ngày sau
    line = prev.reindex(d).to_numpy()
    return price_cross(X, line)


@reg("Balance of Power")
def _(X):
    r = X.h - X.l
    bop = np.where(r == 0, 0.0, (X.c - X.o) / np.where(r == 0, 1, r))
    return zero_cross(K.sma(bop, P("Balance of Power")["length"]))


@reg("Accumulative Swing Index")
def _(X):
    p = P("Accumulative Swing Index")
    c1, o1, l1, h1 = K.shift(X.c, 1), K.shift(X.o, 1), K.shift(X.l, 1), K.shift(X.h, 1)
    A, B, C, D = np.abs(X.h - c1), np.abs(X.l - c1), np.abs(X.h - l1), np.abs(c1 - o1)
    R = np.where((A >= B) & (A >= C), A - 0.5 * B + 0.25 * D, np.where((B >= A) & (B >= C), B - 0.5 * A + 0.25 * D, C + 0.25 * D))
    Kk = np.maximum(A, B)
    with np.errstate(divide="ignore", invalid="ignore"):
        si = np.where(R == 0, 0.0, 50 * (X.c - c1 + 0.5 * (X.c - X.o) + 0.25 * (c1 - o1)) / R * Kk / p["limit"])
    asi = cum(si)
    sig = K.sma(asi, p["signal"])
    return {"asi": asi, "signal": sig}, K.cross_signal(asi, sig)


@reg("Up/Down")
def _(X):
    delta = 2 * X.tb - X.v  # mua chủ động − bán chủ động
    return zero_cross(K.rsum(delta, P("Up/Down")["length"]))


def zscore(x, n):
    return K.safe_div(x - K.sma(x, n), K.stdev(x, n, ddof=1))


@reg("Spread")
def _(X):
    z = zscore(np.log(X.c) - np.log(X.ref), P("Spread")["length"])
    with np.errstate(invalid="ignore"):
        return {"z": z}, np.abs(z) > 1


@reg("Correlation Coefficient")
def _(X): return filt(K.corr(X.c, X.ref, P("Correlation Coefficient")["length"]))


@reg("Correlation-Log")
def _(X): return filt(K.corr(logret(X.c), logret(X.ref), P("Correlation-Log")["length"]))


@reg("Rank Correlation")
def _(X): return filt(K.rank_corr(X.c, X.ref, P("Rank Correlation")["length"]))


@reg("Ratio")
def _(X):
    z = zscore(X.c / X.ref, P("Ratio")["length"])
    with np.errstate(invalid="ignore"):
        return {"z": z}, np.abs(z) > 1


@reg("Standard Error")
def _(X): return filt(K.linreg(X.c, P("Standard Error")["length"])[2] / X.c)


def own_ma_cross(price, n):
    ma = K.sma(price, n)
    return {"price": price, "ma": ma}, K.cross_signal(price, ma)


@reg("Average Price")
def _(X): return own_ma_cross(X.ohlc4, P("Average Price")["length"])


@reg("Typical Price")
def _(X): return own_ma_cross(X.hlc3, P("Typical Price")["length"])


@reg("Median Price")
def _(X): return own_ma_cross(X.hl2, P("Median Price")["length"])


def compute(name: str, X: Ctx):
    """Tính một chỉ báo, ép kiểu float32 cho giá trị và int8/bool cho tín hiệu."""
    out, sig = IMPL[name](X)
    out = {k: np.asarray(v, np.float64).astype(np.float32) for k, v in out.items()}
    kind = BY_NAME[name].kind
    sig = np.asarray(sig).astype(np.int8) if kind == "D" else np.asarray(sig, bool)
    return out, sig
