"""Engine backtest lướt sóng M1 (spec §4, bảng baseline) — mọi kết quả tính theo % notional mỗi lệnh.

Quy tắc:
- Tín hiệu tại đóng cửa nến t → vào ở open nến e = t + 1 + delay; giá khớp = open ± trượt giá (tick) bất lợi.
- TP/SL tính từ open nến vào: TP = open·(1 ± tp), SL = open·(1 ∓ sl).
- Duyệt các nến e … e+14 (giữ tối đa 15 phút):
  * nến mở cửa đã vượt SL (gap) → khớp tại open (xấu hơn SL);
  * TP và SL cùng nằm trong một nến → SL trước;
  * tín hiệu ngược chiều tại đóng cửa nến k → thoát ở open nến k+1 (sau khi xét TP/SL trong nến k);
  * hết 15 phút → thoát ở close nến e+14.
  Mọi lần thoát chịu trượt giá bất lợi (kể cả TP — giả định thận trọng).
- Phí taker 2 chiều trên notional. Funding: mỗi mốc thanh toán trong (vào, ra] → PnL −= side·rate.
- Không vào lệnh: nến vào là filler hoặc trong 30 phút sau filler; đang có lệnh mở cùng symbol.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

try:
    from numba import njit
except ImportError:
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]


@dataclass(frozen=True)
class ScalpParams:
    tp: float = 0.0045
    sl: float = 0.0030
    max_hold: int = 15
    fee: float = 0.0005          # taker, mỗi chiều
    slip_ticks: float = 1.0      # mỗi chiều
    delay: int = 0
    filler_block: int = 30


SCENARIOS = {
    "baseline": ScalpParams(),
    "delay+1": ScalpParams(delay=1),
    "tp0.30": ScalpParams(tp=0.0030), "tp0.60": ScalpParams(tp=0.0060),
    "sl0.20": ScalpParams(sl=0.0020), "sl0.40": ScalpParams(sl=0.0040),
    "fee0.02": ScalpParams(fee=0.0002), "fee0.07": ScalpParams(fee=0.0007),
    "slip3": ScalpParams(slip_ticks=3.0),
}


@njit(cache=True)
def _run(o, h, l, c, blocked, sig, tick, tp, sl, max_hold, slip_ticks, delay, lo, hi):
    n = len(c)
    m = 0
    cap = 0
    for t in range(lo, hi):
        if sig[t] != 0:
            cap += 1
    ent = np.empty(cap, np.int64)
    ext = np.empty(cap, np.int64)
    side = np.empty(cap, np.int8)
    raw_in = np.empty(cap)
    raw_out = np.empty(cap)
    reason = np.empty(cap, np.int8)   # 1 TP, −1 SL, 2 tín hiệu ngược, 0 hết giờ
    busy = -1
    slip = slip_ticks * tick
    for t in range(lo, hi):
        s = sig[t]
        if s == 0:
            continue
        e = t + 1 + delay
        if e >= hi or e <= busy or blocked[e]:
            continue
        p0 = o[e]
        tp_px = p0 * (1.0 + s * tp)
        sl_px = p0 * (1.0 - s * sl)
        last = min(e + max_hold - 1, hi - 1)
        r = 0
        xi = last
        xp = c[last]
        for j in range(e, last + 1):
            if j > e and ((s == 1 and o[j] <= sl_px) or (s == -1 and o[j] >= sl_px)):
                r, xi, xp = -1, j, o[j]
                break
            hit_sl = (s == 1 and l[j] <= sl_px) or (s == -1 and h[j] >= sl_px)
            if hit_sl:
                r, xi, xp = -1, j, sl_px
                break
            hit_tp = (s == 1 and h[j] >= tp_px) or (s == -1 and l[j] <= tp_px)
            if hit_tp:
                r, xi, xp = 1, j, tp_px
                break
            if sig[j] == -s and j < last and j + 1 < hi:
                r, xi, xp = 2, j + 1, o[j + 1]
                break
        ent[m], ext[m], side[m] = e, xi, s
        raw_in[m], raw_out[m], reason[m] = p0, xp, r
        m += 1
        busy = xi
    return ent[:m], ext[:m], side[:m], raw_in[:m], raw_out[:m], reason[:m], slip


def blocked_mask(is_filler: np.ndarray, block: int) -> np.ndarray:
    f = np.asarray(is_filler, np.int64)
    return np.convolve(f, np.ones(block + 1, np.int64))[: len(f)] > 0


def run(m1: pd.DataFrame, sig: np.ndarray, tick: float, prm: ScalpParams, lo: int, hi: int,
        funding: pd.DataFrame | None = None, blocked: np.ndarray | None = None) -> pd.DataFrame:
    """Backtest một symbol trên nến [lo, hi). Trả về bảng lệnh với các thành phần PnL (% notional).
    `blocked` (tuỳ chọn): mặt nạ nến không được vào lệnh, thay cho quy tắc filler + filler_block phút."""
    o, h, l, c = (m1[x].to_numpy(np.float64) for x in ("open", "high", "low", "close"))
    blk = blocked_mask(m1.is_filler.to_numpy(), prm.filler_block) if blocked is None else np.asarray(blocked, bool)
    e, x, s, pin, pout, r, slip = _run(o, h, l, c, blk, np.asarray(sig, np.int8), float(tick), prm.tp, prm.sl, prm.max_hold,
                                       prm.slip_ticks, prm.delay, int(lo), int(hi))
    t = m1.open_time_ms.to_numpy()
    T = pd.DataFrame({"entry_idx": e, "exit_idx": x, "side": s.astype(np.int64), "entry_raw": pin, "exit_raw": pout, "reason": r})
    T["entry_ms"] = t[e]
    # thoát ở open (tín hiệu ngược, gap) → thời điểm là mở cửa nến; còn lại → đóng cửa nến
    at_open = (T.reason == 2) | ((T.reason == -1) & (T.exit_raw == o[x]) & (x > e))
    T["exit_ms"] = np.where(at_open, t[x], t[x] + 60_000)
    T["gross"] = T.side * (T.exit_raw / T.entry_raw - 1)
    T["slippage"] = 2 * slip / T.entry_raw
    T["fees"] = prm.fee * (1 + T.exit_raw / T.entry_raw)
    T["funding"] = 0.0
    if funding is not None and len(funding):
        ft, fr = funding.funding_time_ms.to_numpy(), funding.funding_rate.to_numpy()
        cs = np.concatenate([[0.0], np.cumsum(fr)])
        a = np.searchsorted(ft, T.entry_ms.to_numpy(), "right")
        b = np.searchsorted(ft, T.exit_ms.to_numpy(), "right")
        T["funding"] = -T.side * (cs[b] - cs[a])
    T["net"] = T.gross - T.slippage - T.fees + T.funding
    T["hold_min"] = (T.exit_ms - T.entry_ms) / 60_000
    return T


def metrics(T: pd.DataFrame) -> dict:
    if T.empty:
        return {"n_trades": 0, "n_long": 0, "n_short": 0}
    w, ls = T.net[T.net > 0], T.net[T.net <= 0]
    eq = T.sort_values("exit_ms").net.cumsum()
    return {"n_trades": int(len(T)), "n_long": int((T.side == 1).sum()), "n_short": int((T.side == -1).sum()),
            "win_rate": float((T.net > 0).mean()),
            "gross_pct": float(T.gross.sum() * 100), "fees_pct": float(T.fees.sum() * 100),
            "slippage_pct": float(T.slippage.sum() * 100), "funding_pct": float(T.funding.sum() * 100),
            "net_pct": float(T.net.sum() * 100),
            "profit_factor": float(w.sum() / -ls.sum()) if ls.sum() < 0 else np.inf,
            "max_drawdown_pct": float((eq.cummax().clip(lower=0) - eq).max() * 100),
            "expectancy_net_pct": float(T.net.mean() * 100), "expectancy_gross_pct": float(T.gross.mean() * 100),
            "avg_win_pct": float(w.mean() * 100) if len(w) else 0.0, "avg_loss_pct": float(ls.mean() * 100) if len(ls) else 0.0,
            "avg_hold_min": float(T.hold_min.mean()),
            "tp_share": float((T.reason == 1).mean()), "sl_share": float((T.reason == -1).mean()),
            "opposite_exit_share": float((T.reason == 2).mean()), "time_exit_share": float((T.reason == 0).mean())}


# ---------------------------------------------------------------- track M15 (spec M15 §4): tín hiệu M15, thoát trên đường giá M1
M15_BASE = ScalpParams(tp=0.012, sl=0.008, max_hold=32 * 15, fee=0.0005, slip_ticks=1.0)
SCENARIOS_M15 = {
    "baseline": M15_BASE,
    "tp0.80": ScalpParams(tp=0.008, sl=0.008, max_hold=480), "tp1.80": ScalpParams(tp=0.018, sl=0.008, max_hold=480),
    "sl0.50": ScalpParams(tp=0.012, sl=0.005, max_hold=480), "sl1.20": ScalpParams(tp=0.012, sl=0.012, max_hold=480),
    "fee0.02": ScalpParams(tp=0.012, sl=0.008, max_hold=480, fee=0.0002),
    "fee0.07": ScalpParams(tp=0.012, sl=0.008, max_hold=480, fee=0.0007),
    "slip3": ScalpParams(tp=0.012, sl=0.008, max_hold=480, slip_ticks=3.0),
    "no_funding": M15_BASE,  # chạy không truyền funding
}


def tf_to_m1(m1_t: np.ndarray, tf_t: np.ndarray, sig_tf: np.ndarray, tf: int) -> np.ndarray:
    """Đặt tín hiệu của nến khung `tf` (tính khi nến đóng) vào nến M1 CUỐI của nến đó → engine vào lệnh ở open nến M1
    kế tiếp = open nến khung `tf` kế tiếp; tín hiệu ngược thoát ở open nến khung `tf` kế tiếp."""
    out = np.zeros(len(m1_t), np.int8)
    nz = np.flatnonzero(np.asarray(sig_tf) != 0)
    if len(nz):
        pos = np.searchsorted(m1_t, tf_t[nz] + (tf - 1) * 60_000)
        ok = (pos < len(m1_t)) & (m1_t[np.minimum(pos, len(m1_t) - 1)] == tf_t[nz] + (tf - 1) * 60_000)
        out[pos[ok]] = np.asarray(sig_tf)[nz[ok]]
    return out


def tf_blocked_m1(m1_t: np.ndarray, tf_t: np.ndarray, tf_filler: np.ndarray, tf: int, after: int) -> np.ndarray:
    """Không vào lệnh khi nến khung `tf` chứa filler hoặc trong `after` nến khung `tf` sau đó; trải ra từng nến M1."""
    blk_tf = blocked_mask(np.asarray(tf_filler), after)
    j = np.searchsorted(tf_t, (m1_t // (tf * 60_000)) * (tf * 60_000))
    j = np.minimum(j, len(tf_t) - 1)
    return blk_tf[j] & (tf_t[j] == (m1_t // (tf * 60_000)) * (tf * 60_000))


def run_tf(m1: pd.DataFrame, bars: pd.DataFrame, sig_tf: np.ndarray, tf: int, tick: float, prm: ScalpParams,
           lo_ms: int, hi_ms: int, funding: pd.DataFrame | None = None, after_filler: int = 2) -> pd.DataFrame:
    """Backtest tín hiệu khung `tf` (M15) với TP/SL/thoát mô phỏng trên từng nến M1 trong [lo_ms, hi_ms)."""
    t = m1.open_time_ms.to_numpy()
    tt = bars.open_time_ms.to_numpy()
    sig = tf_to_m1(t, tt, sig_tf, tf)
    blk = tf_blocked_m1(t, tt, bars.is_filler.to_numpy(), tf, after_filler)
    lo, hi = int(np.searchsorted(t, lo_ms)), int(np.searchsorted(t, hi_ms))
    return run(m1, sig, tick, prm, lo, hi, funding, blocked=blk)
