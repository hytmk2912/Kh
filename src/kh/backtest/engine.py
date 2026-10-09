"""Giai đoạn 8 — engine backtest trên nến 1 phút.

Quy tắc thực hiện lệnh (thận trọng):
- Tín hiệu tại đóng cửa nến t → vào lệnh ở giá MỞ CỬA nến t+1+delay, cộng slippage bất lợi.
- TP/SL tính từ giá mở cửa lúc vào. Duyệt từng nến sau khi vào:
  * nếu nến mở cửa đã vượt SL (gap) → khớp tại giá mở cửa (xấu hơn SL);
  * nếu cả TP và SL nằm trong cùng một nến → coi như SL chạm trước (không biết thứ tự trong nến);
  * TP chỉ khớp tại đúng mức TP (không hưởng lợi từ gap).
- Hết thời gian giữ → thoát tại giá đóng cửa nến cuối, slippage bất lợi.
- Phí taker cả hai chiều trên notional. Funding: mỗi mốc thanh toán nằm trong (vào, ra]
  → PnL −= side × rate × notional (long trả khi funding dương).
- Mỗi coin chỉ giữ tối đa một vị thế; tín hiệu đến khi đang có vị thế bị bỏ qua.
- Không vào lệnh nếu có nến filler trong 60 nến trước tín hiệu hoặc tại nến vào lệnh.
Giới hạn: không mô phỏng sổ lệnh, không mô phỏng thanh lý theo mark price (chỉ kiểm tra MAE so với
khoảng cách thanh lý ước tính với đòn bẩy đã chọn).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from kh.config import MS_PER_MIN

try:
    from numba import njit
except ImportError:
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]


@dataclass
class Costs:
    taker_fee: float
    slippage: float  # tỷ lệ, mỗi chiều

    @classmethod
    def from_cfg(cls, cfg: dict, fee_mult: float = 1.0, slip_mult: float = 1.0) -> "Costs":
        return cls(cfg["costs"]["taker_fee"] * fee_mult, cfg["costs"]["slippage_bps"] / 1e4 * slip_mult)


@njit(cache=True)
def _simulate(open_, high, low, close, filler_recent, sig_idx, side, tp, sl, max_hold, exit_at, delay, slip):
    n = len(close)
    m = len(sig_idx)
    out_e = np.full(m, -1, np.int64)
    out_x = np.full(m, -1, np.int64)
    out_pe = np.full(m, np.nan)
    out_px = np.full(m, np.nan)
    out_reason = np.zeros(m, np.int8)   # 1 TP, -1 SL, 0 hết giờ / thoát theo quy tắc
    out_mae = np.full(m, np.nan)
    busy_until = -1
    for k in range(m):
        e = sig_idx[k] + 1 + delay
        if e >= n or e <= busy_until or filler_recent[sig_idx[k]] or filler_recent[e]:
            continue
        s = side[k]
        p0 = open_[e]
        tp_px = p0 * (1.0 + s * tp[k]) if not np.isnan(tp[k]) else np.nan
        sl_px = p0 * (1.0 - s * sl[k]) if not np.isnan(sl[k]) else np.nan
        last_rule = exit_at[k] - 1 if exit_at[k] >= 0 else n - 1
        last_time = e + max_hold[k] - 1 if max_hold[k] > 0 else n - 1
        last = min(last_rule, last_time, n - 1)
        if last < e:
            continue
        reason = 0
        xi = last
        xp = close[last]
        worst = 0.0
        for j in range(e, last + 1):
            adv = (p0 - low[j]) / p0 if s == 1 else (high[j] - p0) / p0
            if adv > worst:
                worst = adv
            if not np.isnan(sl_px):
                if j > e and ((s == 1 and open_[j] <= sl_px) or (s == -1 and open_[j] >= sl_px)):
                    reason = -1; xi = j; xp = open_[j]
                    break
                if (s == 1 and low[j] <= sl_px) or (s == -1 and high[j] >= sl_px):
                    reason = -1; xi = j; xp = sl_px
                    break
            if not np.isnan(tp_px):
                if (s == 1 and high[j] >= tp_px) or (s == -1 and low[j] <= tp_px):
                    reason = 1; xi = j; xp = tp_px
                    break
        if reason == 0 and exit_at[k] >= 0 and exit_at[k] < n and last_rule <= last_time:
            xi = exit_at[k]
            xp = open_[exit_at[k]]
        out_e[k] = e
        out_x[k] = xi
        out_pe[k] = p0 * (1.0 + s * slip)
        out_px[k] = xp * (1.0 - s * slip)
        out_reason[k] = reason
        out_mae[k] = worst
        busy_until = xi
    return out_e, out_x, out_pe, out_px, out_reason, out_mae


def run_symbol(k: pd.DataFrame, funding: pd.DataFrame | None, signals: pd.DataFrame, costs: Costs, cfg: dict,
               delay: int = 0, funding_last_known_ms: int | None = None) -> pd.DataFrame:
    """signals: cột bar_idx, side (+1/−1), tp, sl, max_hold (nến, 0 = không giới hạn), exit_at (−1 = không),
    risk_frac (khoảng cách dùng để tính kích thước vị thế)."""
    if signals.empty:
        return pd.DataFrame()
    sg = signals.sort_values("bar_idx").reset_index(drop=True)
    filler_recent = (k.is_filler.astype(float).rolling(60, min_periods=1).sum() > 0).to_numpy()
    e, x, pe, px, reason, mae = _simulate(
        k.open.to_numpy(np.float64), k.high.to_numpy(np.float64), k.low.to_numpy(np.float64),
        k.close.to_numpy(np.float64), filler_recent, sg.bar_idx.to_numpy(np.int64), sg.side.to_numpy(np.int64),
        sg.tp.to_numpy(np.float64), sg.sl.to_numpy(np.float64), sg.max_hold.to_numpy(np.int64),
        sg.exit_at.to_numpy(np.int64), int(delay), float(costs.slippage))
    done = e >= 0
    t = k.open_time_ms.to_numpy()
    T = sg[done].copy()
    T["entry_idx"], T["exit_idx"] = e[done], x[done]
    T["entry_ms"] = t[e[done]]
    # thoát tại giá mở cửa (quy tắc / gap) hoặc trong nến (TP/SL) hay cuối nến (hết giờ): dùng mốc cuối nến
    T["exit_ms"] = t[x[done]] + MS_PER_MIN
    T["entry_px"], T["exit_px"], T["reason"], T["mae"] = pe[done], px[done], reason[done], mae[done]
    bt = cfg["backtest"]
    cap, nsym = bt["initial_capital"], len(cfg["symbols"])
    T["notional"] = np.minimum(bt["risk_per_trade"] * cap / T.risk_frac.clip(lower=1e-4),
                               bt["max_leverage_per_position"] * cap / nsym)
    # PnL thô (giá mở/thoát chưa trừ slippage) để tách edge khỏi chi phí
    T["raw_pnl"] = T.side * ((T.exit_px / (1 - T.side * costs.slippage)) / (T.entry_px / (1 + T.side * costs.slippage)) - 1) * T.notional
    T["gross_pnl"] = T.side * (T.exit_px / T.entry_px - 1) * T.notional  # sau slippage, trước phí & funding
    T["fees"] = costs.taker_fee * T.notional * (1 + T.exit_px / T.entry_px)
    T["funding"], T["funding_estimated"] = _funding(T, funding, funding_last_known_ms)
    T["pnl"] = T.gross_pnl - T.fees + T.funding
    T["hold_min"] = (T.exit_ms - T.entry_ms) / MS_PER_MIN
    lev = bt["max_leverage_per_position"]
    T["liq_risk"] = T.mae >= (1 / lev - 0.005)  # ước tính thô: lề duy trì 0,5%
    return T


def _funding(T: pd.DataFrame, funding: pd.DataFrame | None, last_known_ms: int | None):
    if funding is None or funding.empty or T.empty:
        return np.zeros(len(T)), np.zeros(len(T), bool)
    ft = funding.funding_time_ms.to_numpy()
    fr = funding.funding_rate.to_numpy()
    cs = np.concatenate([[0.0], np.cumsum(fr)])
    a = np.searchsorted(ft, T.entry_ms.to_numpy(), side="right")
    b = np.searchsorted(ft, T.exit_ms.to_numpy(), side="right")
    paid = cs[b] - cs[a]
    # Mốc funding sau khi dữ liệu kết thúc: ước tính bằng mức funding cuối cùng đã biết
    last_ft = ft[-1]
    extra = np.maximum(0, (np.floor(T.exit_ms.to_numpy() / (8 * 3_600_000)) -
                           np.floor(np.maximum(T.entry_ms.to_numpy(), last_ft) / (8 * 3_600_000))))
    est = extra > 0
    paid = paid + extra * fr[-1]
    return -T.side.to_numpy() * paid * T.notional.to_numpy(), est
