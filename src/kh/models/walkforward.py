"""Giai đoạn 5–6 — mô hình dự báo + walk-forward có purge/embargo, chỉ trên train + validation.

Mục tiêu: y = 1 nếu nhãn triple-barrier = +1 (giá chạm rào trên trước / kết thúc cao hơn), 0 nếu −1.
Siêu tham số CỐ ĐỊNH (chọn trước, không tối ưu) để giảm bậc tự do và nguy cơ overfit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from kh.config import md_table, setup_logging, split_ms, write_json
from kh.data.vision import data_version
from kh.labels.triple_barrier import breakeven_prob
from kh.patterns.dataset import feature_list, load_samples, valid_mask
from kh.tracking.registry import log_experiment

log = setup_logging("models")
DAY = 86_400_000


def make_models(seed: int) -> dict:
    import lightgbm as lgb

    return {
        "logit": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                               LogisticRegression(C=0.05, max_iter=1000)),
        "lgbm": lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=500,
                                   subsample=0.7, subsample_freq=1, colsample_bytree=0.7, reg_lambda=10.0,
                                   random_state=seed, verbose=-1, n_jobs=4),
    }


def folds(cfg: dict) -> list[tuple[int, int]]:
    lo, _ = split_ms(cfg, "train")
    _, hi = split_ms(cfg, "val")
    first = lo + cfg["models"]["walk_forward_first_train_days"] * DAY
    step = cfg["models"]["walk_forward_test_days"] * DAY
    out, s = [], first
    while s < hi:
        out.append((s, min(s + step, hi)))
        s += step
    return out


def train_mask(D: pd.DataFrame, H: int, fold_start: int, emb_ms: int) -> pd.Series:
    """Purge + embargo: chỉ dùng mẫu có nhãn hoàn tất trước (đầu fold − embargo)."""
    return (D[f"label_end_ms_{H}"] <= fold_start - emb_ms) & D.split.isin(["train", "val"])


def metrics(y: np.ndarray, p: np.ndarray, p_base: np.ndarray) -> dict:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    ll, llb = log_loss(y, p, labels=[0, 1]), log_loss(y, np.clip(p_base, 1e-6, 1 - 1e-6), labels=[0, 1])
    return {"n": int(len(y)), "logloss": ll, "logloss_base": llb, "skill": 1 - ll / llb,
            "brier": brier_score_loss(y, p), "auc": roc_auc_score(y, p) if len(np.unique(y)) > 1 else np.nan,
            "base_rate": float(y.mean())}


def run_models(cfg: dict, P) -> None:
    out = P.reports / "models"
    out.mkdir(parents=True, exist_ok=True)
    (P.work / "models").mkdir(parents=True, exist_ok=True)
    D = load_samples(cfg, P)
    feats = feature_list(P)
    emb = cfg["splits"]["embargo_minutes"] * 60_000
    seed = cfg["models"]["seed"]
    F = folds(cfg)
    cost = 2 * (cfg["costs"]["taker_fee"] + cfg["costs"]["slippage_bps"] / 1e4)
    report = {"folds": [(str(pd.Timestamp(a, unit="ms")), str(pd.Timestamp(b, unit="ms"))) for a, b in F],
              "features": feats, "by_H": {}}
    for H in cfg["labels"]["horizons_min"]:
        ok = valid_mask(D, H) & D.split.isin(["train", "val"])
        S = D[ok].copy()
        S["y"] = (S[f"label_{H}"] == 1).astype(int)
        oof, fold_rows, importances = [], [], []
        for i, (fs, fe) in enumerate(F):
            trm = train_mask(S, H, fs, emb)
            tem = (S.open_time_ms >= fs) & (S.open_time_ms < fe)
            Xtr, ytr, Xte = S.loc[trm, feats], S.loc[trm, "y"].to_numpy(), S.loc[tem, feats]
            if len(Xte) == 0:
                continue
            pred = {"p_base": np.full(len(Xte), ytr.mean())}
            for name, m in make_models(seed).items():
                m.fit(Xtr, ytr)
                pred[f"p_{name}"] = m.predict_proba(Xte)[:, 1]
                if name == "lgbm":
                    imp = pd.Series(m.booster_.feature_importance("gain"), index=feats)
                    importances.append(imp / imp.sum())
            # Leave-one-coin-out cho LightGBM: mô hình không thấy coin được dự báo
            pred["p_lgbm_loco"] = np.full(len(Xte), np.nan)
            te_sym = S.loc[tem, "symbol"].to_numpy()
            for c in cfg["symbols"]:
                mtr = trm & (S.symbol != c)
                m = make_models(seed)["lgbm"].fit(S.loc[mtr, feats], S.loc[mtr, "y"])
                sel = te_sym == c
                if sel.any():
                    pred["p_lgbm_loco"][sel] = m.predict_proba(Xte[sel])[:, 1]
            fr = S.loc[tem, ["symbol", "open_time_ms", "split", "y", f"barrier_{H}", f"fwd_logret_{H}"]].copy()
            for k, v in pred.items():
                fr[k] = v
            fr["fold"] = i
            oof.append(fr)
            row = {"fold": i, "start": str(pd.Timestamp(fs, unit="ms").date()), "n_train": int(trm.sum())}
            for k in ("p_logit", "p_lgbm", "p_lgbm_loco"):
                row[k[2:]] = metrics(fr.y.to_numpy(), fr[k].to_numpy(), fr.p_base.to_numpy())
            fold_rows.append(row)
            log.info("H=%d fold %d (%s): skill logit %.4f lgbm %.4f loco %.4f, AUC lgbm %.3f", H, i, row["start"],
                     row["logit"]["skill"], row["lgbm"]["skill"], row["lgbm_loco"]["skill"], row["lgbm"]["auc"])
        O = pd.concat(oof, ignore_index=True)
        O.to_parquet(P.work / "models" / f"oof_H{H}.parquet", index=False)
        report["by_H"][H] = summarize_H(O, fold_rows, importances, cfg, H, cost)
    write_json(report, out / "models_report.json")
    _markdown(report, cfg, out / "models_report.md")
    log_experiment(P.reports, "models", cfg, data_version(P.raw), "walk-forward train+val",
                   n_tests=len(cfg["labels"]["horizons_min"]) * 3,
                   summary={H: {"H8_pass": v["H8"]["pass"], "lgbm_skill_mean": v["H8"]["mean_fold_skill"]}
                            for H, v in report["by_H"].items()}, artifacts=["models/models_report.md"])


def summarize_H(O: pd.DataFrame, fold_rows: list, importances: list, cfg: dict, H: int, cost: float) -> dict:
    from scipy import stats

    sk = np.array([r["lgbm"]["skill"] for r in fold_rows])
    t = sk.mean() / (sk.std(ddof=1) / np.sqrt(len(sk))) if len(sk) > 2 else np.nan
    per_coin = {}
    for c, g in O.groupby("symbol"):
        per_coin[c] = {k: metrics(g.y.to_numpy(), g[f"p_{k}"].to_numpy(), g.p_base.to_numpy())
                       for k in ("logit", "lgbm", "lgbm_loco")}
    coins_pos = sum(per_coin[c]["lgbm"]["skill"] > 0 for c in per_coin)
    pstar = breakeven_prob(float(O[f"barrier_{H}"].median()), cost)
    prec = []
    for tau in (0.52, 0.55, 0.58, 0.6, 0.65):
        for side, sel, hit in (("long", O.p_lgbm >= tau, O.y == 1), ("short", O.p_lgbm <= 1 - tau, O.y == 0)):
            n = int(sel.sum())
            prec.append({"tau": tau, "side": side, "n": n, "share": n / len(O),
                         "hit_rate": float(hit[sel].mean()) if n else np.nan, "breakeven": pstar})
    calib = O.assign(b=pd.qcut(O.p_lgbm, 10, labels=False, duplicates="drop")).groupby("b").agg(
        p_mean=("p_lgbm", "mean"), y_mean=("y", "mean"), n=("y", "size"))
    imp = pd.concat(importances, axis=1).mean(axis=1).sort_values(ascending=False)
    by_split = {sp: {k: metrics(g.y.to_numpy(), g[f"p_{k}"].to_numpy(), g.p_base.to_numpy()) for k in ("logit", "lgbm")}
                for sp, g in O.groupby("split")}
    return {"folds": fold_rows, "per_coin": per_coin, "by_split": by_split,
            "H8": {"mean_fold_skill": float(sk.mean()), "t": float(t),
                   "p_one_sided": float(stats.t.sf(t, len(sk) - 1)) if np.isfinite(t) else np.nan,
                   "coins_positive": int(coins_pos),
                   "pass": bool(np.isfinite(t) and stats.t.sf(t, len(sk) - 1) < 0.05 and coins_pos >= 3)},
            "precision": prec, "calibration": calib.round(4).to_dict("list"),
            "importance_top20": imp.head(20).round(4).to_dict(), "breakeven": pstar}


def _markdown(rep: dict, cfg: dict, path) -> None:
    L = ["# Báo cáo mô hình dự báo (Giai đoạn 5–6)", "",
         "Walk-forward mở rộng trên train + validation: huấn luyện ≥ 180 ngày đầu, mỗi fold kiểm tra 30 ngày,",
         "purge (nhãn phải hoàn tất trước fold) + embargo 1 ngày. Final test KHÔNG dùng.",
         "skill = 1 − logloss / logloss(tần suất cơ sở); > 0 nghĩa là tốt hơn dự báo ngây thơ.",
         "LOCO = leave-one-coin-out: mô hình huấn luyện trên 4 coin, dự báo coin thứ 5.", ""]
    for H, v in rep["by_H"].items():
        h8 = v["H8"]
        L += [f"## H = {H} phút", "",
              f"**H8**: skill TB theo fold = {h8['mean_fold_skill']:.5f}, t = {h8['t']:.2f}, p một phía = {h8['p_one_sided']:.4f}, "
              f"coin có skill > 0: {h8['coins_positive']}/5 → **{'Đạt' if h8['pass'] else 'Không đạt'}**", "",
              "| Fold | Bắt đầu | n train | Skill logit | Skill LGBM | Skill LOCO | AUC LGBM |", "|---|---|---|---|---|---|---|"]
        for r in v["folds"]:
            L.append(f"| {r['fold']} | {r['start']} | {r['n_train']:,} | {r['logit']['skill']:.4f} | {r['lgbm']['skill']:.4f} | "
                     f"{r['lgbm_loco']['skill']:.4f} | {r['lgbm']['auc']:.4f} |")
        L += ["", "| Coin | Skill logit | Skill LGBM | Skill LOCO | AUC LGBM | Brier LGBM |", "|---|---|---|---|---|---|"]
        for c, m in v["per_coin"].items():
            L.append(f"| {c} | {m['logit']['skill']:.4f} | {m['lgbm']['skill']:.4f} | {m['lgbm_loco']['skill']:.4f} | "
                     f"{m['lgbm']['auc']:.4f} | {m['lgbm']['brier']:.4f} |")
        L += ["", f"Độ chính xác tín hiệu LGBM (ngưỡng hòa vốn {v['breakeven']:.3f}):", "",
              "| τ | Phía | Số tín hiệu | Tỷ lệ mẫu | Tỷ lệ đúng |", "|---|---|---|---|---|"]
        for r in v["precision"]:
            L.append(f"| {r['tau']} | {r['side']} | {r['n']:,} | {r['share']:.4f} | {r['hit_rate']:.4f} |")
        cal = pd.DataFrame(v["calibration"])
        L += ["", "Hiệu chỉnh (calibration) — decile xác suất dự báo:", "", md_table(cal.round(4)), "",
              "Top 10 đặc trưng theo gain: " + ", ".join(f"`{k}` {x:.3f}" for k, x in list(v["importance_top20"].items())[:10]), ""]
    path.write_text("\n".join(L) + "\n")
