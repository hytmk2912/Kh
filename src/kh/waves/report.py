"""Giai đoạn 2 — nghiên cứu cấu trúc sóng (mô tả), chỉ trên train + validation."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from kh.config import md_table, setup_logging, split_ms, to_dt, write_json
from kh.data.normalize import load
from kh.data.vision import data_version
from kh.features.regime import regimes
from kh.tracking.registry import log_experiment
from kh.waves.dc import run_dc, scale_specs, theta_series, waves_table

log = setup_logging("waves")


def research_slice(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Chỉ giữ dữ liệu trước final test (train + validation)."""
    _, val_end = split_ms(cfg, "val")
    return df[df.open_time_ms < val_end].reset_index(drop=True)


def block_bootstrap_mean(x: np.ndarray, day: np.ndarray, reps: int = 1000, seed: int = 0) -> tuple:
    """Khoảng tin cậy 90% và p một phía (H0: mean <= 0) bằng bootstrap theo khối ngày."""
    rng = np.random.default_rng(seed)
    days = np.unique(day)
    if len(days) < 5:
        return np.nan, np.nan, np.nan
    groups = {d: x[day == d] for d in days}
    sums = np.array([groups[d].sum() for d in days])
    cnts = np.array([len(groups[d]) for d in days])
    idx = rng.integers(0, len(days), (reps, len(days)))
    means = sums[idx].sum(1) / np.maximum(cnts[idx].sum(1), 1)
    centered = means - means.mean()
    p = float((centered >= x.mean()).mean())
    return float(np.quantile(means, 0.05)), float(np.quantile(means, 0.95)), p


