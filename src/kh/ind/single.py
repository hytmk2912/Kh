"""Việc S1–S2: chấm chỉ báo đơn lẻ trên Train — Bảng A (bắt sóng) và Bảng B (backtest baseline)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from kh.config import setup_logging, split_ms
from kh.ind.indicators.impl import IMPL
from kh.ind.indicators.registry import BY_NAME, CARDS
from kh.ind.score import WaveBook
from kh.ind.signals import col_key, signals_path
from kh.ind.trials import log_trials

log = setup_logging("ind.single")

LOWER_IS_BETTER = {"false_in_flat_share", "false_in_pullback_share", "false_counter_wave_share", "false_late_share",
                   "latency_min_median", "travelled_pct_median", "repeat_signals_per_caught_wave"}


def load_book(P, symbol: str, lo_ms: int, hi_ms: int) -> tuple[WaveBook, pd.DataFrame, pd.DataFrame]:
    from kh.ind.data import load_m1

    m1 = load_m1(P, symbol)
    lab = pd.read_parquet(P.data / "ind" / "labels" / f"bars_{symbol}.parquet").label.to_numpy()
    W = pd.read_parquet(P.data / "ind" / "labels" / f"waves_{symbol}.parquet")
    t = m1.open_time_ms.to_numpy()
    lo, hi = int(np.searchsorted(t, lo_ms)), int(np.searchsorted(t, hi_ms))
    sig = pd.read_parquet(signals_path(P, symbol))
    return WaveBook(m1, lab, W, lo, hi), m1, sig


def apply_htf(sig: np.ndarray, sigs: pd.DataFrame) -> np.ndarray:
    s = sig.copy()
    s[(s == 1) & ~sigs.htf_long_ok.to_numpy()] = 0
    s[(s == -1) & ~sigs.htf_short_ok.to_numpy()] = 0
    return s


def table_a(cfg: dict, P, lo_ms: int, hi_ms: int, seed: int = 0) -> pd.DataFrame:
    rows = []
    for s in cfg["symbols"]:
        book, _, sigs = load_book(P, s, lo_ms, hi_ms)
        rng = np.random.default_rng(seed)
        for c in CARDS:
            if c.name not in IMPL:
                continue
            raw = sigs[col_key(c.name)].to_numpy()
            for htf in (False, True):
                r = {"indicator": c.name, "key": col_key(c.name), "kind": c.kind, "symbol": s, "htf": htf}
                if c.kind == "D":
                    r |= book.score(apply_htf(raw, sigs) if htf else raw, rng)
                    why = ["cột filter_* không áp dụng cho directional"]
                    if r["n_long"] == 0 or r["n_short"] == 0:
                        why.append("không có tín hiệu Long hoặc Short trong train → precision/lift/độ trễ chiều đó là NaN")
                    r["nan_reason"] = "; ".join(why)
                elif not htf:
                    r |= book.filter_lift(raw)
                    r["nan_reason"] = "filter: không cho hướng → không có recall/precision/backtest"
                else:
                    r["nan_reason"] = "filter: HTF không áp dụng (filter không có hướng)"
                rows.append(r)
        log.info("Bảng A %s xong", s)
    return pd.DataFrame(rows)


def summarize(T: pd.DataFrame) -> pd.DataFrame:
    """Tổng hợp 5 symbol: trung vị và giá trị kém nhất (độ ổn định)."""
    num = [c for c in T.columns if T[c].dtype.kind in "fi" and c not in ("htf",)]
    g = T.groupby(["indicator", "key", "kind", "htf"], sort=False)
    med = g[num].median().add_suffix("_median")
    worst = {}
    for c in num:
        worst[c + "_worst"] = g[c].max() if c in LOWER_IS_BETTER else g[c].min()
    return pd.concat([med, pd.DataFrame(worst)], axis=1).reset_index()


def run_table_a(cfg: dict, P) -> None:
    lo, hi = split_ms(cfg, "train")
    T = table_a(cfg, P, lo, hi)
    out = P.reports / "ind"
    T.to_csv(out / "single_tableA.csv", index=False)
    summarize(T).to_csv(out / "single_tableA_summary.csv", index=False)
    log_trials(P.reports, [{"stage": "S1", "trial_id": f"S1-{r.key}-{'htf' if r.htf else 'nohtf'}", "indicators": r.indicator,
                            "htf": r.htf, "params": str(BY_NAME[r.indicator].params), "split": "train",
                            "symbols": ",".join(cfg["symbols"]), "note": "Bảng A đơn lẻ"}
                           for r in T.drop_duplicates(["indicator", "htf"]).itertuples()])
    log.info("Bảng A: %d dòng → %s", len(T), out / "single_tableA.csv")


# ---------------------------------------------------------------- S2: Bảng B — backtest baseline
def table_b(cfg: dict, P, lo_ms: int, hi_ms: int, scenarios: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    from kh.backtest.scalp import SCENARIOS, metrics, run
    from kh.ind.data import load_funding, load_m1, load_ticks

    scenarios = scenarios or SCENARIOS
    ticks = load_ticks(P)
    base_rows, sens_rows = [], []
    for s in cfg["symbols"]:
        m1 = load_m1(P, s)
        fund = load_funding(P, s)
        sigs = pd.read_parquet(signals_path(P, s))
        t = m1.open_time_ms.to_numpy()
        lo, hi = int(np.searchsorted(t, lo_ms)), int(np.searchsorted(t, hi_ms))
        for c in CARDS:
            if c.name not in IMPL or c.kind != "D":
                continue
            raw = sigs[col_key(c.name)].to_numpy()
            for htf in (False, True):
                sig = apply_htf(raw, sigs) if htf else raw
                for name, prm in scenarios.items():
                    m = metrics(run(m1, sig, ticks[s], prm, lo, hi, fund))
                    key = {"indicator": c.name, "key": col_key(c.name), "symbol": s, "htf": htf}
                    if name == "baseline":
                        base_rows.append(key | m)
                    sens_rows.append(key | {"scenario": name, "n_trades": m["n_trades"],
                                            "expectancy_net_pct": m.get("expectancy_net_pct", np.nan),
                                            "net_pct": m.get("net_pct", np.nan), "profit_factor": m.get("profit_factor", np.nan)})
        log.info("Bảng B %s xong", s)
    return pd.DataFrame(base_rows), pd.DataFrame(sens_rows)


def run_table_b(cfg: dict, P) -> None:
    lo, hi = split_ms(cfg, "train")
    B, S = table_b(cfg, P, lo, hi)
    out = P.reports / "ind"
    B.to_csv(out / "single_tableB.csv", index=False)
    S.to_csv(out / "single_tableB_sensitivity.csv", index=False)
    g = B.groupby(["indicator", "key", "htf"], sort=False)
    summ = pd.concat([g[["n_trades", "expectancy_net_pct", "expectancy_gross_pct", "profit_factor", "win_rate", "max_drawdown_pct"]].median().add_suffix("_median"),
                      g["expectancy_net_pct"].min().rename("expectancy_net_pct_worst"),
                      g.apply(lambda d: int((d.expectancy_net_pct > 0).sum()), include_groups=False).rename("symbols_positive")], axis=1).reset_index()
    summ.to_csv(out / "single_tableB_summary.csv", index=False)
    log_trials(P.reports, [{"stage": "S2", "trial_id": f"S2-{r.key}-{'htf' if r.htf else 'nohtf'}-{sc}", "indicators": r.indicator,
                            "htf": r.htf, "params": sc, "split": "train", "symbols": ",".join(cfg["symbols"]), "note": "backtest đơn lẻ"}
                           for r in B.drop_duplicates(["indicator", "htf"]).itertuples() for sc in S.scenario.unique()])
    log.info("Bảng B: %d dòng baseline, %d dòng độ nhạy", len(B), len(S))
