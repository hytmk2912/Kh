"""Việc C2: quét tổ hợp 2–4 ứng viên × có/không HTF, Bảng A tổ hợp (spec §5).

Quy tắc đồng thuận (chốt trong spec): mỗi sự kiện directional còn hiệu lực 3 nến (nến phát + 2 nến sau).
Tổ hợp phát Long tại t nếu: mọi directional có sự kiện Long còn hiệu lực, ít nhất một sự kiện Long mới phát tại t,
không directional nào có sự kiện Short còn hiệu lực, và mọi filter đang bật. Short đối xứng. Phải có ≥ 1 directional.
Module này chỉ tạo tín hiệu từ chỉ báo; phần chấm điểm dùng kh.ind.score (đọc nhãn) ở bước riêng.
"""
from __future__ import annotations

import itertools
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from kh.config import setup_logging, split_ms
from kh.ind.signals import signals_path

log = setup_logging("ind.combos")
VALID = 3


def prep_parts(sig_df: pd.DataFrame, cand: pd.DataFrame, lo: int, hi: int) -> dict:
    """Mảng bool cho từng ứng viên trên đoạn [lo, hi): long_valid, short_valid, new_long, new_short / filter_on."""
    parts = {}
    for _, r in cand.iterrows():
        x = sig_df[r.key].to_numpy()
        if r.kind == "D":
            x = x.astype(np.int8)
            nl, ns = x == 1, x == -1
            k = np.ones(VALID, np.int64)
            lv = np.convolve(nl.astype(np.int64), k)[: len(x)] > 0
            sv = np.convolve(ns.astype(np.int64), k)[: len(x)] > 0
            parts[r.key] = ("D", lv[lo:hi], sv[lo:hi], nl[lo:hi], ns[lo:hi])
        else:
            parts[r.key] = ("F", x.astype(bool)[lo:hi])
    return parts


def combo_signal(parts: dict, keys: tuple, htf_long=None, htf_short=None) -> np.ndarray:
    D = [parts[k] for k in keys if parts[k][0] == "D"]
    F = [parts[k][1] for k in keys if parts[k][0] == "F"]
    n = len(D[0][1])
    lv = np.ones(n, bool)
    sv_any = np.zeros(n, bool)
    sv = np.ones(n, bool)
    lv_any = np.zeros(n, bool)
    new_l = np.zeros(n, bool)
    new_s = np.zeros(n, bool)
    for _, a_lv, a_sv, a_nl, a_ns in D:
        lv &= a_lv
        sv &= a_sv
        lv_any |= a_lv
        sv_any |= a_sv
        new_l |= a_nl
        new_s |= a_ns
    on = np.ones(n, bool)
    for f in F:
        on &= f
    long_ = lv & new_l & ~sv_any & on
    short_ = sv & new_s & ~lv_any & on
    if htf_long is not None:
        long_ &= htf_long
        short_ &= htf_short
    sig = np.zeros(n, np.int8)
    sig[long_] = 1
    sig[short_] = -1
    return sig


def all_combos(cand: pd.DataFrame) -> list[tuple]:
    keys = cand.key.tolist()
    kinds = dict(zip(cand.key, cand.kind))
    out = []
    for r in (2, 3, 4):
        for c in itertools.combinations(keys, r):
            if any(kinds[k] == "D" for k in c):
                out.append(c)
    return out


def _scan_symbol(args):
    cfg, P, symbol, lo_ms, hi_ms, cand, combos, seed = args
    from kh.ind.single import load_book

    book, m1, sigs = load_book(P, symbol, lo_ms, hi_ms)
    lo, hi = book.lo, book.hi
    parts = prep_parts(sigs, cand, 0, len(sigs))
    hl, hs = sigs.htf_long_ok.to_numpy(), sigs.htf_short_ok.to_numpy()
    rng = np.random.default_rng(seed)
    rows = []
    for c in combos:
        for htf in (False, True):
            sig = combo_signal(parts, c, hl if htf else None, hs if htf else None)
            full = np.zeros(len(sigs), np.int8)
            full[lo:hi] = sig[lo:hi]
            r = book.score(full, rng, bar_metrics=False, random_with_replacement=True)
            rows.append({"combo": "+".join(c), "size": len(c), "htf": htf, "symbol": symbol} | r)
    return rows


def scan(cfg: dict, P, cand: pd.DataFrame, lo_ms: int, hi_ms: int, workers: int = 4, seed: int = 0) -> pd.DataFrame:
    combos = all_combos(cand)
    log.info("Quét %d tổ hợp × 2 HTF × %d symbol", len(combos), len(cfg["symbols"]))
    jobs = [(cfg, P, s, lo_ms, hi_ms, cand, combos, seed + i) for i, s in enumerate(cfg["symbols"])]
    rows = []
    with ProcessPoolExecutor(workers) as ex:
        for res in ex.map(_scan_symbol, jobs):
            rows += res
            log.info("xong %s", res[0]["symbol"] if res else "?")
    return pd.DataFrame(rows)


