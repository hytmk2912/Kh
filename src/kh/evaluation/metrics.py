"""Chỉ số hiệu suất chiến lược và các thước đo chống overfitting (DSR, PBO).

Định nghĩa (vốn không tái đầu tư — mọi lợi nhuận tính trên vốn ban đầu):
- Lợi nhuận ngày = tổng PnL của các lệnh ĐÓNG trong ngày / vốn ban đầu (ngày không có lệnh = 0).
- Sharpe = TB / độ lệch chuẩn lợi nhuận ngày × √365; Sortino dùng độ lệch chuẩn phần âm.
- MaxDD = sụt giảm lớn nhất của đường vốn (theo lệnh đã đóng) so với đỉnh trước đó, tính trên vốn ban đầu.
- Profit factor = tổng lãi / |tổng lỗ|; Expectancy = PnL TB mỗi lệnh (USD và bps của notional).
Giới hạn: đường vốn theo lệnh đã đóng, chưa đánh giá theo giá thị trường trong lúc giữ lệnh.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import pandas as pd
from scipy import stats

DAY = 86_400_000


def daily_returns(T: pd.DataFrame, start_ms: int, end_ms: int, capital: float) -> pd.Series:
    days = np.arange(start_ms // DAY, (end_ms - 1) // DAY + 1)
    if T is None or T.empty:
        return pd.Series(0.0, index=days)
    d = T.groupby(T.exit_ms // DAY).pnl.sum() / capital
    return d.reindex(days, fill_value=0.0)


def perf(T: pd.DataFrame, start_ms: int, end_ms: int, capital: float) -> dict:
    r = daily_returns(T, start_ms, end_ms, capital)
    n_days = len(r)
    eq = 1 + r.cumsum()
    dd = (eq.cummax() - eq).max()
    sd = r.std(ddof=1)
    down = r[r < 0].std(ddof=1) if (r < 0).sum() > 1 else np.nan
    total = float(r.sum())
    out = {"days": n_days, "n_trades": 0 if T is None else int(len(T)), "total_return": total,
           "cagr": (1 + total) ** (365 / max(n_days, 1)) - 1 if total > -1 else -1.0,
           "max_drawdown": float(dd), "sharpe": float(r.mean() / sd * math.sqrt(365)) if sd > 0 else np.nan,
           "sortino": float(r.mean() / down * math.sqrt(365)) if down and down > 0 else np.nan}
    if T is None or T.empty:
        return out | {"net_pnl": 0.0}
    win, loss = T.pnl[T.pnl > 0], T.pnl[T.pnl <= 0]
    out |= {"net_pnl": float(T.pnl.sum()), "gross_pnl": float(T.gross_pnl.sum()), "fees": float(T.fees.sum()),
            "funding": float(T.funding.sum()), "win_rate": float((T.pnl > 0).mean()),
            "avg_win": float(win.mean()) if len(win) else 0.0, "avg_loss": float(loss.mean()) if len(loss) else 0.0,
            "profit_factor": float(win.sum() / -loss.sum()) if loss.sum() < 0 else np.inf,
            "expectancy_usd": float(T.pnl.mean()), "expectancy_bps": float((T.pnl / T.notional).mean() * 1e4),
            "gross_expectancy_bps": float((T.gross_pnl / T.notional).mean() * 1e4),
            "avg_hold_min": float(T.hold_min.mean()), "avg_notional": float(T.notional.mean()),
            "exposure": float(T.hold_min.sum() / (n_days * 1440 * 5)), "long_share": float((T.side == 1).mean()),
            "tp_share": float((T.reason == 1).mean()), "sl_share": float((T.reason == -1).mean()),
            "liq_risk_trades": int(T.liq_risk.sum()), "funding_estimated_trades": int(T.funding_estimated.sum())}
    return out


def bootstrap_expectancy(T: pd.DataFrame, reps: int = 2000, seed: int = 0) -> dict:
    """CI 90% và p một phía (H0: expectancy ≤ 0) của PnL/notional, bootstrap theo ngày đóng lệnh."""
    if T is None or len(T) < 10:
        return {"ci90_bps": [np.nan, np.nan], "p_one_sided": np.nan}
    x = (T.pnl / T.notional).to_numpy()
    g = pd.DataFrame({"x": x, "d": (T.exit_ms // DAY).to_numpy()}).groupby("d").x.agg(["sum", "size"]).to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(g), (reps, len(g)))
    s = g[idx].sum(1)
    m = s[:, 0] / s[:, 1]
    p = float(((m - m.mean()) >= x.mean()).mean())
    return {"ci90_bps": [float(np.quantile(m, 0.05) * 1e4), float(np.quantile(m, 0.95) * 1e4)], "p_one_sided": p}


def drop_top_winners(T: pd.DataFrame, frac: float = 0.05) -> pd.DataFrame:
    if T is None or T.empty:
        return T
    k = int(math.ceil(len(T) * frac))
    return T.drop(T.pnl.nlargest(k).index)


def deflated_sharpe(r: pd.Series, sr_all: np.ndarray) -> dict:
    """Deflated Sharpe Ratio (Bailey & López de Prado 2014), Sharpe theo ngày (chưa nhân √365)."""
    r = np.asarray(r, float)
    T = len(r)
    sr = r.mean() / r.std(ddof=1) if r.std(ddof=1) > 0 else 0.0
    sr_all = np.asarray([x for x in sr_all if np.isfinite(x)])
    N = max(len(sr_all), 1)
    v = sr_all.var(ddof=1) if len(sr_all) > 1 else 0.0
    g = 0.5772156649
    sr0 = math.sqrt(v) * ((1 - g) * stats.norm.ppf(1 - 1 / N) + g * stats.norm.ppf(1 - 1 / (N * math.e))) if N > 1 else 0.0
    sk, ku = stats.skew(r), stats.kurtosis(r, fisher=False)
    den = math.sqrt(max(1 - sk * sr + (ku - 1) / 4 * sr ** 2, 1e-12))
    dsr = stats.norm.cdf((sr - sr0) * math.sqrt(T - 1) / den)
    return {"sr_daily": float(sr), "sr0_daily": float(sr0), "n_trials": int(N), "dsr": float(dsr)}


def pbo_cscv(M: pd.DataFrame, S: int = 16) -> dict:
    """Probability of Backtest Overfitting bằng CSCV. M: ma trận (ngày × biến thể) lợi nhuận ngày."""
    M = M.dropna(how="all").fillna(0.0)
    if M.shape[1] < 2 or len(M) < S * 5:
        return {"pbo": np.nan, "n_combinations": 0}
    blocks = np.array_split(np.arange(len(M)), S)
    X = M.to_numpy()
    mu = np.array([X[b].mean(0) for b in blocks])
    sd = np.array([X[b].std(0) for b in blocks])
    sq = np.array([(X[b] ** 2).sum(0) for b in blocks])
    sm = np.array([X[b].sum(0) for b in blocks])
    n = np.array([len(b) for b in blocks])
    logits = []
    for comb in itertools.combinations(range(S), S // 2):
        isb = np.zeros(S, bool)
        isb[list(comb)] = True

        def sharpe(mask):
            N = n[mask].sum()
            m = sm[mask].sum(0) / N
            v = sq[mask].sum(0) / N - m ** 2
            return m / np.sqrt(np.maximum(v, 1e-18))

        s_is, s_os = sharpe(isb), sharpe(~isb)
        best = int(np.argmax(s_is))
        rank = stats.rankdata(s_os)[best] / (len(s_os) + 1)
        logits.append(math.log(rank / (1 - rank)))
    logits = np.array(logits)
    del mu, sd
    return {"pbo": float((logits <= 0).mean()), "n_combinations": int(len(logits)),
            "median_logit": float(np.median(logits))}
