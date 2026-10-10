"""Việc N4 (track M15, spec M15 §5–6): tổ hợp KÍCH HOẠT + XÁC NHẬN, Bảng A tổ hợp, walk-forward, Bảng B,
tiêu chí "đạt" chốt trước.

Cấu trúc tổ hợp: 1 directional kích hoạt (dạng SỰ KIỆN tại nến t) + 1 hoặc 2 directional xác nhận (dạng TRẠNG THÁI
cùng chiều tại nến t) + bộ lọc ∈ {không, filter tốt nhất trong 3} × HTF (H1 + H4) có/không.
10 × (9 + 36) × 2 × 2 = 1.800 lần thử. Module tạo tín hiệu chỉ đọc cột tín hiệu; chấm điểm dùng kh.ind.score.
"""
from __future__ import annotations

import itertools
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from kh.backtest.scalp import M15_BASE, ScalpParams, metrics, run_tf
from kh.config import setup_logging, split_ms, write_json
from kh.evaluation.metrics import pbo_cscv
from kh.evaluation.wf import DAY, monthly_folds
from kh.ind.candidates import select
from kh.ind.indicators import core as K
from kh.ind.indicators.registry import BY_NAME
from kh.ind.signals import signals_path
from kh.ind.track import M15
from kh.ind.trials import count_trials, log_trials
from kh.ind.wf import bootstrap_ci, daily_series, dsr, name_map, scaled_params

log = setup_logging("ind15.combos")
N_D, N_F = 10, 3
TOP_N = 30
MIN_SIGNALS = 30      # trung vị số tín hiệu (Long + Short) mỗi symbol trong train [A]: "≥ 30 lệnh/symbol"
PRECISION_X = 1.2
CRIT = {"c1_trades_ge_100": "≥ 100 lệnh ngoài mẫu", "c2_exp_and_ci_low_pos": "expectancy ròng > 0 và cận dưới CI95 > 0",
        "c3_dsr_ge_095": "DSR ≥ 0,95 (lần thử track M15)", "c4_symbols_pos_ge_3": "expectancy > 0 ở ≥ 3/5 symbol",
        "c5_no_sign_flip": "không đổi dấu khi tham số × 0,8 / × 1,2"}


# ------------------------------------------------------------------ tổ hợp
def combo_list(cand: pd.DataFrame) -> list[dict]:
    D = cand[cand.kind == "D"].sort_values("pick_order").key.tolist()
    F = cand[cand.kind == "F"].sort_values("pick_order").key.tolist()
    best_f = F[0] if F else None
    out = []
    for trig in D:
        others = [k for k in D if k != trig]
        for r in (1, 2):
            for conf in itertools.combinations(others, r):
                for filt in (None, best_f):
                    for htf in (False, True):
                        out.append({"combo": f"{trig}>{'+'.join(conf)}|{filt or '-'}", "trigger": trig, "confirm": "+".join(conf),
                                    "filter": filt or "", "htf": htf})
    return out


def parse(combo: str) -> tuple[str, list[str], str | None]:
    head, filt = combo.split("|")
    trig, conf = head.split(">")
    return trig, conf.split("+"), (None if filt == "-" else filt)


def combo_signal(sigs: pd.DataFrame | dict, combo: str, htf: bool) -> np.ndarray:
    trig, conf, filt = parse(combo)
    e = np.asarray(sigs[trig]).astype(np.int8)
    L, S = e == 1, e == -1
    for c in conf:
        st = np.asarray(sigs[c + "_st"])
        L &= st == 1
        S &= st == -1
    if filt:
        on = np.asarray(sigs[filt]).astype(bool)
        L &= on
        S &= on
    if htf:
        L &= np.asarray(sigs["htf_long_ok"]).astype(bool)
        S &= np.asarray(sigs["htf_short_ok"]).astype(bool)
    out = np.zeros(len(e), np.int8)
    out[L] = 1
    out[S] = -1
    return out


