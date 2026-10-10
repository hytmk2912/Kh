"""Giai đoạn 4 — khai phá quy luật: giả thuyết định trước H2–H7, quét exploratory có FDR,
tổ hợp hai đặc trưng, phân tích decile, theo coin và chế độ thị trường.

Chỉ dùng train (khám phá) và validation (xác nhận). Final test không được chạm tới.
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from kh.config import setup_logging, write_json
from kh.data.vision import data_version
from kh.labels.triple_barrier import breakeven_prob
from kh.patterns.dataset import feature_list, load_samples, valid_mask
from kh.patterns.stats import (bootstrap_diff_by_day, ecdf_transform, fdr_by, ic_daily_products, nw_tstat,
                               p_one_sided, p_two_sided)
from kh.tracking.registry import log_experiment

log = setup_logging("mining")


def ic_scan(D: pd.DataFrame, feats: list[str], cfg: dict) -> pd.DataFrame:
    """IC theo ngày cho mọi (đặc trưng × symbol/ALL × H × tập)."""
    lags = cfg["mining"]["nw_lags"]
    rows = []
    for H in cfg["labels"]["horizons_min"]:
        y = f"fwd_logret_{H}"
        ok = valid_mask(D, H)
        per_sym = {}
        for split in ("train", "val"):
            for s in cfg["symbols"]:
                sub = D[ok & (D.split == split) & (D.symbol == s)]
                per_sym[(split, s)] = ic_daily_products(sub, feats, y)
            per_sym[(split, "ALL")] = pd.concat([per_sym[(split, s)] for s in cfg["symbols"]]).groupby(level=0).mean()
        for f in feats:
            for s in cfg["symbols"] + ["ALL"]:
                r = {"feature": f, "symbol": s, "H": H}
                for split in ("train", "val"):
                    m, t, n = nw_tstat(per_sym[(split, s)][f], lags)
                    r[f"ic_{split}"], r[f"t_{split}"], r[f"days_{split}"] = m, t, n
                r["p_train"] = p_two_sided(r["t_train"])
                r["p_val_same_sign"] = p_one_sided(r["t_val"], r["ic_train"])
                if s == "ALL":
                    signs = [np.sign(per_sym[("val", c)][f].mean()) for c in cfg["symbols"]]
                    r["coins_same_sign_val"] = int(sum(x == np.sign(r["ic_train"]) for x in signs))
                rows.append(r)
    T = pd.DataFrame(rows)
    T["fdr_train"] = fdr_by(T.p_train.to_numpy(), cfg["mining"]["fdr_q"])
    T["val_confirm"] = (T.p_val_same_sign < cfg["mining"]["val_alpha"])
    return T


def deciles(D: pd.DataFrame, f: str, H: int, cfg: dict) -> pd.DataFrame:
    ok = valid_mask(D, H) & D[f].notna()
    tr = D[ok & (D.split == "train")]
    edges = np.unique(np.nanquantile(tr[f], np.linspace(0, 1, 11)))
    out = []
    for split in ("train", "val"):
        sub = D[ok & (D.split == split)]
        b = np.clip(np.searchsorted(edges, sub[f], side="right") - 1, 0, len(edges) - 2)
        g = sub.groupby(b)
        out.append(pd.DataFrame({f"n_{split}": g.size(), f"up_rate_{split}": g[f"label_{H}"].apply(lambda s: (s == 1).mean()),
                                 f"fwd_bps_{split}": g[f"fwd_logret_{H}"].mean() * 1e4}))
    return pd.concat(out, axis=1)


def regime_ic(D: pd.DataFrame, f: str, H: int, cfg: dict) -> dict:
    ok = valid_mask(D, H) & D.split.isin(["train", "val"])
    out = {}
    for col in ("trend_regime", "vol_regime"):
        for val, sub in D[ok].groupby(col):
            ics = [ic_daily_products(sub[sub.symbol == s], [f], f"fwd_logret_{H}")[f] for s in cfg["symbols"]]
            m, t, n = nw_tstat(pd.concat(ics).groupby(level=0).mean(), cfg["mining"]["nw_lags"])
            out[f"{col}={val}"] = {"ic": m, "t": t, "days": n}
    return out


def preregistered(D: pd.DataFrame, cfg: dict, T: pd.DataFrame) -> dict:
    """Kiểm định H2–H7 đúng như đã đăng ký."""
    res = {}
    reps = cfg["mining"]["bootstrap_reps"]

    def ic_row(f, H):
        r = T[(T.feature == f) & (T.symbol == "ALL") & (T.H == H)].iloc[0]
        return {"ic_train": r.ic_train, "t_train": r.t_train, "ic_val": r.ic_val, "t_val": r.t_val,
                "coins_same_sign_val": r.coins_same_sign_val}

    for split in ("train", "val"):
        ok = valid_mask(D, 60) & (D.split == split)
        S = D[ok]
        up = (S.label_60 == 1).to_numpy().astype(float)
        dn = (S.label_60 == -1).to_numpy().astype(float)
        res.setdefault("H2_breakout", {})[split] = {
            "breakout_up_rate": bootstrap_diff_by_day(up, S.breakout_240.to_numpy() == 1, S.day.to_numpy(), reps),
            "breakdown_down_rate": bootstrap_diff_by_day(dn, S.breakdown_240.to_numpy() == 1, S.day.to_numpy(), reps)}
        q10 = D.loc[valid_mask(D, 60) & (D.split == "train"), "rv_ratio_60_1440"].quantile(0.1)
        absmove = (S.fwd_logret_60.abs() / S.barrier_60).to_numpy()
        res.setdefault("H3_squeeze", {})[split] = bootstrap_diff_by_day(
            absmove, (S.rv_ratio_60_1440 <= q10).to_numpy(), S.day.to_numpy(), reps)
        res["H3_squeeze"]["decile10_threshold"] = float(q10)
    res["H4_reversal_ret15"] = ic_row("ret_15_z", 60) | {"expected_sign": -1}
    res["H5_funding"] = ic_row("funding_last_bps", 240) | {"expected_sign": -1}
    res["H6_oi_price"] = ic_row("oi_price_60", 60) | {"expected_sign": +1}
    res["H7_taker_imb"] = ic_row("taker_imb_15", 60) | {"expected_sign": 0}
    for h, d in res.items():
        if h in ("H4_reversal_ret15", "H5_funding", "H6_oi_price", "H7_taker_imb"):
            s = d["expected_sign"]
            if s == 0:
                d["p_train"] = p_two_sided(d["t_train"])
                d["p_val"] = p_one_sided(d["t_val"], d["ic_train"])
                d["pass"] = bool(d["p_train"] < 0.05 and d["p_val"] < 0.05 and d["coins_same_sign_val"] >= 3)
            else:
                d["p_train"] = p_one_sided(d["t_train"], s)
                d["p_val"] = p_one_sided(d["t_val"], s)
                d["pass"] = bool(d["p_train"] < 0.05 and d["p_val"] < 0.05 and d["coins_same_sign_val"] >= 3)
    for h in ("H2_breakout",):
        a, b = res[h]["train"], res[h]["val"]
        res[h]["pass"] = bool(all(x["breakout_up_rate"]["p_one_sided"] < 0.05 for x in (a, b)) or
                              all(x["breakdown_down_rate"]["p_one_sided"] < 0.05 for x in (a, b)))
    res["H3_squeeze"]["pass"] = bool(res["H3_squeeze"]["train"]["p_one_sided"] < 0.05 and
                                     res["H3_squeeze"]["val"]["p_one_sided"] < 0.05)
    return res


def pair_scan(D: pd.DataFrame, top: list[str], cfg: dict) -> pd.DataFrame:
    rows = []
    for H in cfg["labels"]["horizons_min"]:
        ok = valid_mask(D, H)
        S = D[ok & D.split.isin(["train", "val"])].copy()
        # Biến đổi hạng theo phân phối TRAIN của từng coin (không dùng thông tin tương lai)
        pr = pd.DataFrame(index=S.index, columns=top, dtype=float)
        for sym, g in S.groupby("symbol"):
            tr = g[g.split == "train"]
            for c in top:
                pr.loc[g.index, c] = ecdf_transform(tr[c].to_numpy(float), g[c].to_numpy(float))
        names = []
        for a, b in itertools.combinations(top, 2):
            n = f"{a}*{b}"
            S[n] = pr[a] * pr[b]
            names.append(n)
        res = {}
        for split in ("train", "val"):
            per = [ic_daily_products(S[(S.split == split) & (S.symbol == s)], names, f"fwd_logret_{H}") for s in cfg["symbols"]]
            res[split] = pd.concat(per).groupby(level=0).mean()
        for n in names:
            r = {"pair": n, "H": H}
            for split in ("train", "val"):
                r[f"ic_{split}"], r[f"t_{split}"], r[f"days_{split}"] = nw_tstat(res[split][n], cfg["mining"]["nw_lags"])
            r["p_train"] = p_two_sided(r["t_train"])
            r["p_val_same_sign"] = p_one_sided(r["t_val"], r["ic_train"])
            rows.append(r)
    P = pd.DataFrame(rows)
    if len(P):
        P["fdr_train"] = fdr_by(P.p_train.to_numpy(), cfg["mining"]["fdr_q"])
        P["val_confirm"] = P.p_val_same_sign < cfg["mining"]["val_alpha"]
    return P


def status_of(row, dec: pd.DataFrame | None, pstar: float) -> str:
    if not row.fdr_train:
        return "Không đạt (không qua FDR trên train)"
    if not row.val_confirm:
        return "Không đạt (không xác nhận trên validation)"
    if row.get("coins_same_sign_val", 5) < 3:
        return "Đạt một phần (không nhất quán ≥ 3/5 coin)"
    if dec is not None:
        best = max(dec.up_rate_val.max(), 1 - dec.up_rate_val.min())
        if best < pstar:
            return f"Đạt một phần (decile tốt nhất {best:.3f} < ngưỡng hòa vốn {pstar:.3f})"
    return "Có tiềm năng nhưng chưa đủ bằng chứng (chờ backtest)"


def run_mining(cfg: dict, P) -> None:
    out = P.reports / "patterns"
    out.mkdir(parents=True, exist_ok=True)
    D = load_samples(cfg, P)
    feats = feature_list(P)
    log.info("Mẫu: %s; %d đặc trưng", D.split.value_counts().to_dict(), len(feats))
    T = ic_scan(D, feats, cfg)
    T.insert(0, "rule_id", [f"U{i:04d}" for i in range(len(T))])
    T.to_csv(out / "univariate_scan.csv", index=False)
    cost = 2 * (cfg["costs"]["taker_fee"] + cfg["costs"]["slippage_bps"] / 1e4)
    pstar = {H: breakeven_prob(float(D[f"barrier_{H}"].median()), cost) for H in cfg["labels"]["horizons_min"]}
    pre = preregistered(D, cfg, T)
    # Ứng viên: hàng ALL qua FDR train
    allrows = T[T.symbol == "ALL"].copy()
    cand = allrows[allrows.fdr_train].sort_values("t_train", key=np.abs, ascending=False)
    detail = {}
    for _, r in cand.iterrows():
        dec = deciles(D, r.feature, r.H, cfg)
        st = status_of(r, dec, pstar[r.H])
        detail[r.rule_id] = {"feature": r.feature, "H": int(r.H), "ic_train": r.ic_train, "t_train": r.t_train,
                             "ic_val": r.ic_val, "t_val": r.t_val, "coins_same_sign_val": r.coins_same_sign_val,
                             "status": st, "deciles": dec.round(4).reset_index().to_dict("records"),
                             "regimes": regime_ic(D, r.feature, r.H, cfg) if r.val_confirm else None}
    top = list(dict.fromkeys(cand.feature))[:10]
    if len(top) < 4:  # quá ít ứng viên: dùng top theo |t| train (exploratory)
        top = list(dict.fromkeys(allrows.sort_values("t_train", key=np.abs, ascending=False).feature))[:10]
    PS = pair_scan(D, top, cfg)
    PS.to_csv(out / "pair_scan.csv", index=False)
    n_tests = len(T) + len(PS) + 7
    summary = {"n_univariate_tests": len(T), "n_pair_tests": len(PS),
               "univariate_fdr_train_ALL": int(allrows.fdr_train.sum()),
               "univariate_fdr_and_val_ALL": int((allrows.fdr_train & allrows.val_confirm).sum()),
               "univariate_full_pass_ALL": int((allrows.fdr_train & allrows.val_confirm & (allrows.coins_same_sign_val >= 3)).sum()),
               "pairs_fdr_and_val": int((PS.fdr_train & PS.val_confirm).sum()) if len(PS) else 0,
               "breakeven_prob": pstar, "preregistered_pass": {k: v.get("pass") for k, v in pre.items()}}
    write_json({"summary": summary, "preregistered": pre, "candidates": detail}, out / "patterns_report.json")
    _markdown(cfg, T, PS, pre, detail, summary, out / "patterns_report.md")
    log_experiment(P.reports, "mine", cfg, data_version(P.raw), "train(discovery)+val(confirm)", n_tests, summary,
                   artifacts=["patterns/patterns_report.md", "patterns/univariate_scan.csv", "patterns/pair_scan.csv"])
    log.info("Tóm tắt: %s", summary)


def _markdown(cfg, T, PS, pre, detail, summary, path) -> None:
    f = lambda x: "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.4f}"
    L = ["# Báo cáo khai phá quy luật (Giai đoạn 4)", "",
         "Train = khám phá, validation = xác nhận. Final test không được dùng.",
         "IC = tương quan hạng Spearman GỘP (toàn tập, từng coin) giữa đặc trưng tại t và log return từ giá mở cửa t+1 tới t+H;",
         "t-stat Newey-West trên chuỗi đóng góp theo ngày (đơn vị quan sát hiệu dụng = ngày). Hàng ALL = trung bình 5 coin.",
         "Lưu ý: phiên bản đầu dùng IC trong từng ngày và bị thiên lệch (xem docs/hypotheses.md, nhật ký thay đổi).", "",
         "## Tóm tắt", "",
         f"- Số kiểm định đơn biến: **{summary['n_univariate_tests']}**; tổ hợp hai đặc trưng: **{summary['n_pair_tests']}**.",
         f"- Qua FDR (BY, q = {cfg['mining']['fdr_q']}) trên train (hàng ALL): **{summary['univariate_fdr_train_ALL']}**.",
         f"- Qua FDR + xác nhận validation: **{summary['univariate_fdr_and_val_ALL']}**; thêm ≥ 3/5 coin cùng dấu: **{summary['univariate_full_pass_ALL']}**.",
         f"- Tổ hợp qua FDR + validation: **{summary['pairs_fdr_and_val']}**.",
         f"- Xác suất thắng hòa vốn (TP=SL=rào trung vị, chi phí khứ hồi 14 bps): "
         + ", ".join(f"H={h}: **{p:.3f}**" for h, p in summary["breakeven_prob"].items()), "",
         "## Giả thuyết định trước", "",
         "| ID | Kết quả train | Kết quả validation | Đạt? |", "|---|---|---|---|"]
    h2 = pre["H2_breakout"]
    L.append(f"| H2 breakout → tỷ lệ lên | Δ={h2['train']['breakout_up_rate']['diff']:+.4f} (p={h2['train']['breakout_up_rate']['p_one_sided']:.3f}, n={h2['train']['breakout_up_rate']['n_event']}) | "
             f"Δ={h2['val']['breakout_up_rate']['diff']:+.4f} (p={h2['val']['breakout_up_rate']['p_one_sided']:.3f}) | {h2['pass']} |")
    L.append(f"| H2 breakdown → tỷ lệ xuống | Δ={h2['train']['breakdown_down_rate']['diff']:+.4f} (p={h2['train']['breakdown_down_rate']['p_one_sided']:.3f}) | "
             f"Δ={h2['val']['breakdown_down_rate']['diff']:+.4f} (p={h2['val']['breakdown_down_rate']['p_one_sided']:.3f}) | |")
    h3 = pre["H3_squeeze"]
    L.append(f"| H3 co hẹp → biên độ 60′/rào | Δ={h3['train']['diff']:+.4f} (p={h3['train']['p_one_sided']:.3f}) | "
             f"Δ={h3['val']['diff']:+.4f} (p={h3['val']['p_one_sided']:.3f}) | {h3['pass']} |")
    for k in ("H4_reversal_ret15", "H5_funding", "H6_oi_price", "H7_taker_imb"):
        d = pre[k]
        L.append(f"| {k} (dấu kỳ vọng {d['expected_sign']:+d}) | IC={f(d['ic_train'])}, t={d['t_train']:.2f}, p={d['p_train']:.3f} | "
                 f"IC={f(d['ic_val'])}, t={d['t_val']:.2f}, p={d['p_val']:.3f}, coin cùng dấu {d['coins_same_sign_val']}/5 | {d['pass']} |")
    L += ["", "H1 (theo sóng DC) được kiểm định ở Giai đoạn 2 — xem `reports/waves/wave_report.md`.", "",
          "## Ứng viên exploratory qua FDR trên train (hàng ALL)", "",
          "| Rule | Đặc trưng | H | IC train | t train | IC val | t val | Coin cùng dấu (val) | Trạng thái |",
          "|---|---|---|---|---|---|---|---|---|"]
    for rid, d in detail.items():
        L.append(f"| {rid} | `{d['feature']}` | {d['H']} | {f(d['ic_train'])} | {d['t_train']:.2f} | {f(d['ic_val'])} | "
                 f"{d['t_val']:.2f} | {d['coins_same_sign_val']}/5 | {d['status']} |")
    passed = {k: v for k, v in detail.items() if not v["status"].startswith("Không đạt")}
    for rid, d in list(passed.items())[:12]:
        L += ["", f"### {rid} — `{d['feature']}`, H = {d['H']}", "",
              "| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |",
              "|---|---|---|---|---|---|---|"]
        for x in d["deciles"]:
            L.append(f"| {x['index'] + 1} | {x.get('n_train', 0):.0f} | {x.get('up_rate_train', np.nan):.3f} | {x.get('fwd_bps_train', np.nan):.1f} | "
                     f"{x.get('n_val', 0):.0f} | {x.get('up_rate_val', np.nan):.3f} | {x.get('fwd_bps_val', np.nan):.1f} |")
        if d["regimes"]:
            L.append("")
            L.append("IC theo chế độ (train+val): " + "; ".join(f"{k}: {v['ic']:+.4f} (t={v['t']:.1f})" for k, v in d["regimes"].items()))
    if len(PS):
        L += ["", "## Tổ hợp hai đặc trưng (tương tác hạng theo phân phối train)", "",
              "| Cặp | H | IC train | t train | IC val | t val | FDR train | Xác nhận val |", "|---|---|---|---|---|---|---|---|"]
        for _, r in PS.sort_values("t_train", key=np.abs, ascending=False).head(20).iterrows():
            L.append(f"| `{r.pair}` | {r.H} | {f(r.ic_train)} | {r.t_train:.2f} | {f(r.ic_val)} | {r.t_val:.2f} | {r.fdr_train} | {r.val_confirm} |")
    L += ["", "## Top 25 theo |t| train (mọi hàng, kể cả từng coin)", "",
          "| Rule | Đặc trưng | Symbol | H | IC train | t train | IC val | t val | FDR | Val |", "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in T.sort_values("t_train", key=np.abs, ascending=False).head(25).iterrows():
        L.append(f"| {r.rule_id} | `{r.feature}` | {r.symbol} | {r.H} | {f(r.ic_train)} | {r.t_train:.2f} | {f(r.ic_val)} | {r.t_val:.2f} | {r.fdr_train} | {r.val_confirm} |")
    L += ["", "Ghi chú: IC có ý nghĩa thống kê chưa chắc có ý nghĩa kinh tế. Quy luật chỉ đáng giao dịch nếu decile cực trị",
          "vượt ngưỡng hòa vốn và vượt qua backtest có chi phí (Giai đoạn 7–8)."]
    path.write_text("\n".join(L) + "\n")