def aggregate(R: pd.DataFrame) -> pd.DataFrame:
    """Trung vị 5 symbol + giá trị kém nhất; điều kiện precision ≥ 1,5 × ngẫu nhiên (cả Long và Short, trung vị)."""
    num = ["n_long", "n_short", "precision_long", "precision_short", "random_precision_long", "random_precision_short",
           "lift_long", "lift_short", "recall_fast_up", "recall_fast_down", "recall_fast", "recall_slow",
           "false_in_flat_share", "false_in_pullback_share", "false_counter_wave_share", "false_late_share",
           "latency_min_median", "travelled_pct_median", "repeat_signals_per_caught_wave"]
    g = R.groupby(["combo", "size", "htf"], sort=False)
    med = g[num].median()
    worst = pd.DataFrame({"lift_long_worst": g.lift_long.min(), "lift_short_worst": g.lift_short.min(),
                          "recall_fast_worst": g.recall_fast.min()})
    A = pd.concat([med, worst], axis=1).reset_index()
    A["recall_fast_up_down"] = A.recall_fast  # recall sóng nhanh (tăng + giảm) theo đúng số sóng
    A["precision_ok"] = (A.precision_long >= 1.5 * A.random_precision_long) & (A.precision_short >= 1.5 * A.random_precision_short)
    return A


def add_pooled_tests(top: pd.DataFrame, R: pd.DataFrame) -> pd.DataFrame:
    """Thông tin thêm (KHÔNG đổi tiêu chí xếp hạng): số tín hiệu gộp 5 symbol và p binomial một phía
    của precision so với precision ngẫu nhiên gộp — cho biết precision cao có thể chỉ do mẫu nhỏ."""
    from scipy import stats

    key = ["combo", "size", "htf"]
    g = R.assign(cl=R.n_long * R.precision_long.fillna(0), cs=R.n_short * R.precision_short.fillna(0),
                 rl=R.n_long * R.random_precision_long.fillna(0), rs=R.n_short * R.random_precision_short.fillna(0)) \
        .groupby(key)[["n_long", "n_short", "cl", "cs", "rl", "rs"]].sum().reset_index()
    t = top.merge(g, on=key, how="left", suffixes=("", "_tot"))
    for side, n, c, r in (("long", "n_long_tot", "cl", "rl"), ("short", "n_short_tot", "cs", "rs")):
        p0 = (t[r] / t[n]).where(t[n] > 0)
        t[f"pooled_precision_{side}"] = (t[c] / t[n]).where(t[n] > 0)
        t[f"p_binom_{side}"] = [stats.binom.sf(round(k) - 1, int(n_), p) if n_ > 0 else np.nan
                                for k, n_, p in zip(t[c], t[n], p0)]
    return t.drop(columns=["cl", "cs", "rl", "rs"]).rename(columns={"n_long_tot": "n_long_total", "n_short_tot": "n_short_total"})


def run_scan(cfg: dict, P) -> None:
    from kh.ind.trials import log_trials

    lo, hi = split_ms(cfg, "train")
    cand = pd.read_csv(P.reports / "ind" / "candidates.csv")
    R = scan(cfg, P, cand, lo, hi)
    R.to_parquet(P.data / "ind" / "combos_train_by_symbol.parquet", index=False)
    A = aggregate(R)
    out = P.reports / "ind"
    A.to_csv(out / "combos_tableA_all.csv.gz", index=False, compression="gzip")
    ok = A[A.precision_ok].sort_values(["recall_fast_up_down", "precision_long"], ascending=False)
    top = add_pooled_tests(ok.head(50).copy(), R)
    top.insert(0, "rank", range(1, len(top) + 1))
    top.to_csv(out / "combos_tableA.csv", index=False)
    n = log_trials(P.reports, [{"stage": "C2", "trial_id": f"C2-{r.combo}-{'htf' if r.htf else 'nohtf'}", "indicators": r.combo,
                                "htf": r.htf, "params": "mặc định", "split": "train", "symbols": ",".join(cfg["symbols"]),
                                "note": "Bảng A tổ hợp"} for r in A.itertuples()])
    big = A.precision_ok & (A.n_long >= 100) & (A.n_short >= 100)
    log.info("Tổ hợp: %d lần thử (%d mới ghi), %d đạt precision ≥ 1,5× ngẫu nhiên (trong đó %d có ≥ 100 tín hiệu mỗi chiều), top %d",
             len(A), n, len(ok), int(big.sum()), len(top))
