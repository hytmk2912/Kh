"""Giai đoạn 7–8 — backtest mọi biến thể trên validation, baseline, độ bền, DSR/PBO và khóa lựa chọn.

Không dùng final test. Kết quả lựa chọn ghi vào configs/locked_strategies.yaml (khóa thiết kế).
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import yaml

from kh.backtest.engine import Costs, run_symbol
from kh.backtest.strategies import VARIANTS, dc_signals, model_signals, random_signals, reversal_signals
from kh.config import REPO_ROOT, git_hash, setup_logging, split_ms, write_json
from kh.data.normalize import load
from kh.data.vision import data_version
from kh.evaluation.metrics import (bootstrap_expectancy, daily_returns, deflated_sharpe, drop_top_winners, pbo_cscv,
                                   perf)
from kh.models.walkforward import folds
from kh.patterns.dataset import load_samples, valid_mask
from kh.tracking.registry import log_experiment

log = setup_logging("backtest")
DAY = 86_400_000


class Market:
    """Dữ liệu 1m + funding của mọi coin, nạp một lần."""

    def __init__(self, cfg: dict, P):
        self.k, self.f, self.bar = {}, {}, {}
        for s in cfg["symbols"]:
            k = load(P.norm, "klines_1m", s)
            self.k[s] = k
            self.f[s] = load(P.norm, "fundingRate", s) if "fundingRate" in cfg["data"]["datasets"] else None
            self.bar[s] = pd.Series(np.arange(len(k)), index=k.open_time_ms.to_numpy())


def reversal_edges(D: pd.DataFrame, cfg: dict) -> dict:
    tr = D[(D.split == "train") & valid_mask(D, 60)]
    return {f: (float(tr[f].quantile(0.1)), float(tr[f].quantile(0.9))) for f in ("ret_15_z", "taker_imb_15", "rsi_14")}


def signals_for(v: dict, s: str, M: Market, D: pd.DataFrame, oof: dict, edges: dict, cfg: dict,
                lo: int, hi: int) -> pd.DataFrame:
    """Tín hiệu của biến thể v cho coin s, chỉ trong [lo, hi) và lệnh phải kết thúc trước hi."""
    if v["family"] == "dc_follow":
        sg = dc_signals(M.k[s], v, cfg["waves"]["sigma_halflife_min"])
        t = M.k[s].open_time_ms.to_numpy()
        ok = (t[sg.bar_idx] >= lo) & (sg.exit_at >= 0) & (t[np.minimum(sg.exit_at, len(t) - 1)] < hi)
        return sg[ok]
    H = v["H"]
    if v["family"] == "model":
        O = oof[H]
        S = O[(O.symbol == s) & (O.open_time_ms >= lo) & (O.open_time_ms < hi - (H + 1) * 60_000)]
        return model_signals(S, M.bar[s], v)
    S = D[(D.symbol == s) & (D.open_time_ms >= lo) & (D.open_time_ms < hi - (H + 1) * 60_000)]
    return reversal_signals(S, M.bar[s], v, edges)


def run_variant(v, M, D, oof, edges, cfg, lo, hi, costs: Costs, delay: int = 0) -> pd.DataFrame:
    out = []
    for s in cfg["symbols"]:
        sg = signals_for(v, s, M, D, oof, edges, cfg, lo, hi)
        T = run_symbol(M.k[s], M.f[s], sg, costs, cfg, delay=delay)
        if len(T):
            T["symbol"] = s
            out.append(T)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def attach_regime(T: pd.DataFrame, D: pd.DataFrame, M: Market) -> pd.DataFrame:
    if T.empty:
        return T
    R = D[["symbol", "open_time_ms", "trend_regime", "vol_regime"]]
    T = T.copy()
    T["sig_ms"] = [M.k[s].open_time_ms.iloc[i] for s, i in zip(T.symbol, T.bar_idx)]
    T = T.merge(R, left_on=["symbol", "sig_ms"], right_on=["symbol", "open_time_ms"], how="left").drop(columns="open_time_ms")
    return T


def buy_hold(M: Market, cfg: dict, lo: int, hi: int, costs: Costs) -> dict:
    cap, n = cfg["backtest"]["initial_capital"], len(cfg["symbols"])
    daily = []
    for s in cfg["symbols"]:
        k = M.k[s]
        k = k[(k.open_time_ms >= lo) & (k.open_time_ms < hi)]
        c = k.groupby(k.open_time_ms // DAY).close.last()
        p0 = k.open.iloc[0]
        val = (c / p0 - 1) * cap / n
        f = M.f[s]
        fs = f[(f.funding_time_ms > lo) & (f.funding_time_ms <= hi)] if f is not None else None
        fsum = fs.groupby(fs.funding_time_ms // DAY).funding_rate.sum() if fs is not None else pd.Series(dtype=float)
        val = val - (fsum.reindex(c.index, fill_value=0).cumsum() * cap / n)
        daily.append(val.diff().fillna(val.iloc[0]) / cap)
    r = pd.concat(daily, axis=1).sum(axis=1)
    r.iloc[0] -= 2 * costs.taker_fee  # phí vào + ra, tổng notional = vốn
    eq = 1 + r.cumsum()
    return {"total_return": float(r.sum()), "max_drawdown": float((eq.cummax() - eq).max()),
            "sharpe": float(r.mean() / r.std() * np.sqrt(365)) if r.std() > 0 else np.nan, "daily": r}


def random_baseline(v, T, M, cfg, lo, hi, costs, reps=50, seed=0) -> dict:
    """Phân phối PnL ròng khi giữ nguyên số lệnh/quy tắc thoát nhưng chọn thời điểm & hướng ngẫu nhiên."""
    if T.empty:
        return {"pct_rank": np.nan}
    rng = np.random.default_rng(seed)
    nets = []
    for _ in range(reps):
        tot = 0.0
        for s, g in T.groupby("symbol"):
            t = M.k[s].open_time_ms.to_numpy()
            bars = np.flatnonzero((t >= lo) & (t < hi - 300 * 60_000) & (((t // 60_000) + 1) % 15 == 0))
            tmpl = g[["bar_idx", "side", "tp", "sl", "max_hold", "exit_at", "risk_frac"]].copy()
            if v["family"] == "dc_follow":  # giữ thời lượng giữ lệnh như mẫu
                dur = (g.exit_at - g.bar_idx).to_numpy()
                rs = random_signals(tmpl, bars, rng)
                rs["exit_at"] = np.minimum(rs.bar_idx.to_numpy() + rng.permutation(dur), len(t) - 1)
            else:
                rs = random_signals(tmpl, bars, rng)
            R = run_symbol(M.k[s], M.f[s], rs, costs, cfg)
            tot += R.pnl.sum() if len(R) else 0.0
        nets.append(tot)
    nets = np.array(nets)
    return {"random_net_mean": float(nets.mean()), "random_net_p5": float(np.quantile(nets, 0.05)),
            "random_net_p95": float(np.quantile(nets, 0.95)), "pct_rank": float((nets < T.pnl.sum()).mean())}


def evaluate_variant(v, M, D, oof, edges, cfg, lo, hi, with_random=True) -> tuple[dict, pd.DataFrame]:
    cap = cfg["backtest"]["initial_capital"]
    base = Costs.from_cfg(cfg)
    T = run_variant(v, M, D, oof, edges, cfg, lo, hi, base)
    T = attach_regime(T, D, M)
    res = {"base": perf(T, lo, hi, cap), "bootstrap": bootstrap_expectancy(T)}
    for name, c, d in (("cost_x1.5", Costs.from_cfg(cfg, 1.5, 1.5), 0), ("cost_x2", Costs.from_cfg(cfg, 2, 2), 0),
                       ("slip_x3", Costs.from_cfg(cfg, 1, 3), 0), ("delay_1", base, 1)):
        res[name] = perf(run_variant(v, M, D, oof, edges, cfg, lo, hi, c, d), lo, hi, cap)
    res["drop_top5pct"] = perf(drop_top_winners(T), lo, hi, cap)
    if not T.empty:
        res["by_coin"] = T.groupby("symbol").pnl.agg(["sum", "size"]).to_dict("index")
        res["by_trend_regime"] = T.groupby("trend_regime").pnl.agg(["sum", "size"]).to_dict("index")
        res["by_vol_regime"] = T.groupby("vol_regime").pnl.agg(["sum", "size"]).to_dict("index")
        res["by_month"] = T.groupby(pd.to_datetime(T.exit_ms, unit="ms").dt.strftime("%Y-%m")).pnl.sum().round(2).to_dict()
        res["top5pct_share_of_net"] = float(T.pnl.nlargest(int(np.ceil(len(T) * 0.05))).sum() / T.pnl.sum()) if T.pnl.sum() != 0 else np.nan
    if with_random:
        res["random"] = random_baseline(v, T, M, cfg, lo, hi, base)
    return res, T


def criteria(res: dict, dsr: float, pbo: float) -> dict:
    b, bs = res["base"], res["bootstrap"]
    c = {
        "1_expectancy_and_ci": b.get("net_pnl", 0) > 0 and (bs["ci90_bps"][0] or -1) > 0,
        "2_pf_and_n": b.get("profit_factor", 0) > 1.1 and b.get("n_trades", 0) >= 100,
        "3_cost_and_delay": res["cost_x1.5"].get("net_pnl", 0) > 0 and res["delay_1"].get("net_pnl", 0) > 0,
        "4_without_top5": res["drop_top5pct"].get("net_pnl", 0) > 0,
        "5_dsr_pbo": (dsr > 0.95) and (np.isnan(pbo) or pbo < 0.5),
    }
    c["selected"] = all(c.values())
    return c


def run_backtest_study(cfg: dict, P) -> None:
    out = P.reports / "backtest"
    out.mkdir(parents=True, exist_ok=True)
    M = Market(cfg, P)
    D = load_samples(cfg, P)
    oof = {H: pd.read_parquet(P.work / "models" / f"oof_H{H}.parquet") for H in cfg["labels"]["horizons_min"]}
    edges = reversal_edges(D, cfg)
    emb = cfg["splits"]["embargo_minutes"] * 60_000
    va_lo, va_hi = split_ms(cfg, "val")
    va_lo += emb
    tr_lo, tr_hi = split_ms(cfg, "train")
    research_lo = folds(cfg)[0][0]
    cap = cfg["backtest"]["initial_capital"]
    results, daily_val, daily_research, trades = {}, {}, {}, {}
    for v in VARIANTS:
        res, T = evaluate_variant(v, M, D, oof, edges, cfg, va_lo, va_hi)
        if v["family"] == "reversal":
            res["train_in_sample"] = perf(run_variant(v, M, D, oof, edges, cfg, tr_lo, tr_hi, Costs.from_cfg(cfg)),
                                          tr_lo, tr_hi, cap)
        results[v["name"]] = res
        trades[v["name"]] = T
        daily_val[v["name"]] = daily_returns(T, va_lo, va_hi, cap)
        Tr = run_variant(v, M, D, oof, edges, cfg, research_lo, va_hi, Costs.from_cfg(cfg))
        daily_research[v["name"]] = daily_returns(Tr, research_lo, va_hi, cap)
        b = res["base"]
        log.info("%-24s val: lệnh %5d, ròng %8.1f USD, exp %6.1f bps (gộp %6.1f), Sharpe %5.2f, PF %.2f",
                 v["name"], b["n_trades"], b.get("net_pnl", 0), b.get("expectancy_bps", np.nan),
                 b.get("gross_expectancy_bps", np.nan), b.get("sharpe", np.nan), b.get("profit_factor", np.nan))
    DV = pd.DataFrame(daily_val)
    sr_all = (DV.mean() / DV.std(ddof=1)).to_numpy()
    pbo = pbo_cscv(pd.DataFrame(daily_research))
    sel = {}
    for v in VARIANTS:
        d = deflated_sharpe(DV[v["name"]], sr_all)
        results[v["name"]]["dsr"] = d
        results[v["name"]]["criteria"] = criteria(results[v["name"]], d["dsr"], pbo["pbo"])
        sel[v["name"]] = results[v["name"]]["criteria"]["selected"]
    bh = buy_hold(M, cfg, va_lo, va_hi, Costs.from_cfg(cfg))
    baselines = {"no_trade": {"total_return": 0.0, "max_drawdown": 0.0}, "buy_hold_equal_weight": {k: v for k, v in bh.items() if k != "daily"}}
    informational = {}
    for fam in sorted({v["family"] for v in VARIANTS}):
        names = [v["name"] for v in VARIANTS if v["family"] == fam]
        best = max(names, key=lambda n: np.nan_to_num(results[n]["base"].get("sharpe", -9), nan=-9))
        informational[fam] = best
    locked = {"locked": True, "locked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "git": git_hash(), "config_hash": cfg["_hash"],
              "selection_rule": "docs/hypotheses.md — tiêu chí chọn chiến lược vào final test",
              "selected": [v for v in VARIANTS if sel[v["name"]]],
              "informational_best_val_sharpe_per_family": [v for v in VARIANTS if v["name"] in informational.values()],
              "reversal_edges_from_train": edges, "n_variants_tried": len(VARIANTS), "pbo_research": pbo}
    # Bản khóa ứng viên luôn ghi vào reports; configs/locked_strategies.yaml chỉ tạo nếu chưa có
    # (không bao giờ ghi đè một bản khóa đã commit — lần chạy lại trên Colab chỉ là tái lập).
    text = "# Sinh tự động bởi stage backtest. KHÔNG sửa tay sau khi đã chạy final test.\n" + \
        yaml.safe_dump(_plain(locked), allow_unicode=True, sort_keys=False)
    (out / "locked_strategies.yaml").write_text(text)
    lock_path = REPO_ROOT / "configs" / "locked_strategies.yaml"
    if not lock_path.exists():
        lock_path.write_text(text)
    else:
        log.warning("Đã có %s — giữ nguyên bản khóa cũ, bản mới ở %s", lock_path, out / "locked_strategies.yaml")
    rep = {"period_val": [str(pd.Timestamp(va_lo, unit="ms")), str(pd.Timestamp(va_hi, unit="ms"))],
           "variants": results, "pbo": pbo, "baselines": baselines, "selected": [n for n, s in sel.items() if s],
           "informational": informational}
    write_json(rep, out / "backtest_report.json")
    _markdown(rep, cfg, out / "backtest_report.md")
    _chart(DV, bh["daily"], out / "equity_val.png")
    log_experiment(P.reports, "backtest", cfg, data_version(P.raw), "validation", n_tests=len(VARIANTS),
                   summary={"selected": rep["selected"], "pbo": pbo.get("pbo"),
                            "best_val": {n: results[n]["base"].get("sharpe") for n in informational.values()}},
                   artifacts=["backtest/backtest_report.md", "configs/locked_strategies.yaml"])


def _plain(o):
    if isinstance(o, dict):
        return {str(k): _plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_plain(x) for x in o]
    if isinstance(o, (np.floating, float)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    return o


def _markdown(rep, cfg, path) -> None:
    f = lambda x, d=2: "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{d}f}"
    L = ["# Báo cáo backtest (Giai đoạn 7–8) — tập validation", "",
         f"Giai đoạn: {rep['period_val'][0][:10]} → {rep['period_val'][1][:10]}. Vốn giả định {cfg['backtest']['initial_capital']:,.0f} USD, "
         f"rủi ro {cfg['backtest']['risk_per_trade'] * 100:.1f}% vốn/lệnh, đòn bẩy tối đa {cfg['backtest']['max_leverage_per_position']}× trên phần vốn mỗi coin.",
         f"Phí taker {cfg['costs']['taker_fee'] * 100:.3f}%/chiều (giả định VIP0), slippage {cfg['costs']['slippage_bps']} bps/chiều, funding thực tế.",
         "Vào lệnh ở giá mở cửa nến sau tín hiệu; TP/SL cùng nến → SL trước; mỗi coin tối đa 1 vị thế.", "",
         f"Số biến thể đã thử: **{len(rep['variants'])}** (cố định trước). PBO (CSCV, giai đoạn walk-forward): **{f(rep['pbo'].get('pbo'), 3)}**.", "",
         "| Biến thể | Lệnh | Ròng (USD) | Return | Sharpe | MaxDD | PF | Win | Exp ròng (bps) | Exp gộp (bps) | CI90 exp (bps) | Phí | Funding | Ngẫu nhiên %ile | DSR | Chọn |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for n, r in rep["variants"].items():
        b = r["base"]
        ci = r["bootstrap"]["ci90_bps"]
        L.append(f"| {n} | {b['n_trades']} | {f(b.get('net_pnl'), 0)} | {f(b['total_return'] * 100, 2)}% | {f(b.get('sharpe'))} | "
                 f"{f(b['max_drawdown'] * 100, 2)}% | {f(b.get('profit_factor'))} | {f(b.get('win_rate'), 3)} | {f(b.get('expectancy_bps'), 1)} | "
                 f"{f(b.get('gross_expectancy_bps'), 1)} | [{f(ci[0], 1)}, {f(ci[1], 1)}] | {f(b.get('fees'), 0)} | {f(b.get('funding'), 0)} | "
                 f"{f(r.get('random', {}).get('pct_rank'), 2)} | {f(r['dsr']['dsr'], 3)} | {r['criteria']['selected']} |")
    bh = rep["baselines"]["buy_hold_equal_weight"]
    L += ["", f"Baseline: không giao dịch = 0%; mua & giữ 5 coin (1× vốn, có funding) = {bh['total_return'] * 100:.2f}% "
              f"(MaxDD {bh['max_drawdown'] * 100:.2f}%, Sharpe {f(bh['sharpe'])}).", "",
          "## Độ bền (PnL ròng USD)", "",
          "| Biến thể | Gốc | Chi phí ×1,5 | Chi phí ×2 | Slippage ×3 | Trễ 1 nến | Bỏ 5% lệnh lãi nhất | Train (trong mẫu) |",
          "|---|---|---|---|---|---|---|---|"]
    for n, r in rep["variants"].items():
        L.append(f"| {n} | {f(r['base'].get('net_pnl'), 0)} | {f(r['cost_x1.5'].get('net_pnl'), 0)} | {f(r['cost_x2'].get('net_pnl'), 0)} | "
                 f"{f(r['slip_x3'].get('net_pnl'), 0)} | {f(r['delay_1'].get('net_pnl'), 0)} | {f(r['drop_top5pct'].get('net_pnl'), 0)} | "
                 f"{f(r.get('train_in_sample', {}).get('net_pnl'), 0)} |")
    L += ["", "## Tiêu chí lựa chọn (docs/hypotheses.md)", "",
          "| Biến thể | 1. Exp & CI > 0 | 2. PF > 1,1 & ≥ 100 lệnh | 3. Chi phí ×1,5 & trễ | 4. Bỏ top 5% | 5. DSR & PBO | Chọn |",
          "|---|---|---|---|---|---|---|"]
    for n, r in rep["variants"].items():
        c = r["criteria"]
        L.append(f"| {n} | {c['1_expectancy_and_ci']} | {c['2_pf_and_n']} | {c['3_cost_and_delay']} | {c['4_without_top5']} | {c['5_dsr_pbo']} | {c['selected']} |")
    L += ["", f"**Chiến lược được chọn vào final test:** {', '.join(rep['selected']) or 'KHÔNG CÓ'}.",
          f"Biến thể tốt nhất mỗi họ trên validation (chạy final test chỉ để THAM KHẢO, không phải lựa chọn): "
          + ", ".join(f"{k}: {v}" for k, v in rep["informational"].items()), "",
          "## PnL theo coin trên validation (USD)", "", "| Biến thể | " + " | ".join(cfg["symbols"]) + " |",
          "|---|" + "---|" * len(cfg["symbols"])]
    for n, r in rep["variants"].items():
        bc = r.get("by_coin", {})
        L.append(f"| {n} | " + " | ".join(f(bc.get(s, {}).get("sum"), 0) for s in cfg["symbols"]) + " |")
    path.write_text("\n".join(L) + "\n")


def _chart(DV: pd.DataFrame, bh: pd.Series, path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(13, 5))
    idx = pd.to_datetime(DV.index * DAY, unit="ms")
    for c in DV.columns:
        ax.plot(idx, DV[c].cumsum() * 100, lw=0.9, label=c)
    ax.plot(pd.to_datetime(bh.index * DAY, unit="ms"), bh.cumsum() * 100, color="k", lw=1.5, ls="--", label="mua & giữ")
    ax.axhline(0, color="gray", lw=0.6)
    ax.set_ylabel("lợi nhuận cộng dồn (% vốn)")
    ax.set_title("Validation — đường vốn sau chi phí")
    ax.legend(fontsize=7, ncol=3)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