def summarize(w: pd.DataFrame, cost_rt: float) -> dict:
    if w.empty:
        return {"n": 0}
    days = (w.end_ms.max() - w.start_ms.min()) / 86_400_000
    q = lambda s: {f"p{int(p * 100)}": float(np.nanquantile(s, p)) for p in (0.1, 0.25, 0.5, 0.75, 0.9)}
    net = w.dc_follow_logret - cost_rt
    day = (w.start_confirm_ms // 86_400_000).to_numpy()
    lo, hi, p = block_bootstrap_mean(w.dc_follow_logret.to_numpy(), day)
    return {
        "n": int(len(w)), "per_day": float(len(w) / max(days, 1e-9)),
        "amp_pct_abs": q(w.amp_pct.abs() * 100), "duration_min": q(w.duration_min),
        "speed_pct_per_hour": q(w.speed_pct_per_hour), "max_retracement_frac": q(w.max_retracement_frac),
        "overshoot_over_theta_mean": float(w.overshoot_over_theta.mean()),
        "overshoot_over_theta_median": float(w.overshoot_over_theta.median()),
        "start_detect_lag_min_median": float(w.start_detect_lag_min.median()),
        "n_counter_moves_median": float(w.n_counter_moves.median()) if "n_counter_moves" in w else None,
        "rel_volume_median": float(w.rel_volume.median()),
        "cost_to_amplitude_median": float(np.median(cost_rt / w.amp_log_abs)),
        "H1_dc_follow_mean_bps": float(w.dc_follow_logret.mean() * 1e4),
        "H1_dc_follow_ci90_bps": [lo * 1e4, hi * 1e4], "H1_p_one_sided": p,
        "H1_dc_follow_net_mean_bps": float(net.mean() * 1e4),
        "H1_win_rate_gross": float((w.dc_follow_logret > 0).mean()),
    }


def transitions(w: pd.DataFrame) -> dict:
    """Quan hệ giữa sóng hiện tại và sóng kế tiếp (luôn ngược hướng theo định nghĩa DC)."""
    a, b = w.amp_log_abs.to_numpy()[:-1], w.amp_log_abs.to_numpy()[1:]
    d1, d2 = w.duration_min.to_numpy()[:-1], w.duration_min.to_numpy()[1:]
    if len(a) < 30:
        return {}
    ta = pd.qcut(a, 3, labels=["small", "mid", "large"])
    tb = pd.qcut(b, 3, labels=["small", "mid", "large"])
    mat = pd.crosstab(ta, tb, normalize="index").round(3)
    ratio = b / a
    fib = {}
    for r0 in (0.382, 0.5, 0.618, 1.0, 1.618):
        fib[str(r0)] = float(((ratio > r0 * 0.95) & (ratio < r0 * 1.05)).mean())
    for r0 in (0.45, 0.56, 0.75, 1.3):  # mốc "không Fibonacci" để so sánh mật độ
        fib[f"ctrl_{r0}"] = float(((ratio > r0 * 0.95) & (ratio < r0 * 1.05)).mean())
    return {"spearman_amp_next": float(stats.spearmanr(a, b)[0]),
            "spearman_duration_next": float(stats.spearmanr(d1, d2)[0]),
            "amp_tercile_transition": mat.to_dict(),
            "next_over_current_amp_quantiles": {str(p): float(np.quantile(ratio, p)) for p in (0.1, 0.25, 0.5, 0.75, 0.9)},
            "share_ratio_within_5pct_of": fib}


def run_wave_study(cfg: dict, P) -> None:
    specs = scale_specs(cfg)
    hl = cfg["waves"]["sigma_halflife_min"]
    cost_rt = 2 * (cfg["costs"]["taker_fee"] + cfg["costs"]["slippage_bps"] / 1e4)
    out_dir = P.work / "waves"
    out_dir.mkdir(parents=True, exist_ok=True)
    tr_lo, tr_hi = split_ms(cfg, "train")
    results, regime_share, all_w = {}, {}, []
    for s in cfg["symbols"]:
        df = research_slice(load(P.norm, "klines_1m", s), cfg)
        reg = regimes(df, hl)
        regime_share[s] = {"trend": reg.trend_regime.value_counts(normalize=True).round(4).to_dict(),
                           "vol": reg.vol_regime.value_counts(normalize=True).round(4).to_dict()}
        small = run_dc(df, theta_series(df.close, {"kind": "sigma", "value": cfg["waves"]["small_scale"]}, hl))
        for sp in specs:
            dc = run_dc(df, theta_series(df.close, sp, hl))
            w = waves_table(df, dc, small)
            if w.empty:
                continue
            pos = np.searchsorted(df.open_time_ms.to_numpy(), w.start_ms.to_numpy())
            w["trend_regime"] = reg.trend_regime.to_numpy()[pos]
            w["vol_regime"] = reg.vol_regime.to_numpy()[pos]
            w["split"] = np.where(w.start_confirm_ms < tr_hi, "train", "val")
            w.insert(0, "scale", sp["name"])
            w.insert(0, "symbol", s)
            w.to_parquet(out_dir / f"{s}_{sp['name']}.parquet", index=False)
            all_w.append(w)
            key = f"{s}|{sp['name']}"
            results[key] = {"all": summarize(w, cost_rt), "transitions": transitions(w)}
            for d, g in w.groupby("direction"):
                results[key]["up" if d == 1 else "down"] = summarize(g, cost_rt)
            for sp_name, g in w.groupby("split"):
                results[key][f"split_{sp_name}"] = summarize(g, cost_rt)
            log.info("%s %s: %d sóng, biên độ trung vị %.2f%%, H1 %.1f bps", s, sp["name"], len(w),
                     results[key]["all"]["amp_pct_abs"]["p50"], results[key]["all"]["H1_dc_follow_mean_bps"])
    W = pd.concat(all_w, ignore_index=True)
    by_regime = {}
    for (sc, tr, vo), g in W.groupby(["scale", "trend_regime", "vol_regime"]):
        if len(g) >= 30:
            by_regime[f"{sc}|{tr}|{vo}"] = {"n": len(g), "amp_pct_abs_median": float(g.amp_pct.abs().median() * 100),
                                            "duration_median": float(g.duration_min.median()),
                                            "overshoot_over_theta_mean": float(g.overshoot_over_theta.mean()),
                                            "dc_follow_mean_bps": float(g.dc_follow_logret.mean() * 1e4)}
    pooled = {sc: {"all": summarize(g, cost_rt), **{f"split_{k}": summarize(gg, cost_rt) for k, gg in g.groupby("split")}}
              for sc, g in W.groupby("scale")}
    rep = {"per_symbol_scale": results, "pooled_by_scale": pooled, "by_regime": by_regime,
           "regime_time_share": regime_share, "cost_round_trip": cost_rt}
    write_json(rep, P.reports / "waves" / "wave_report.json")
    _markdown(rep, cfg, P.reports / "waves" / "wave_report.md")
    _charts(W, cfg, P)
    log_experiment(P.reports, "waves", cfg, data_version(P.raw), "train+val",
                   n_tests=len(specs) * (len(cfg["symbols"]) + 1),
                   summary={sc: {"n": v["all"]["n"], "H1_bps": v["all"]["H1_dc_follow_mean_bps"],
                                 "H1_p": v["all"]["H1_p_one_sided"]} for sc, v in pooled.items()},
                   artifacts=["waves/wave_report.md"])


def _markdown(rep: dict, cfg: dict, path) -> None:
    L = ["# Báo cáo cấu trúc sóng (Giai đoạn 2)", "",
         "Phạm vi: train + validation (2024-10-09 → 2026-05-15). Final test KHÔNG được dùng.",
         "Thang `sigK` = ngưỡng K × σ_1m × √60 (σ EWMA 1 ngày, dịch 1 nến); `pctX` = ngưỡng X% cố định.",
         "Đây là thống kê MÔ TẢ lịch sử; không tự động có giá trị dự báo.", "",
         "## Tổng hợp 5 coin theo thang", "",
         "| Thang | Số sóng | Sóng/ngày | Biên độ trung vị % | p90 % | Thời lượng trung vị (phút) | Hồi sâu nhất trung vị | Overshoot/θ TB | Trễ xác nhận (phút) | Phí/biên độ |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for sc, v in rep["pooled_by_scale"].items():
        a = v["all"]
        L.append(f"| {sc} | {a['n']:,} | {a['per_day']:.1f} | {a['amp_pct_abs']['p50']:.2f} | {a['amp_pct_abs']['p90']:.2f} | "
                 f"{a['duration_min']['p50']:.0f} | {a['max_retracement_frac']['p50']:.2f} | "
                 f"{a['overshoot_over_theta_mean']:.2f} | {a['start_detect_lag_min_median']:.0f} | {a['cost_to_amplitude_median']:.2f} |")
    L += ["", "## H1 — theo sóng DC (vào ở nến sau xác nhận, thoát ở nến sau xác nhận ngược)", "",
          "| Thang | Tập | Số lệnh | TB gộp (bps) | CI 90% (bps) | p một phía | TB ròng sau phí (bps) | Tỷ lệ thắng gộp |",
          "|---|---|---|---|---|---|---|---|"]
    for sc, v in rep["pooled_by_scale"].items():
        for sp in ("split_train", "split_val"):
            if sp in v:
                a = v[sp]
                L.append(f"| {sc} | {sp[6:]} | {a['n']:,} | {a['H1_dc_follow_mean_bps']:.1f} | "
                         f"[{a['H1_dc_follow_ci90_bps'][0]:.1f}, {a['H1_dc_follow_ci90_bps'][1]:.1f}] | {a['H1_p_one_sided']:.3f} | "
                         f"{a['H1_dc_follow_net_mean_bps']:.1f} | {a['H1_win_rate_gross']:.3f} |")
    L += ["", "## Theo coin (thang chính sig4)", "",
          "| Symbol | Sóng | Biên độ trung vị % | Thời lượng trung vị | Overshoot/θ | ρ(biên độ, biên độ sau) | H1 gộp (bps) | H1 ròng (bps) |",
          "|---|---|---|---|---|---|---|---|"]
    for s in cfg["symbols"]:
        v = rep["per_symbol_scale"].get(f"{s}|sig{cfg['waves']['primary_scale']}")
        if v:
            a, t = v["all"], v["transitions"]
            L.append(f"| {s} | {a['n']:,} | {a['amp_pct_abs']['p50']:.2f} | {a['duration_min']['p50']:.0f} | "
                     f"{a['overshoot_over_theta_mean']:.2f} | {t.get('spearman_amp_next', float('nan')):.3f} | "
                     f"{a['H1_dc_follow_mean_bps']:.1f} | {a['H1_dc_follow_net_mean_bps']:.1f} |")
    L += ["", "## Chuyển tiếp biên độ (sig4, BTCUSDT): P(tercile sóng sau | tercile sóng hiện tại)", ""]
    t = rep["per_symbol_scale"].get(f"{cfg['symbols'][0]}|sig{cfg['waves']['primary_scale']}", {}).get("transitions", {})
    if t:
        m = pd.DataFrame(t["amp_tercile_transition"])
        L += ["Cột = tercile sóng hiện tại, dòng = tercile sóng kế tiếp. Nếu độc lập, mỗi ô ≈ 0,333.", "",
              md_table(m), "",
              "Tỷ lệ cặp sóng có (biên độ sau / biên độ trước) nằm trong ±5% quanh mốc:", "",
              ", ".join(f"{k}: {v:.3f}" for k, v in t["share_ratio_within_5pct_of"].items())]
    L += ["", "## Theo chế độ thị trường (gộp coin, chỉ nhóm ≥ 30 sóng)", "",
          "| Thang | Xu hướng | Biến động | Sóng | Biên độ TV % | Thời lượng TV | Overshoot/θ | H1 gộp (bps) |",
          "|---|---|---|---|---|---|---|---|"]
    for k, v in rep["by_regime"].items():
        sc, tr, vo = k.split("|")
        if sc != f"sig{cfg['waves']['primary_scale']}":
            continue
        L.append(f"| {sc} | {tr} | {vo} | {v['n']} | {v['amp_pct_abs_median']:.2f} | {v['duration_median']:.0f} | "
                 f"{v['overshoot_over_theta_mean']:.2f} | {v['dc_follow_mean_bps']:.1f} |")
    L += ["", "## Tỷ lệ thời gian theo chế độ", ""]
    for s, v in rep["regime_time_share"].items():
        L.append(f"- {s}: xu hướng {v['trend']}; biến động {v['vol']}")
    L += ["", "## Ghi chú phương pháp", "",
          "- Theo định nghĩa DC, sóng luôn luân phiên tăng/giảm nên “xác suất chuyển từ tăng sang giảm” luôn bằng 1;",
          "  câu hỏi có ý nghĩa là về **độ lớn** sóng kế tiếp (bảng chuyển tiếp tercile).",
          "- Với bước ngẫu nhiên không trôi, overshoot/θ kỳ vọng ≈ 1 và H1 kỳ vọng ≈ 0; độ lệch khỏi mốc này mới là thông tin.",
          "- Đỉnh/đáy (extreme) là nhãn hồi cứu; mọi con số H1 dùng thời điểm xác nhận + giá mở cửa nến kế tiếp."]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n")


def _charts(W: pd.DataFrame, cfg: dict, P) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for sc, g in W[W.scale.str.startswith("sig")].groupby("scale"):
        axes[0].hist(np.log10(g.amp_pct.abs() * 100), bins=60, histtype="step", label=sc, density=True)
        axes[1].hist(np.log10(g.duration_min.clip(lower=1)), bins=60, histtype="step", label=sc, density=True)
        axes[2].hist(g.overshoot_over_theta.clip(-2, 6), bins=80, histtype="step", label=sc, density=True)
    axes[0].set_xlabel("log10 biên độ (%)")
    axes[1].set_xlabel("log10 thời lượng (phút)")
    axes[2].set_xlabel("overshoot / θ")
    axes[2].axvline(1, color="k", lw=0.8, ls="--")
    for a in axes:
        a.legend()
    fig.suptitle("Phân phối sóng (5 coin, train+val)")
    fig.tight_layout()
    out = P.reports / "waves"
    fig.savefig(out / "wave_distributions.png", dpi=110)
    plt.close(fig)
    # Ví dụ 3 ngày BTC với pivot thang chính
    s = cfg["symbols"][0]
    df = load(P.norm, "klines_1m", s)
    t0 = pd.Timestamp(cfg["splits"]["train"][0], tz="UTC") + pd.Timedelta(days=60)
    lo, hi = int(t0.value // 10**6), int((t0 + pd.Timedelta(days=3)).value // 10**6)
    d = df[(df.open_time_ms >= lo) & (df.open_time_ms < hi)]
    w = W[(W.symbol == s) & (W.scale == f"sig{cfg['waves']['primary_scale']}") & (W.start_ms >= lo) & (W.end_ms < hi)]
    fig, ax = plt.subplots(figsize=(15, 5))
    ax.plot(to_dt(d.open_time_ms), d.close, lw=0.6, color="gray")
    for _, r in w.iterrows():
        ax.plot(to_dt([r.start_ms, r.end_ms]), [r.start_price, r.end_price], color="green" if r.direction == 1 else "red")
        ax.axvline(to_dt(r.end_confirm_ms), color="orange", lw=0.4, alpha=0.6)
    ax.set_title(f"{s}: sóng thang sig{cfg['waves']['primary_scale']} (đường cam = thời điểm xác nhận online)")
    fig.tight_layout()
    fig.savefig(out / "wave_example_btc.png", dpi=110)
    plt.close(fig)