# ------------------------------------------------------------------ Bảng A tổ hợp
def _scan_symbol(args):
    cfg, P, symbol, lo_ms, hi_ms, combos, seed = args
    from kh.ind.single import load_book

    book, _, sigs = load_book(P, symbol, lo_ms, hi_ms, M15)
    cols = {c: sigs[c].to_numpy() for c in sigs.columns}
    rng = np.random.default_rng(seed)
    rows = []
    for c in combos:
        sig = combo_signal(cols, c["combo"], c["htf"])
        full = np.zeros(len(sig), np.int8)
        full[book.lo:book.hi] = sig[book.lo:book.hi]
        r = book.score(full, rng, bar_metrics=False, random_with_replacement=True)
        rows.append(c | {"symbol": symbol} | r)
    return rows


def scan(cfg: dict, P, cand: pd.DataFrame, lo_ms: int, hi_ms: int, workers: int = 4, seed: int = 0) -> pd.DataFrame:
    combos = combo_list(cand)
    jobs = [(cfg, P, s, lo_ms, hi_ms, combos, seed + i) for i, s in enumerate(cfg["symbols"])]
    rows = []
    with ProcessPoolExecutor(workers) as ex:
        for res in ex.map(_scan_symbol, jobs):
            rows += res
    return pd.DataFrame(rows)


def aggregate(R: pd.DataFrame) -> pd.DataFrame:
    """Trung vị 5 symbol + kém nhất; điều kiện: trung vị tín hiệu ≥ 30/symbol và precision ≥ 1,2 × ngẫu nhiên
    (cả Long và Short, trung vị)."""
    R = R.assign(n_signals=R.n_long + R.n_short)
    num = ["n_signals", "n_long", "n_short", "precision_long", "precision_short", "random_precision_long", "random_precision_short",
           "lift_long", "lift_short", "recall_fast_up", "recall_fast_down", "recall_fast", "recall_slow",
           "false_in_flat_share", "false_in_pullback_share", "false_counter_wave_share", "false_late_share",
           "latency_min_median", "travelled_pct_median"]
    g = R.groupby(["combo", "trigger", "confirm", "filter", "htf"], sort=False)
    A = pd.concat([g[num].median(), pd.DataFrame({"lift_long_worst": g.lift_long.min(), "lift_short_worst": g.lift_short.min(),
                                                  "n_signals_worst": g.n_signals.min()})], axis=1).reset_index()
    A["precision_mean"] = (A.precision_long + A.precision_short) / 2
    A["enough_signals"] = A.n_signals >= MIN_SIGNALS
    A["precision_ok"] = (A.precision_long >= PRECISION_X * A.random_precision_long) & \
                        (A.precision_short >= PRECISION_X * A.random_precision_short)
    A["eligible"] = A.enough_signals & A.precision_ok
    return A


def top_from(R: pd.DataFrame, n: int = TOP_N, exclude_symbol: str | None = None) -> pd.DataFrame:
    if exclude_symbol:
        R = R[R.symbol != exclude_symbol]
    A = aggregate(R)
    return A[A.eligible].sort_values(["recall_fast", "precision_mean"], ascending=False).head(n)


def run_n4a(cfg: dict, P, workers: int = 4) -> None:
    out = M15.reports(P)
    lo, hi = split_ms(cfg, "train")
    cand = select(cfg, P, N_D, N_F, lo, hi, tr=M15)
    cols = ["candidate_no", "indicator", "key", "kind", "pick_order", "score_rank", "recall_fast", "lift", "lift_long", "lift_short",
            "false_flat_pullback", "latency", "stability", "n_long", "n_short", "filter_lift", "max_abs_corr_with_picked"]
    cand = cand[[c for c in cols if c in cand.columns]]
    cand.to_csv(out / "candidates.csv", index=False)
    log.info("Ứng viên: %d D + %d F; filter dùng trong tổ hợp: %s", (cand.kind == "D").sum(), (cand.kind == "F").sum(),
             cand[cand.kind == "F"].sort_values("pick_order").indicator.iloc[0])
    R = scan(cfg, P, cand, lo, hi, workers)
    (M15.data(P)).mkdir(parents=True, exist_ok=True)
    R.to_parquet(M15.data(P) / "combos_train_by_symbol.parquet", index=False)
    A = aggregate(R)
    names = name_map(P)
    A.insert(1, "indicators", A.combo.map(lambda c: describe(c, names)))
    A.to_csv(out / "combos_tableA_all.csv.gz", index=False, compression="gzip")
    top = A[A.eligible].sort_values(["recall_fast", "precision_mean"], ascending=False).head(TOP_N).copy()
    top.insert(0, "rank", range(1, len(top) + 1))
    top.to_csv(out / "combos_tableA.csv", index=False)
    n = log_trials(P.reports, [{"stage": "N4a", "trial_id": f"N4a-{r.combo}-{'htf' if r.htf else 'nohtf'}", "indicators": r.combo,
                                "htf": r.htf, "params": "mặc định (quy đổi M15)", "split": "train", "symbols": ",".join(cfg["symbols"]),
                                "note": "Bảng A tổ hợp kích hoạt + xác nhận"} for r in A.itertuples()], track=M15.name)
    log.info("Tổ hợp: %d lần thử (%d mới ghi); đủ tín hiệu %d; precision đạt %d; cả hai %d → top %d", len(A), n,
             int(A.enough_signals.sum()), int(A.precision_ok.sum()), int(A.eligible.sum()), len(top))


