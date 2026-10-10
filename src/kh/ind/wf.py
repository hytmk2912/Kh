"""Việc W1: walk-forward lồng nhau cho quy trình chọn tổ hợp (spec §6).

Mỗi fold: Bảng A đơn lẻ + chọn 20 ứng viên + quét tổ hợp CHỈ trên train của fold → top ≤ 50 → backtest baseline trên
tháng kiểm tra. Gộp lệnh ngoài mẫu các fold → Bảng B tổ hợp, DSR (tổng số lần thử), PBO (CSCV 16 khối), CI 95%
bootstrap khối 1 ngày, theo symbol, theo 3 chế độ biến động (tam phân vị ATR M1 từ train), leave-one-coin-out,
độ nhạy ±20% tham số. Không tinh chỉnh tham số (dùng mặc định) để không tăng số lần thử.
"""
from __future__ import annotations

import contextlib
import copy
import math
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
from scipy import stats

from kh.backtest.scalp import ScalpParams, metrics, run
from kh.config import setup_logging, split_ms, write_json
from kh.evaluation.metrics import pbo_cscv
from kh.evaluation.wf import DAY, monthly_folds
from kh.ind.candidates import select
from kh.ind.combos import aggregate, combo_signal, prep_parts, scan
from kh.ind.indicators import core as K
from kh.ind.indicators.registry import BY_NAME
from kh.ind.signals import signals_path
from kh.ind.single import table_a
from kh.ind.trials import count_trials, log_trials

log = setup_logging("ind.wf")
TOP_N = 50


# ------------------------------------------------------------------ chọn tổ hợp trên train của fold
def _table_a_one(args):
    cfg, P, s, lo, hi = args
    c = dict(cfg)
    c["symbols"] = [s]
    return table_a(c, P, lo, hi)


def fold_selection(cfg: dict, P, f) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with ProcessPoolExecutor(4) as ex:
        A = pd.concat(list(ex.map(_table_a_one, [(cfg, P, s, f.train_lo, f.train_hi) for s in cfg["symbols"]])), ignore_index=True)
    cand = select(cfg, P, lo_ms=f.train_lo, hi_ms=f.train_hi, A=A)
    R = scan(cfg, P, cand, f.train_lo, f.train_hi)
    return A, cand, R


def top_from(R: pd.DataFrame, n: int = TOP_N, exclude_symbol: str | None = None) -> pd.DataFrame:
    if exclude_symbol:
        R = R[R.symbol != exclude_symbol]
    Ag = aggregate(R)
    return Ag[Ag.precision_ok].sort_values(["recall_fast_up_down", "precision_long"], ascending=False).head(n)


# ------------------------------------------------------------------ backtest tổ hợp trên một khoảng
class SymbolData:
    def __init__(self, P, symbol):
        from kh.ind.data import load_funding, load_m1, load_ticks

        self.m1 = load_m1(P, symbol)
        self.t = self.m1.open_time_ms.to_numpy()
        self.sigs = pd.read_parquet(signals_path(P, symbol))
        self.fund = load_funding(P, symbol)
        self.tick = load_ticks(P)[symbol]
        atr = K.atr(*(self.m1[x].to_numpy(np.float64) for x in ("high", "low", "close")), 14) / self.m1.close.to_numpy()
        self.atr_rel = atr

    def idx(self, ms):
        return int(np.searchsorted(self.t, ms))


def backtest_combo(sd: SymbolData, cand: pd.DataFrame, combo: str, htf: bool, lo_ms: int, hi_ms: int,
                   prm: ScalpParams = ScalpParams(), sigs: pd.DataFrame | None = None) -> pd.DataFrame:
    sigs = sd.sigs if sigs is None else sigs
    keys = tuple(combo.split("+"))
    parts = prep_parts(sigs, cand[cand.key.isin(keys)], 0, len(sigs))
    sig = combo_signal(parts, keys, sigs.htf_long_ok.to_numpy() if htf else None, sigs.htf_short_ok.to_numpy() if htf else None)
    T = run(sd.m1, sig, sd.tick, prm, sd.idx(lo_ms), sd.idx(hi_ms), sd.fund)
    T["atr_rel"] = sd.atr_rel[np.maximum(T.entry_idx.to_numpy() - 1, 0)]
    return T


