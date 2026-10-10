"""Việc C1: chọn 20 ứng viên (16 directional + 4 filter) theo điểm chốt trước (CHANGELOG 2026-10-09)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from kh.config import setup_logging, split_ms
from kh.ind.signals import signals_path

log = setup_logging("ind.candidates")
MIN_SIGNALS = 100
VALID_BARS = 3  # nến phát + 2 nến sau


def active_direction(sig: np.ndarray, k: int = VALID_BARS) -> np.ndarray:
    """Hướng còn hiệu lực: tổng sự kiện trong k nến gần nhất (cắt về −1/0/+1)."""
    s = np.asarray(sig, np.float32)
    c = np.convolve(s, np.ones(k, np.float32))[: len(s)]
    return np.sign(c).astype(np.float32)


def signal_corr(cfg: dict, P, keys: list[str], kind: str, lo_ms: int, hi_ms: int, tr=None) -> pd.DataFrame:
    """Ma trận tương quan Pearson gộp 5 symbol (cộng dồn tổng để tiết kiệm RAM).
    Track M15: directional dùng cột trạng thái `<key>_st` (dạng xác nhận của tổ hợp, spec M15 §5)."""
    from kh.ind.track import M1

    tr = tr or M1
    k = len(keys)
    n, sx, sxx = 0, np.zeros(k), np.zeros((k, k))
    for s in cfg["symbols"]:
        cols = [c + "_st" for c in keys] if (kind == "D" and tr is not M1) else keys
        sig = pd.read_parquet(signals_path(P, s, tr), columns=["open_time_ms"] + cols)
        m = (sig.open_time_ms >= lo_ms) & (sig.open_time_ms < hi_ms)
        if kind == "D" and tr is not M1:
            X = sig.loc[m, cols].to_numpy(np.float32)
        elif kind == "D":
            X = np.stack([active_direction(sig[c].to_numpy()) for c in keys], axis=1)[m.to_numpy()]
        else:
            X = sig.loc[m, keys].to_numpy(np.float32)
        X = X.astype(np.float64)
        n += len(X)
        sx += X.sum(0)
        sxx += X.T @ X
    mean = sx / n
    cov = sxx / n - np.outer(mean, mean)
    sd = np.sqrt(np.clip(np.diag(cov), 1e-18, None))
    return pd.DataFrame(cov / np.outer(sd, sd), index=keys, columns=keys)


def rank_score(df: pd.DataFrame, cols_hi: list[str], cols_lo: list[str]) -> pd.Series:
    r = [df[c].rank(ascending=False, method="average") for c in cols_hi] + [df[c].rank(ascending=True, method="average") for c in cols_lo]
    return pd.concat(r, axis=1).mean(axis=1)


def select(cfg: dict, P, n_d: int = 16, n_f: int = 4, lo_ms=None, hi_ms=None, A: pd.DataFrame | None = None,
           tr=None) -> pd.DataFrame:
    from kh.ind.track import M1

    tr = tr or M1
    if lo_ms is None:
        lo_ms, hi_ms = split_ms(cfg, "train")
    if A is None:
        A = pd.read_csv(tr.reports(P) / "single_tableA.csv")
    A = A[~A.htf.astype(bool)]
    g = A.groupby(["indicator", "key", "kind"])
    D = g.agg(n_long=("n_long", "median"), n_short=("n_short", "median"), recall_fast=("recall_fast", "median"),
              lift_long=("lift_long", "median"), lift_short=("lift_short", "median"),
              false_flat=("false_in_flat_share", "median"), false_pull=("false_in_pullback_share", "median"),
              latency=("latency_min_median", "median"),
              worst_lift_long=("lift_long", "min"), worst_lift_short=("lift_short", "min"),
              filter_lift=("filter_lift", "median")).reset_index()
    d = D[D.kind == "D"].copy()
    d["eligible"] = (d.n_long >= MIN_SIGNALS) & (d.n_short >= MIN_SIGNALS)
    d["lift"] = (d.lift_long + d.lift_short) / 2
    d["false_flat_pullback"] = d.false_flat + d.false_pull
    d["stability"] = np.minimum(d.worst_lift_long, d.worst_lift_short)
    e = d[d.eligible].copy()
    e["score_rank"] = rank_score(e, ["recall_fast", "lift", "stability"], ["false_flat_pullback", "latency"])
    e = e.sort_values("score_rank")
    f = D[D.kind == "F"].copy().sort_values("filter_lift", ascending=False)
    picked = []
    for kind, pool, n in (("D", e, n_d), ("F", f, n_f)):
        C = signal_corr(cfg, P, pool.key.tolist(), kind, lo_ms, hi_ms, tr)
        chosen = []
        for _, r in pool.iterrows():
            if len(chosen) == n:
                break
            corr_max = max([abs(C.loc[r.key, c]) for c in chosen], default=0.0)
            if corr_max > 0.8:
                continue
            chosen.append(r.key)
            picked.append(r.to_dict() | {"max_abs_corr_with_picked": corr_max, "pick_order": len(chosen)})
    out = pd.DataFrame(picked)
    out.insert(0, "candidate_no", range(1, len(out) + 1))
    return out


def run_candidates(cfg: dict, P) -> None:
    out = select(cfg, P)
    cols = ["candidate_no", "indicator", "key", "kind", "pick_order", "score_rank", "recall_fast", "lift", "lift_long", "lift_short",
            "false_flat_pullback", "latency", "stability", "n_long", "n_short", "filter_lift", "max_abs_corr_with_picked"]
    out[[c for c in cols if c in out.columns]].to_csv(P.reports / "ind" / "candidates.csv", index=False)
    log.info("Ứng viên: %d (%d D + %d F)", len(out), (out.kind == "D").sum(), (out.kind == "F").sum())