def describe(combo: str, names: dict) -> str:
    trig, conf, filt = parse(combo)
    s = f"{names[trig]} (kích hoạt) + " + " + ".join(f"{names[c]} (xác nhận)" for c in conf)
    return s + (f" + {names[filt]} (lọc)" if filt else "")


# ------------------------------------------------------------------ walk-forward (N4b)
class SymbolData15:
    def __init__(self, P, symbol):
        from kh.ind.data import load_bars, load_funding, load_m1, load_ticks

        self.symbol = symbol
        self.m1 = load_m1(P, symbol)
        self.bars = load_bars(P, symbol, M15.tf)
        self.tb = self.bars.open_time_ms.to_numpy()
        self.sigs = pd.read_parquet(signals_path(P, symbol, M15))
        self.fund = load_funding(P, symbol)
        self.tick = load_ticks(P)[symbol]
        self.atr_rel = K.atr(*(self.bars[x].to_numpy(np.float64) for x in ("high", "low", "close")), 14) / self.bars.close.to_numpy()

    def idx(self, ms):
        return int(np.searchsorted(self.tb, ms))


def backtest(sd: SymbolData15, combo: str, htf: bool, lo_ms: int, hi_ms: int, prm: ScalpParams = M15_BASE,
             sigs: pd.DataFrame | None = None) -> pd.DataFrame:
    sig = combo_signal(sd.sigs if sigs is None else sigs, combo, htf)
    T = run_tf(sd.m1, sd.bars, sig, M15.tf, sd.tick, prm, lo_ms, hi_ms, sd.fund, M15.unknown_after_filler)
    j = np.searchsorted(sd.tb, T.entry_ms.to_numpy(), "right") - 2  # nến M15 phát tín hiệu (đã đóng)
    T["atr_rel"] = sd.atr_rel[np.maximum(j, 0)]
    return T


def _table_a_one(args):
    from kh.ind.single import table_a

    cfg, P, s, lo, hi = args
    c = dict(cfg)
    c["symbols"] = [s]
    return table_a(c, P, lo, hi, tr=M15)


def fold_selection(cfg: dict, P, f, workers: int = 4):
    with ProcessPoolExecutor(workers) as ex:
        A = pd.concat(list(ex.map(_table_a_one, [(cfg, P, s, f.train_lo, f.train_hi) for s in cfg["symbols"]])), ignore_index=True)
    cand = select(cfg, P, N_D, N_F, f.train_lo, f.train_hi, A=A, tr=M15)
    R = scan(cfg, P, cand, f.train_lo, f.train_hi, workers)
    return A, cand, R