# ------------------------------------------------------------------ thống kê
def daily_series(T: pd.DataFrame, days: np.ndarray, n_symbols: int) -> pd.Series:
    """Lợi nhuận ngày của tổ hợp: tổng net (% notional) các lệnh đóng trong ngày / số symbol (mỗi symbol 1 phần vốn)."""
    if T.empty:
        return pd.Series(0.0, index=days)
    return (T.groupby(T.exit_ms // DAY).net.sum() / n_symbols).reindex(days, fill_value=0.0)


def bootstrap_ci(T: pd.DataFrame, reps: int = 1000, seed: int = 0) -> tuple[float, float]:
    if len(T) < 10:
        return np.nan, np.nan
    g = T.groupby(T.exit_ms // DAY).net.agg(["sum", "size"]).to_numpy()
    rng = np.random.default_rng(seed)
    s = g[rng.integers(0, len(g), (reps, len(g)))].sum(1)
    m = s[:, 0] / s[:, 1]
    return float(np.quantile(m, 0.025) * 100), float(np.quantile(m, 0.975) * 100)


def dsr(r: np.ndarray, sr_var: float, n_trials: int) -> dict:
    """Deflated Sharpe Ratio (Bailey & López de Prado 2014) với số lần thử N cho trước."""
    r = np.asarray(r, float)
    T = len(r)
    sd = r.std(ddof=1)
    sr = r.mean() / sd if sd > 0 else 0.0
    g = 0.5772156649
    N = max(int(n_trials), 2)
    sr0 = math.sqrt(max(sr_var, 0)) * ((1 - g) * stats.norm.ppf(1 - 1 / N) + g * stats.norm.ppf(1 - 1 / (N * math.e)))
    sk, ku = stats.skew(r), stats.kurtosis(r, fisher=False)
    den = math.sqrt(max(1 - sk * sr + (ku - 1) / 4 * sr ** 2, 1e-12))
    return {"sharpe_daily": float(sr), "sharpe_annual": float(sr * math.sqrt(365)), "sr0_daily": float(sr0),
            "dsr": float(stats.norm.cdf((sr - sr0) * math.sqrt(max(T - 1, 1)) / den)) if T > 2 else np.nan}


# ------------------------------------------------------------------ độ nhạy tham số ±20%
def _scale(v, f):
    if isinstance(v, bool) or isinstance(v, str):
        return v
    if isinstance(v, int):
        return max(1, int(round(v * f)))
    if isinstance(v, float):
        return v * f
    if isinstance(v, list):
        return [_scale(x, f) for x in v]
    return v


@contextlib.contextmanager
def scaled_params(names: list[str], f: float):
    old = {n: copy.deepcopy(BY_NAME[n].params) for n in names}
    try:
        for n in names:
            BY_NAME[n].params = {k: _scale(v, f) for k, v in BY_NAME[n].params.items()}
        yield
    finally:
        for n, p in old.items():
            BY_NAME[n].params = p


def signals_with_scale(sd: SymbolData, ref_close: np.ndarray, names: list[str], keys: list[str], f: float) -> pd.DataFrame:
    from kh.ind.indicators.impl import Ctx, compute

    s = sd.sigs.copy()
    X = Ctx.from_frame(sd.m1, ref_close)
    with scaled_params(names, f):
        for n, k in zip(names, keys):
            s[k] = compute(n, X)[1]
    return s


# ------------------------------------------------------------------ chạy W1
def run_w1(cfg: dict, P) -> None:
    out = P.reports / "ind"
    wf_dir = P.data / "ind" / "wf"
    wf_dir.mkdir(parents=True, exist_ok=True)
    (out / "wf").mkdir(parents=True, exist_ok=True)
    folds = monthly_folds(cfg["splits"]["train"][0], cfg["splits"]["val"][1], 6, cfg["splits"]["embargo_minutes"] // 1440)
    syms = cfg["symbols"]
    SD = {s: SymbolData(P, s) for s in syms}
    trades, sel_rows = [], []
    for f in folds:
        cache = wf_dir / f"fold{f.no:02d}"
        if (cache / "R.parquet").exists():
            R, cand = pd.read_parquet(cache / "R.parquet"), pd.read_csv(cache / "cand.csv")
            log.info("Fold %d (%s): dùng kết quả chọn đã lưu", f.no, f.label)
        else:
            cache.mkdir(exist_ok=True)
            A, cand, R = fold_selection(cfg, P, f)
            R.to_parquet(cache / "R.parquet", index=False)
            cand.to_csv(cache / "cand.csv", index=False)
            log_trials(P.reports, [
                {"stage": "W1-S1", "trial_id": f"W1-f{f.no:02d}-S1", "indicators": "99 chỉ báo đơn lẻ", "htf": "cả hai",
                 "params": "mặc định", "split": f"train fold {f.label}", "symbols": ",".join(syms), "note": "Bảng A đơn lẻ trong fold",
                 "n_trials": int(A.drop_duplicates(["indicator", "htf"]).shape[0])},
                {"stage": "W1-C2", "trial_id": f"W1-f{f.no:02d}-C2", "indicators": "tổ hợp 2–4 từ 20 ứng viên của fold", "htf": "cả hai",
                 "params": "mặc định", "split": f"train fold {f.label}", "symbols": ",".join(syms), "note": "quét tổ hợp trong fold",
                 "n_trials": int(R.drop_duplicates(["combo", "htf"]).shape[0])}])
        top = top_from(R)
        top.to_csv(out / "wf" / f"fold{f.no:02d}_{f.label}_top.csv", index=False)
        for _, r in top.iterrows():
            sel_rows.append({"fold": f.no, "month": f.label, "combo": r.combo, "htf": bool(r.htf)})
            for s in syms:
                T = backtest_combo(SD[s], cand, r.combo, bool(r.htf), f.test_lo, f.test_hi)
                T["fold"], T["month"], T["combo"], T["htf"], T["symbol"] = f.no, f.label, r.combo, bool(r.htf), s
                trades.append(T)
        log.info("Fold %d (%s): %d tổ hợp được chọn", f.no, f.label, len(top))
    TR = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()
    TR.to_parquet(P.data / "ind" / "wf_trades.parquet", index=False)
    SEL = pd.DataFrame(sel_rows)
    SEL.to_csv(out / "wf" / "selections.csv", index=False)
    table_b(cfg, P, folds, TR, SEL, SD)


def table_b(cfg, P, folds, TR, SEL, SD) -> None:
    out = P.reports / "ind"
    syms = cfg["symbols"]
    n_trials = count_trials(P.reports)
    days_all = np.arange(folds[0].test_lo // DAY, (folds[-1].test_hi - 1) // DAY + 1)
    # ngưỡng chế độ biến động: tam phân vị ATR/close trên train, từng symbol
    tr_lo, tr_hi = split_ms(cfg, "train")
    thr = {s: np.nanquantile(SD[s].atr_rel[SD[s].idx(tr_lo):SD[s].idx(tr_hi)], [1 / 3, 2 / 3]) for s in syms}
    if not TR.empty:
        TR["vol_regime"] = [("thấp", "vừa", "cao")[int(np.searchsorted(thr[s], a))] if np.isfinite(a) else "na"
                            for s, a in zip(TR.symbol, TR.atr_rel)]
    rows, daily = [], {}
    for (combo, htf), g in (TR.groupby(["combo", "htf"]) if not TR.empty else []):
        m = metrics(g)
        lo95, hi95 = bootstrap_ci(g)
        per_sym = {s: g[g.symbol == s].net.mean() * 100 if (g.symbol == s).any() else np.nan for s in syms}
        per_reg = {f"exp_regime_{k}": (g[g.vol_regime == k].net.mean() * 100 if (g.vol_regime == k).any() else np.nan)
                   for k in ("thấp", "vừa", "cao")}
        sel_days = np.concatenate([np.arange(f.test_lo // DAY, (f.test_hi - 1) // DAY + 1) for f in folds
                                   if ((SEL.fold == f.no) & (SEL.combo == combo) & (SEL.htf == htf)).any()])
        d = daily_series(g, sel_days, len(syms))
        daily[f"{combo}|{htf}"] = daily_series(g, days_all, len(syms))
        rows.append({"combo": combo, "htf": htf, "n_folds_selected": int(((SEL.combo == combo) & (SEL.htf == htf)).sum()),
                     "oos_days": len(sel_days), **m, "expectancy_ci95_low_pct": lo95, "expectancy_ci95_high_pct": hi95,
                     **{f"exp_{s}": v for s, v in per_sym.items()}, **per_reg,
                     "symbols_positive": int(sum(v > 0 for v in per_sym.values() if np.isfinite(v))),
                     "exp_worst_symbol": float(np.nanmin(list(per_sym.values()))) if per_sym else np.nan,
                     "_daily": d.to_numpy()})
    B = pd.DataFrame(rows)
    if B.empty:
        log.warning("Không có lệnh ngoài mẫu nào")
        return
    srs = [x.mean() / x.std(ddof=1) if x.std(ddof=1) > 0 else 0.0 for x in B._daily]
    sr_var = float(np.var(srs, ddof=1)) if len(srs) > 1 else 0.0
    D = pd.DataFrame([dsr(x, sr_var, n_trials) for x in B._daily])
    B = pd.concat([B.drop(columns="_daily"), D], axis=1)
    pbo = pbo_cscv(pd.DataFrame(daily), S=16) if len(daily) >= 2 else {"pbo": np.nan}
    B["pbo_all_combos"] = pbo.get("pbo")
    B["n_trials_total"] = n_trials
    B["kept"] = B.expectancy_net_pct > 0
    B = B.sort_values(["kept", "expectancy_net_pct", "profit_factor", "max_drawdown_pct", "symbols_positive"],
                      ascending=[False, False, False, True, False]).reset_index(drop=True)
    B.insert(0, "rank_b", np.where(B.kept, np.cumsum(B.kept), np.nan))
    names = name_map(P)
    B.insert(2, "indicators", B.combo.map(lambda c: " + ".join(names.get(k, k) for k in c.split("+"))))
    kept = B[B.kept]
    top = kept.head(10).copy()
    info = top.empty
    if info:  # không tổ hợp nào lãi: báo 10 tổ hợp expectancy cao nhất để tham khảo
        top = B.head(10).copy()
    top = robustness(cfg, P, top, TR, SEL, SD, folds)
    B = B.merge(top[["combo", "htf"] + [c for c in top.columns if c.startswith(("loco_", "sens_", "train_"))]], on=["combo", "htf"], how="left")
    B.to_csv(out / "combos_tableB.csv", index=False)
    write_json({"n_folds": len(folds), "n_trials_total": n_trials, "pbo": pbo, "n_combos_evaluated": int(len(B)),
                "n_kept_expectancy_positive": int(B.kept.sum()), "top10_is_informational": info},
               out / "wf" / "summary.json")
    top10_md(cfg, top, B, pbo, n_trials, folds, info, out / "top10.md")
    log.info("Bảng B: %d tổ hợp đánh giá ngoài mẫu, %d có expectancy > 0", len(B), int(B.kept.sum()))


def name_map(P) -> dict:
    from kh.ind.indicators.registry import CARDS

    return {f"i{i:03d}": c.name for i, c in enumerate(CARDS, 1)}


def robustness(cfg, P, top, TR, SEL, SD, folds) -> pd.DataFrame:
    """LOCO + độ nhạy ±20% + kết quả trên train cho các dòng top."""
    from kh.ind.signals import ref_symbol

    syms = cfg["symbols"]
    wf_dir = P.data / "ind" / "wf"
    names = name_map(P)
    tr_lo, tr_hi = split_ms(cfg, "train")
    rows = []
    for _, r in top.iterrows():
        keys = r.combo.split("+")
        cand_any = pd.read_csv(wf_dir / f"fold{int(SEL[(SEL.combo == r.combo) & (SEL.htf == r.htf)].fold.iloc[0]):02d}" / "cand.csv")
        extra = {}
        # train (trong mẫu, toàn bộ tập train)
        Ttr = pd.concat([backtest_combo(SD[s], cand_any, r.combo, r.htf, tr_lo, tr_hi) for s in syms], ignore_index=True)
        extra["train_expectancy_net_pct"] = float(Ttr.net.mean() * 100) if len(Ttr) else np.nan
        extra["train_n_trades"] = int(len(Ttr))
        # leave-one-coin-out: chọn bằng 4 coin trong từng fold, kiểm tra coin thứ 5
        for c in syms:
            parts = []
            for f in folds:
                R = pd.read_parquet(wf_dir / f"fold{f.no:02d}" / "R.parquet")
                t4 = top_from(R, exclude_symbol=c)
                if ((t4.combo == r.combo) & (t4.htf == r.htf)).any():
                    cand = pd.read_csv(wf_dir / f"fold{f.no:02d}" / "cand.csv")
                    parts.append(backtest_combo(SD[c], cand, r.combo, r.htf, f.test_lo, f.test_hi))
            T = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
            extra[f"loco_{c}_n_trades"] = int(len(T))
            extra[f"loco_{c}_expectancy_pct"] = float(T.net.mean() * 100) if len(T) else np.nan
        # độ nhạy ±20% tham số (tất cả chỉ báo trong tổ hợp), trên các tháng ngoài mẫu tổ hợp được chọn
        sel_f = [f for f in folds if ((SEL.fold == f.no) & (SEL.combo == r.combo) & (SEL.htf == r.htf)).any()]
        base = TR[(TR.combo == r.combo) & (TR.htf == r.htf)].net.mean() * 100
        for fct in (0.8, 1.2):
            parts = []
            for s in syms:
                ref = SD[ref_symbol(s)].m1.close.to_numpy() if ref_symbol(s) in SD else SD[s].m1.close.to_numpy()
                sig_s = signals_with_scale(SD[s], ref, [names[k] for k in keys], keys, fct)
                for f in sel_f:
                    cand = pd.read_csv(wf_dir / f"fold{f.no:02d}" / "cand.csv")
                    parts.append(backtest_combo(SD[s], cand, r.combo, r.htf, f.test_lo, f.test_hi, sigs=sig_s))
            T = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
            e = float(T.net.mean() * 100) if len(T) else np.nan
            extra[f"sens_x{fct}_expectancy_pct"] = e
            extra[f"sens_x{fct}_n_trades"] = int(len(T))
        extra["sens_sign_flip"] = bool(any(np.sign(extra[f"sens_x{x}_expectancy_pct"]) != np.sign(base)
                                           for x in (0.8, 1.2) if np.isfinite(extra[f"sens_x{x}_expectancy_pct"])))
        rows.append({**r.to_dict(), **extra})
        log.info("Độ bền %s (%s): train %.4f%%, ±20%% đổi dấu: %s", r.combo, r.htf, extra["train_expectancy_net_pct"], extra["sens_sign_flip"])
    return pd.DataFrame(rows)


def top10_md(cfg, top, B, pbo, n_trials, folds, info, path) -> None:
    f = lambda x, d=4: "" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{d}f}"
    pf = lambda x: "∞" if isinstance(x, float) and np.isposinf(x) else f(x, 2)
    syms = cfg["symbols"]
    L = ["# Top 10 tổ hợp — walk-forward ngoài mẫu (Bảng B)", "",
         f"Walk-forward lồng nhau: {len(folds)} fold, train mở rộng từ 2024-10-09 (≥ 6 tháng), kiểm tra từng tháng "
         f"{folds[0].label} → {folds[-1].label}, embargo 1 ngày. Trong mỗi fold: Bảng A đơn lẻ, 20 ứng viên, quét tổ hợp chỉ trên train; "
         "top ≤ 50 (precision ≥ 1,5× ngẫu nhiên, xếp theo recall sóng nhanh) được backtest baseline trên tháng kiểm tra.",
         "Baseline: TP 0,45% / SL 0,30% [A], giữ ≤ 15 phút, phí taker 0,05%/chiều [A], trượt 1 tick/chiều [A], funding thật.", "",
         f"- Số lần thử tổng (trials.csv, dùng cho DSR): **{n_trials:,}**",
         f"- PBO (CSCV 16 khối, mọi tổ hợp được đánh giá ngoài mẫu): **{f(pbo.get('pbo'), 3)}**",
         f"- Tổ hợp được đánh giá ngoài mẫu: **{len(B)}**; có expectancy ròng > 0: **{int(B.kept.sum())}**", ""]
    if info:
        L += ["**Không tổ hợp nào có expectancy ròng > 0 ngoài mẫu → Bảng B (sau khi loại) trống, không có Top 10.**",
              "Bảng dưới là 10 tổ hợp có expectancy cao nhất (đều ≤ 0), chỉ để tham khảo.", ""]
    L += ["| # | Tổ hợp | HTF | Fold chọn | Lệnh | Win | Exp ròng %/lệnh | CI95 | Exp gộp % | PF | MaxDD % | Symbol dương | Sharpe năm | DSR |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(top.itertuples(), 1):
        L.append(f"| {i} | {r.indicators} | {'có' if r.htf else 'không'} | {r.n_folds_selected} | {r.n_trades} | {f(r.win_rate, 3)} | "
                 f"{f(r.expectancy_net_pct)} | [{f(r.expectancy_ci95_low_pct)}, {f(r.expectancy_ci95_high_pct)}] | {f(r.expectancy_gross_pct)} | "
                 f"{pf(r.profit_factor)} | {f(r.max_drawdown_pct, 2)} | {r.symbols_positive}/5 | {f(r.sharpe_annual, 2)} | {f(r.dsr, 3)} |")
    L += ["", "## Theo symbol, chế độ biến động, train, leave-one-coin-out, độ nhạy ±20% (expectancy ròng %/lệnh)", "",
          "| # | " + " | ".join(syms) + " | Biến động thấp | vừa | cao | Train | " + " | ".join(f"LOCO {s[:3]}" for s in syms) + " | ×0,8 | ×1,2 | Đổi dấu |",
          "|---|" + "---|" * (len(syms) + 3 + 1 + len(syms) + 3)]
    for i, d in enumerate(top.to_dict("records"), 1):  # to_dict: tên cột có dấu chấm (sens_x0.8_…)
        L.append(f"| {i} | " + " | ".join(f(d.get(f"exp_{s}")) for s in syms) + " | " +
                 " | ".join(f(d.get(f"exp_regime_{k}")) for k in ("thấp", "vừa", "cao")) + f" | {f(d.get('train_expectancy_net_pct'))} | " +
                 " | ".join(f(d.get(f"loco_{s}_expectancy_pct")) for s in syms) +
                 f" | {f(d.get('sens_x0.8_expectancy_pct'))} | {f(d.get('sens_x1.2_expectancy_pct'))} | {d.get('sens_sign_flip')} |")
    L += ["", "Ô trống: CI95 khi < 10 lệnh (bootstrap khối ngày không có nghĩa); PF = ∞ khi không có lệnh lỗ; "
          "theo symbol/chế độ khi không có lệnh; LOCO khi bỏ coin đó ra thì tổ hợp không lọt top ở fold nào hoặc không có lệnh "
          "trên coin bị bỏ; ×0,8/×1,2 khi không có lệnh.", "", "## Vì sao các chỉ báo bổ trợ nhau", ""]
    role = {"A1": "xu hướng (MA)", "A2": "xu hướng/kênh", "A3": "động lượng", "A4": "biến động", "A5": "khối lượng", "A6": "giá/khác"}
    src = {"A1": "xu hướng", "A2": "xu hướng", "A3": "động lượng", "A4": "biến động", "A5": "khối lượng", "A6": "giá"}
    for i, r in enumerate(top.itertuples(), 1):
        cards = [BY_NAME[n.strip()] for n in r.indicators.split("+")]
        parts = [f"{c.name} ({role.get(c.group[:2], c.group)}, {'bộ lọc' if c.kind == 'F' else 'tín hiệu'})" for c in cards]
        srcs = sorted({src.get(c.group[:2], c.group) for c in cards})
        L.append(f"{i}. {' + '.join(parts)} — nguồn thông tin: {', '.join(srcs)}"
                 + (". Tín hiệu chỉ phát khi các nguồn khác nhau cùng đồng ý → ít lệnh, chọn lọc hơn." if len(srcs) > 1 else
                    ". Cùng một nguồn, ít bổ trợ.")
                 + f" [I] Đây là giả thuyết; bằng chứng ngoài mẫu: {r.n_trades} lệnh.")
    L += ["", "Ghi chú: [F] số đo trên dữ liệu thật trong train + validation; chưa chạm tập test khoá. Kết quả backtest không phải lợi nhuận thực tế."]
    path.write_text("\n".join(L) + "\n")
