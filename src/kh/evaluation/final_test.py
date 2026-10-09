"""Giai đoạn 6/9 — final test: chạy MỘT LẦN trên tập test đã khóa.

Điều kiện:
- `configs/locked_strategies.yaml` tồn tại và `locked: true` (đã commit trước khi chạy).
- Phải truyền `--confirm-final`.
- Nếu đã có `reports/final_test/FINAL_TEST_DONE.json` trong repo: lần chạy mới chỉ được coi là
  TÁI LẬP (reproduction) với cùng file khóa; không được dùng để sửa chiến lược.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import sys

import numpy as np
import pandas as pd
import yaml

from kh.backtest.engine import Costs
from kh.backtest.study import Market, attach_regime, buy_hold, random_baseline, run_variant
from kh.config import REPO_ROOT, git_hash, setup_logging, split_ms, write_json
from kh.data.vision import data_version
from kh.evaluation.metrics import bootstrap_expectancy, drop_top_winners, perf
from kh.models.walkforward import make_models, metrics
from kh.patterns.dataset import feature_list, load_samples, valid_mask
from kh.tracking.registry import log_experiment

log = setup_logging("final")
LOCK = REPO_ROOT / "configs" / "locked_strategies.yaml"


def final_status(res: dict, selected: bool) -> tuple[str, dict]:
    b, bs = res["base"], res["bootstrap"]
    coins_pos = sum(1 for v in res.get("by_coin", {}).values() if v["sum"] > 0)
    c = {"p_lt_0.05": (bs["p_one_sided"] or 1) < 0.05, "pf_gt_1.1": b.get("profit_factor", 0) > 1.1,
         "n_ge_100": b.get("n_trades", 0) >= 100, "coins_ge_3": coins_pos >= 3,
         "cost_x1.5_pos": res["cost_x1.5"].get("net_pnl", 0) > 0, "no_top5_pos": res["drop_top5pct"].get("net_pnl", 0) > 0}
    if not selected:
        return "Tham khảo (không được chọn trên validation)", c
    if b.get("net_pnl", 0) <= 0:
        return "Không đạt", c
    return ("Đạt kiểm định ngoài mẫu" if all(c.values()) else "Đạt một phần"), c


def test_predictions(D: pd.DataFrame, feats: list[str], H: int, cfg: dict, te_lo: int) -> tuple[pd.DataFrame, dict]:
    """Huấn luyện mô hình cuối trên toàn bộ train+val (purge trước test) rồi dự báo test."""
    ok = valid_mask(D, H)
    tr = D[ok & D.split.isin(["train", "val"]) & (D[f"label_end_ms_{H}"] <= te_lo)]
    te = D[(D.split == "test") & (D.filler_last_60 == 0)].copy()
    y = (tr[f"label_{H}"] == 1).astype(int)
    m = make_models(cfg["models"]["seed"])["lgbm"].fit(tr[feats], y)
    te["p_lgbm"] = m.predict_proba(te[feats])[:, 1]
    lab = te[valid_mask(te, H)]
    yt = (lab[f"label_{H}"] == 1).astype(int).to_numpy()
    pred = metrics(yt, lab.p_lgbm.to_numpy(), np.full(len(yt), y.mean())) if len(yt) else {}
    return te[["symbol", "open_time_ms", "p_lgbm", f"barrier_{H}"]], pred


def run_final_test(cfg: dict, P, confirm: bool = False, force: bool = False) -> None:
    marker_repo = REPO_ROOT / "reports" / "final_test" / "FINAL_TEST_DONE.json"
    marker = P.reports / "final_test" / "FINAL_TEST_DONE.json"
    if not LOCK.exists():
        log.error("Thiếu %s — chạy stage backtest và commit file khóa trước.", LOCK)
        sys.exit(2)
    lock_bytes = LOCK.read_bytes()
    lock = yaml.safe_load(lock_bytes)
    if not lock.get("locked"):
        log.error("File khóa chưa đặt locked: true")
        sys.exit(2)
    if not confirm:
        log.error("Final test chỉ chạy một lần. Thêm --confirm-final nếu thiết kế đã khóa và đã commit.")
        sys.exit(2)
    mode = "first_run"
    if marker.exists() and not force:
        log.error("Final test đã chạy (%s). Dùng --force chỉ để tái lập; kết quả không được dùng để sửa chiến lược.", marker)
        sys.exit(2)
    if marker_repo.exists():
        mode = "reproduction"
    lock_hash = hashlib.sha256(lock_bytes).hexdigest()[:12]
    log.info("Final test (%s), file khóa %s", mode, lock_hash)

    M = Market(cfg, P)
    D = load_samples(cfg, P)
    feats = feature_list(P)
    emb = cfg["splits"]["embargo_minutes"] * 60_000
    te_lo, te_hi = split_ms(cfg, "test")
    lo = te_lo + emb
    cap = cfg["backtest"]["initial_capital"]
    selected = {v["name"] for v in lock.get("selected", [])}
    variants = {v["name"]: v for v in lock.get("selected", []) + lock.get("informational_best_val_sharpe_per_family", [])}
    edges = {k: tuple(v) for k, v in lock["reversal_edges_from_train"].items()}
    preds, oof = {}, {}
    for H in sorted({v["H"] for v in variants.values() if v["family"] == "model"}):
        oof[H], preds[H] = test_predictions(D, feats, H, cfg, te_lo)
    base = Costs.from_cfg(cfg)
    results = {}
    for name, v in variants.items():
        T = attach_regime(run_variant(v, M, D, oof, edges, cfg, lo, te_hi, base), D, M)
        r = {"base": perf(T, lo, te_hi, cap), "bootstrap": bootstrap_expectancy(T),
             "cost_x1.5": perf(run_variant(v, M, D, oof, edges, cfg, lo, te_hi, Costs.from_cfg(cfg, 1.5, 1.5)), lo, te_hi, cap),
             "delay_1": perf(run_variant(v, M, D, oof, edges, cfg, lo, te_hi, base, 1), lo, te_hi, cap),
             "drop_top5pct": perf(drop_top_winners(T), lo, te_hi, cap),
             "random": random_baseline(v, T, M, cfg, lo, te_hi, base)}
        if not T.empty:
            r["by_coin"] = T.groupby("symbol").pnl.agg(["sum", "size"]).to_dict("index")
            r["by_trend_regime"] = T.groupby("trend_regime").pnl.agg(["sum", "size"]).to_dict("index")
        r["status"], r["checks"] = final_status(r, name in selected)
        results[name] = r
        log.info("%s: %s — ròng %.1f USD, %d lệnh", name, r["status"], r["base"].get("net_pnl", 0), r["base"]["n_trades"])
    bh = buy_hold(M, cfg, lo, te_hi, base)
    rep = {"mode": mode, "run_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "git": git_hash(), "lock_hash": lock_hash, "period": [str(pd.Timestamp(lo, unit="ms")), str(pd.Timestamp(te_hi, unit="ms"))],
           "selected": sorted(selected), "results": results, "model_predictive_test": preds,
           "buy_hold": {k: v for k, v in bh.items() if k != "daily"},
           "funding_note": "Funding sau mốc cuối cùng có dữ liệu được ước tính bằng mức funding cuối cùng đã biết."}
    write_json(rep, P.reports / "final_test" / "final_test_report.json")
    _markdown(rep, cfg, P.reports / "final_test" / "final_test_report.md")
    write_json({"done_at_utc": rep["run_at_utc"], "git": rep["git"], "lock_hash": lock_hash, "mode": mode},
               marker)
    log_experiment(P.reports, "final_test", cfg, data_version(P.raw), "test (một lần)", len(variants),
                   {n: r["status"] for n, r in results.items()}, artifacts=["final_test/final_test_report.md"])


def _markdown(rep, cfg, path) -> None:
    f = lambda x, d=2: "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{d}f}"
    L = ["# Báo cáo FINAL TEST", "",
         f"Chế độ: **{rep['mode']}** · chạy lúc {rep['run_at_utc']} · git {rep['git']} · file khóa {rep['lock_hash']}",
         f"Giai đoạn: {rep['period'][0][:10]} → {rep['period'][1][:10]} (sau embargo 1 ngày).",
         f"Chiến lược được chọn trên validation: **{', '.join(rep['selected']) or 'không có'}**.", "",
         "| Biến thể | Trạng thái | Lệnh | Ròng (USD) | Return | Sharpe | MaxDD | PF | Exp ròng (bps) | p bootstrap | Ngẫu nhiên %ile | Chi phí ×1,5 | Trễ 1 nến | Bỏ top 5% |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for n, r in rep["results"].items():
        b = r["base"]
        L.append(f"| {n} | {r['status']} | {b['n_trades']} | {f(b.get('net_pnl'), 0)} | {f(b['total_return'] * 100)}% | {f(b.get('sharpe'))} | "
                 f"{f(b['max_drawdown'] * 100)}% | {f(b.get('profit_factor'))} | {f(b.get('expectancy_bps'), 1)} | {f(r['bootstrap']['p_one_sided'], 3)} | "
                 f"{f(r['random'].get('pct_rank'))} | {f(r['cost_x1.5'].get('net_pnl'), 0)} | {f(r['delay_1'].get('net_pnl'), 0)} | {f(r['drop_top5pct'].get('net_pnl'), 0)} |")
    bh = rep["buy_hold"]
    L += ["", f"Baseline mua & giữ 5 coin: {bh['total_return'] * 100:.2f}% (MaxDD {bh['max_drawdown'] * 100:.2f}%, Sharpe {f(bh['sharpe'])}). Không giao dịch: 0%.", ""]
    for H, m in rep["model_predictive_test"].items():
        if m:
            L.append(f"- Mô hình LGBM H={H} trên test: skill {m['skill']:.4f}, AUC {m['auc']:.4f}, n {m['n']:,}.")
    L += ["", rep["funding_note"], "",
          "Kết quả backtest không phải lợi nhuận thực tế. Không có chiến lược nào được coi là chắc chắn hiệu quả."]
    path.write_text("\n".join(L) + "\n")