def run_n4b(cfg: dict, P, workers: int = 4) -> None:
    out = M15.reports(P)
    wf_dir = M15.data(P) / "wf"
    wf_dir.mkdir(parents=True, exist_ok=True)
    (out / "wf").mkdir(parents=True, exist_ok=True)
    folds = monthly_folds(cfg["splits"]["train"][0], cfg["splits"]["val"][1], 6, cfg["splits"]["embargo_minutes"] // 1440)
    syms = cfg["symbols"]
    SD = {s: SymbolData15(P, s) for s in syms}
    trades, sel_rows = [], []
    for f in folds:
        cache = wf_dir / f"fold{f.no:02d}"
        if (cache / "R.parquet").exists():
            R, cand = pd.read_parquet(cache / "R.parquet"), pd.read_csv(cache / "cand.csv")
            log.info("Fold %d (%s): dùng kết quả chọn đã lưu", f.no, f.label)
        else:
            cache.mkdir(exist_ok=True)
            A, cand, R = fold_selection(cfg, P, f, workers)
            R.to_parquet(cache / "R.parquet", index=False)
            cand.to_csv(cache / "cand.csv", index=False)
            log_trials(P.reports, [
                {"stage": "N4b-S1", "trial_id": f"N4b-f{f.no:02d}-S1", "indicators": "99 chỉ báo đơn lẻ", "htf": "cả hai",
                 "params": "mặc định (quy đổi M15)", "split": f"train fold {f.label}", "symbols": ",".join(syms),
                 "note": "Bảng A đơn lẻ trong fold", "n_trials": int(A.drop_duplicates(["indicator", "htf"]).shape[0])},
                {"stage": "N4b-C", "trial_id": f"N4b-f{f.no:02d}-C", "indicators": "tổ hợp kích hoạt + xác nhận của fold", "htf": "cả hai",
                 "params": "mặc định (quy đổi M15)", "split": f"train fold {f.label}", "symbols": ",".join(syms),
                 "note": "quét tổ hợp trong fold", "n_trials": int(R.drop_duplicates(["combo", "htf"]).shape[0])}], track=M15.name)
        top = top_from(R)
        top.to_csv(out / "wf" / f"fold{f.no:02d}_{f.label}_top.csv", index=False)
        for _, r in top.iterrows():
            sel_rows.append({"fold": f.no, "month": f.label, "combo": r.combo, "htf": bool(r.htf)})
            for s in syms:
                T = backtest(SD[s], r.combo, bool(r.htf), f.test_lo, f.test_hi)
                T["fold"], T["month"], T["combo"], T["htf"], T["symbol"] = f.no, f.label, r.combo, bool(r.htf), s
                trades.append(T)
        log.info("Fold %d (%s): %d tổ hợp được chọn", f.no, f.label, len(top))
    TR = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()
    TR.to_parquet(M15.data(P) / "wf_trades.parquet", index=False)
    SEL = pd.DataFrame(sel_rows, columns=["fold", "month", "combo", "htf"])
    SEL.to_csv(out / "wf" / "selections.csv", index=False)
    table_b(cfg, P, folds, TR, SEL, SD)


def table_b(cfg, P, folds, TR, SEL, SD) -> None:
    out = M15.reports(P)
    syms = cfg["symbols"]
    n15 = count_trials(P.reports, track=M15.name)
    n_all = n15 + count_trials(P.reports, track="ind")
    days_all = np.arange(folds[0].test_lo // DAY, (folds[-1].test_hi - 1) // DAY + 1)
    tr_lo, tr_hi = split_ms(cfg, "train")
    thr = {s: np.nanquantile(SD[s].atr_rel[SD[s].idx(tr_lo):SD[s].idx(tr_hi)], [1 / 3, 2 / 3]) for s in syms}
    if TR.empty:
        log.warning("Không có lệnh ngoài mẫu nào")
        write_json({"n_folds": len(folds), "n_trials_m15": n15, "n_combos_evaluated": 0, "n_pass_all": 0}, out / "wf" / "summary.json")
        return
    TR["vol_regime"] = [("thấp", "vừa", "cao")[int(np.searchsorted(thr[s], a))] if np.isfinite(a) else "na"
                        for s, a in zip(TR.symbol, TR.atr_rel)]
    rows, daily = [], {}
    for (combo, htf), g in TR.groupby(["combo", "htf"]):
        m = metrics(g)
        lo95, hi95 = bootstrap_ci(g)
        per_sym = {s: g[g.symbol == s].net.mean() * 100 if (g.symbol == s).any() else np.nan for s in syms}
        per_reg = {f"exp_regime_{k}": (g[g.vol_regime == k].net.mean() * 100 if (g.vol_regime == k).any() else np.nan)
                   for k in ("thấp", "vừa", "cao")}
        sel = SEL[(SEL.combo == combo) & (SEL.htf == htf)]
        sel_days = np.concatenate([np.arange(f.test_lo // DAY, (f.test_hi - 1) // DAY + 1) for f in folds if (sel.fold == f.no).any()])
        daily[f"{combo}|{htf}"] = daily_series(g, days_all, len(syms))
        rows.append({"combo": combo, "htf": htf, "n_folds_selected": int(len(sel)), "oos_days": len(sel_days), **m,
                     "expectancy_ci95_low_pct": lo95, "expectancy_ci95_high_pct": hi95,
                     **{f"exp_{s}": v for s, v in per_sym.items()}, **per_reg,
                     "symbols_positive": int(sum(v > 0 for v in per_sym.values() if np.isfinite(v))),
                     "_daily": daily_series(g, sel_days, len(syms)).to_numpy()})
    B = pd.DataFrame(rows)
    srs = [x.mean() / x.std(ddof=1) if len(x) > 1 and x.std(ddof=1) > 0 else 0.0 for x in B._daily]
    sr_var = float(np.var(srs, ddof=1)) if len(srs) > 1 else 0.0
    D15 = pd.DataFrame([dsr(x, sr_var, n15) for x in B._daily])
    Dall = pd.DataFrame([dsr(x, sr_var, n_all) for x in B._daily])[["sr0_daily", "dsr"]].add_suffix("_m1_m15")
    B = pd.concat([B.drop(columns="_daily"), D15, Dall], axis=1)
    pbo = pbo_cscv(pd.DataFrame(daily), S=16) if len(daily) >= 2 else {"pbo": np.nan}
    B["pbo_all_combos"], B["n_trials_m15"], B["n_trials_m1_m15"] = pbo.get("pbo"), n15, n_all
    B = B.sort_values(["expectancy_net_pct", "profit_factor", "max_drawdown_pct"], ascending=[False, False, True]).reset_index(drop=True)
    B.insert(0, "rank_b", range(1, len(B) + 1))
    names = name_map(P)
    B.insert(2, "indicators", B.combo.map(lambda c: describe(c, names)))
    B["c1_trades_ge_100"] = B.n_trades >= 100
    B["c2_exp_and_ci_low_pos"] = (B.expectancy_net_pct > 0) & (B.expectancy_ci95_low_pct > 0)
    B["c3_dsr_ge_095"] = B.dsr >= 0.95
    B["c4_symbols_pos_ge_3"] = B.symbols_positive >= 3
    pre = B.c1_trades_ge_100 & B.c2_exp_and_ci_low_pos & B.c3_dsr_ge_095 & B.c4_symbols_pos_ge_3
    rob_idx = sorted(set(B.index[:10]) | set(B.index[pre]))
    R = robustness(cfg, P, B.loc[rob_idx], SEL, SD, folds)
    B = B.merge(R, on=["combo", "htf"], how="left")
    B["c5_no_sign_flip"] = B.sens_sign_flip.eq(False)
    B["pass_all"] = pre & B.c5_no_sign_flip
    B.to_csv(out / "combos_tableB.csv", index=False)
    summary = {"n_folds": len(folds), "n_trials_m15": n15, "n_trials_m1_m15": n_all, "pbo": pbo,
               "n_combos_evaluated": int(len(B)), "n_trades_total": int(B.n_trades.sum()),
               "pooled_expectancy_net_pct": float(B.net_pct.sum() / B.n_trades.sum()),
               "pooled_expectancy_gross_pct": float(B.gross_pct.sum() / B.n_trades.sum()),
               "n_expectancy_positive": int((B.expectancy_net_pct > 0).sum()),
               **{f"n_{k}": int(B[k].sum()) for k in CRIT}, "n_pass_all": int(B.pass_all.sum()),
               "dsr_max": float(B.dsr.max())}
    write_json(summary, out / "wf" / "summary.json")
    top10_md(cfg, B.head(10), summary, folds, out / "top10.md")
    log.info("Bảng B: %d tổ hợp ngoài mẫu, %d lệnh; đạt cả 5 tiêu chí: %d", len(B), summary["n_trades_total"], summary["n_pass_all"])


def signals_scaled(P, sd: SymbolData15, combo: str, f: float) -> pd.DataFrame:
    """Tín hiệu M15 của các chỉ báo trong tổ hợp với mọi tham số số × f (quy đổi M15 giữ nguyên trước khi nhân)."""
    from kh.ind.indicators.impl import compute, timeframe
    from kh.ind.signals import build_ctx, event_state

    trig, conf, filt = parse(combo)
    names = name_map(P)
    keys = [trig, *conf] + ([filt] if filt else [])
    X, _ = build_ctx(P, sd.symbol, M15)
    s = sd.sigs.copy()
    with timeframe(M15), scaled_params([names[k] for k in keys], f):
        for k in keys:
            sig = compute(names[k], X)[1]
            s[k] = sig
            if BY_NAME[names[k]].kind == "D":
                s[k + "_st"] = event_state(sig)
    return s


def robustness(cfg, P, top: pd.DataFrame, SEL, SD, folds) -> pd.DataFrame:
    """Train (trong mẫu), leave-one-coin-out, độ nhạy ±20% cho các dòng cần xét tiêu chí 5."""
    syms = cfg["symbols"]
    wf_dir = M15.data(P) / "wf"
    tr_lo, tr_hi = split_ms(cfg, "train")
    loco = {}
    for f in folds:
        Rf = pd.read_parquet(wf_dir / f"fold{f.no:02d}" / "R.parquet")
        for c in syms:
            t4 = top_from(Rf, exclude_symbol=c)
            loco[(f.no, c)] = set(zip(t4.combo, t4.htf.astype(bool)))
    rows = []
    for _, r in top.iterrows():
        x = {"combo": r.combo, "htf": r.htf}
        Ttr = pd.concat([backtest(SD[s], r.combo, r.htf, tr_lo, tr_hi) for s in syms], ignore_index=True)
        x["train_n_trades"], x["train_expectancy_net_pct"] = int(len(Ttr)), float(Ttr.net.mean() * 100) if len(Ttr) else np.nan
        for c in syms:
            parts = [backtest(SD[c], r.combo, r.htf, f.test_lo, f.test_hi) for f in folds if (r.combo, bool(r.htf)) in loco[(f.no, c)]]
            T = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
            x[f"loco_{c}_n_trades"] = int(len(T))
            x[f"loco_{c}_expectancy_pct"] = float(T.net.mean() * 100) if len(T) else np.nan
        sel_f = [f for f in folds if ((SEL.fold == f.no) & (SEL.combo == r.combo) & (SEL.htf == r.htf)).any()]
        for fct in (0.8, 1.2):
            parts = []
            for s in syms:
                sg = signals_scaled(P, SD[s], r.combo, fct)
                parts += [backtest(SD[s], r.combo, r.htf, f.test_lo, f.test_hi, sigs=sg) for f in sel_f]
            T = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
            x[f"sens_x{fct}_n_trades"] = int(len(T))
            x[f"sens_x{fct}_expectancy_pct"] = float(T.net.mean() * 100) if len(T) else np.nan
        base = r.expectancy_net_pct
        vals = [x[f"sens_x{v}_expectancy_pct"] for v in (0.8, 1.2)]
        x["sens_sign_flip"] = bool(any(not np.isfinite(v) or np.sign(v) != np.sign(base) for v in vals))
        rows.append(x)
        log.info("Độ bền %s (%s): train %.4f%%, ×0,8 %.4f%%, ×1,2 %.4f%%", r.combo, r.htf, x["train_expectancy_net_pct"], *vals)
    return pd.DataFrame(rows)


def top10_md(cfg, top: pd.DataFrame, S: dict, folds, path) -> None:
    f = lambda x, d=4: "" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{d}f}"
    pf = lambda x: "∞" if isinstance(x, float) and np.isposinf(x) else f(x, 2)
    ok = lambda b: "✓" if b is True or b is np.True_ else ("✗" if b is False or b is np.False_ else "")
    syms = cfg["symbols"]
    L = ["# Top 10 tổ hợp M15 — walk-forward ngoài mẫu (Bảng B)", "",
         f"Walk-forward lồng nhau: {len(folds)} fold, train mở rộng từ 2024-10-09 (≥ 6 tháng), kiểm tra từng tháng "
         f"{folds[0].label} → {folds[-1].label}, embargo 1 ngày. Trong mỗi fold: Bảng A đơn lẻ, chọn 10 D + 3 F, quét tổ hợp "
         "kích hoạt + xác nhận chỉ trên train; top ≤ 30 (≥ 30 tín hiệu/symbol, precision ≥ 1,2× ngẫu nhiên, xếp theo recall "
         "sóng nhanh) được backtest baseline trên tháng kiểm tra.",
         "Baseline: tín hiệu khi nến M15 đóng, vào ở open nến M15 sau; TP 1,2% / SL 0,8% [A] kiểm trên từng nến M1; giữ ≤ 8 giờ; "
         "phí taker 0,05%/chiều [A]; trượt 1 tick/chiều [A]; funding thật.", "",
         f"- Số lần thử track M15 (dùng cho DSR): **{S['n_trials_m15']:,}**; cộng M1: {S['n_trials_m1_m15']:,}",
         f"- PBO (CSCV 16 khối, mọi tổ hợp được đánh giá ngoài mẫu): **{f(S['pbo'].get('pbo'), 3)}**",
         f"- Tổ hợp được đánh giá ngoài mẫu: **{S['n_combos_evaluated']}**, tổng {S['n_trades_total']:,} lệnh; gộp: gross "
         f"{f(S['pooled_expectancy_gross_pct'])}%/lệnh, ròng **{f(S['pooled_expectancy_net_pct'])}%/lệnh**",
         f"- Đạt từng tiêu chí §6: " + " · ".join(f"{v}: {S['n_' + k]}" for k, v in CRIT.items()) +
         f" → **đạt cả 5: {S['n_pass_all']}**", "",
         "| # | Tổ hợp | HTF | Fold chọn | Lệnh | Win | Exp ròng %/lệnh | CI95 | Exp gộp % | PF | MaxDD % | Symbol dương | DSR | DSR (M1+M15) | 1 | 2 | 3 | 4 | 5 | Đạt |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(top.to_dict("records"), 1):
        L.append(f"| {i} | {r['indicators']} | {'có' if r['htf'] else 'không'} | {r['n_folds_selected']} | {r['n_trades']} | {f(r['win_rate'], 3)} | "
                 f"{f(r['expectancy_net_pct'])} | [{f(r['expectancy_ci95_low_pct'])}, {f(r['expectancy_ci95_high_pct'])}] | "
                 f"{f(r['expectancy_gross_pct'])} | {pf(r['profit_factor'])} | {f(r['max_drawdown_pct'], 2)} | {r['symbols_positive']}/5 | "
                 f"{f(r['dsr'], 3)} | {f(r['dsr_m1_m15'], 3)} | " + " | ".join(ok(r[k]) for k in CRIT) + f" | **{ok(r['pass_all'])}** |")
    L += ["", "## Theo symbol, chế độ biến động, train, leave-one-coin-out, độ nhạy ±20% (expectancy ròng %/lệnh)", "",
          "| # | " + " | ".join(syms) + " | Biến động thấp | vừa | cao | Train | " + " | ".join(f"LOCO {s[:3]}" for s in syms) + " | ×0,8 | ×1,2 |",
          "|---|" + "---|" * (len(syms) + 3 + 1 + len(syms) + 2)]
    for i, d in enumerate(top.to_dict("records"), 1):
        L.append(f"| {i} | " + " | ".join(f(d.get(f"exp_{s}")) for s in syms) + " | " +
                 " | ".join(f(d.get(f"exp_regime_{k}")) for k in ("thấp", "vừa", "cao")) + f" | {f(d.get('train_expectancy_net_pct'))} | " +
                 " | ".join(f(d.get(f"loco_{s}_expectancy_pct")) for s in syms) +
                 f" | {f(d.get('sens_x0.8_expectancy_pct'))} | {f(d.get('sens_x1.2_expectancy_pct'))} |")
    L += ["", "Tiêu chí §6 (chốt trước): " + " · ".join(f"{i}. {v}" for i, v in enumerate(CRIT.values(), 1)) + ".",
          "Ô trống: CI95 khi < 10 lệnh; theo symbol/chế độ khi không có lệnh; LOCO khi bỏ coin đó ra thì tổ hợp không lọt top ở fold nào; "
          "×0,8/×1,2 khi không có lệnh (tính là đổi dấu → không đạt tiêu chí 5).", "",
          "Ghi chú: [F] số đo trên dữ liệu thật trong train + validation; chưa chạm giai đoạn test. Kết quả backtest không phải lợi nhuận thực tế."]
    path.write_text("\n".join(L) + "\n")
