"""Giai đoạn 3 — đặc trưng causal trên nến 1 phút.

Quy tắc thời gian: đặc trưng tại nến t chỉ dùng dữ liệu có sẵn khi nến t ĐÓNG CỬA
(open_time_ms + 60 000 ms). Metrics chỉ được dùng từ `available_ms`, funding chỉ dùng sau
thời điểm thanh toán. Tín hiệu tại t → vào lệnh ở giá mở cửa nến t+1.
Mọi đặc trưng phải vượt qua test cắt cụt (tests/test_lookahead.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from kh.config import MS_PER_MIN, setup_logging, write_json
from kh.data.normalize import load
from kh.features.regime import regimes
from kh.waves.dc import run_dc, theta_series

log = setup_logging("features")

# Mô tả từng đặc trưng: nhóm, công thức, đơn vị, nguồn. Được xuất thành docs/feature_registry.md.
REGISTRY: dict[str, tuple[str, str, str, str]] = {}


def _reg(name, group, formula, unit, source="klines_1m"):
    REGISTRY[name] = (group, formula, unit, source)


def _wilder(x: pd.Series, n: int) -> pd.Series:
    return x.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()


def compute_features(k: pd.DataFrame, cfg: dict, metrics: pd.DataFrame | None = None,
                     funding: pd.DataFrame | None = None, btc_close: pd.Series | None = None) -> pd.DataFrame:
    """Trả về DataFrame cùng chỉ số với `k` (nến 1m đã sắp xếp)."""
    hl = cfg["waves"]["sigma_halflife_min"]
    o, h, l, c, v = k.open, k.high, k.low, k.close, k.volume
    lr = np.log(c).diff()
    reg = regimes(k, hl)
    sig = reg.sigma_1m
    F = {}

    def z(x, n):  # chuẩn hóa theo độ biến động kỳ vọng trong n phút
        return x / (sig * np.sqrt(n))

    # A. Giá
    for n in (5, 15, 30, 60, 240, 1440):
        F[f"ret_{n}_z"] = z(np.log(c / c.shift(n)), n)
        _reg(f"ret_{n}_z", "A_price", f"log(c_t/c_(t-{n})) / (σ·√{n})", "z")
    for n in (60, 240, 1440):
        hh, ll = h.rolling(n).max(), l.rolling(n).min()
        F[f"pos_range_{n}"] = (c - ll) / (hh - ll).replace(0, np.nan)
        _reg(f"pos_range_{n}", "A_price", f"(c−min low_{n})/(max high_{n}−min low_{n})", "0..1")
        if n >= 240:
            F[f"dist_high_{n}_z"] = z(np.log(c / hh), n)
            F[f"dist_low_{n}_z"] = z(np.log(c / ll), n)
            _reg(f"dist_high_{n}_z", "F_structure", f"log(c/max high_{n}) / (σ·√{n})", "z")
            _reg(f"dist_low_{n}_z", "F_structure", f"log(c/min low_{n}) / (σ·√{n})", "z")
    rng = (h - l).replace(0, np.nan)
    F["body_15"] = ((c - o) / rng).fillna(0).rolling(15).mean()
    F["uwick_15"] = ((h - np.maximum(o, c)) / rng).fillna(0).rolling(15).mean()
    F["lwick_15"] = ((np.minimum(o, c) - l) / rng).fillna(0).rolling(15).mean()
    _reg("body_15", "A_price", "TB 15 nến của (c−o)/(h−l)", "-1..1")
    _reg("uwick_15", "A_price", "TB 15 nến của râu trên/(h−l)", "0..1")
    _reg("lwick_15", "A_price", "TB 15 nến của râu dưới/(h−l)", "0..1")
    sgn = np.sign(lr).fillna(0)
    grp = (sgn != sgn.shift()).cumsum()
    F["streak"] = sgn * (sgn.groupby(grp).cumcount() + 1)
    _reg("streak", "A_price", "số nến liên tiếp cùng chiều (có dấu)", "nến")

    # B. Xu hướng
    ema = {n: c.ewm(span=n, adjust=False, min_periods=n).mean() for n in (20, 60, 240, 1440)}
    for n, e in ema.items():
        F[f"ema_dist_{n}_z"] = z(np.log(c / e), n)
        _reg(f"ema_dist_{n}_z", "B_trend", f"log(c/EMA{n}) / (σ·√{n})", "z")
    F["ema_slope_60_z"] = z(np.log(ema[60] / ema[60].shift(15)), 15)
    F["ema_cross_20_60_z"] = z(np.log(ema[20] / ema[60]), 60)
    _reg("ema_slope_60_z", "B_trend", "log(EMA60_t/EMA60_(t−15)) / (σ·√15)", "z")
    _reg("ema_cross_20_60_z", "B_trend", "log(EMA20/EMA60) / (σ·√60)", "z")
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    up, dn = h.diff(), -l.diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=k.index)
    ndm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=k.index)
    atr60 = _wilder(tr, 60)
    pdi, ndi = 100 * _wilder(pdm, 60) / atr60, 100 * _wilder(ndm, 60) / atr60
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan)
    F["adx_60"] = _wilder(dx, 60)
    F["di_diff_60"] = pdi - ndi
    _reg("adx_60", "B_trend", "ADX Wilder chu kỳ 60 nến", "0..100")
    _reg("di_diff_60", "B_trend", "+DI − −DI (60)", "điểm")

    # C. Động lượng
    for n in (14, 60):
        g, ls = _wilder(lr.clip(lower=0), n), _wilder((-lr).clip(lower=0), n)
        F[f"rsi_{n}"] = 100 - 100 / (1 + g / ls.replace(0, np.nan))
        _reg(f"rsi_{n}", "C_momentum", f"RSI Wilder {n} nến", "0..100")
    m1 = c.ewm(span=180, adjust=False).mean() - c.ewm(span=390, adjust=False).mean()
    F["macd_hist_z"] = (m1 - m1.ewm(span=135, adjust=False).mean()) / c / sig
    _reg("macd_hist_z", "C_momentum", "MACD(180,390,135) histogram / c / σ (≈MACD 12/26/9 khung 15m)", "z")

    # D. Biến động
    for n in (15, 60, 240):
        F[f"rv_{n}_rel"] = lr.rolling(n).std() / sig
        _reg(f"rv_{n}_rel", "D_volatility", f"std(log return 1m, {n}) / σ", "tỷ lệ")
    F["rv_ratio_60_1440"] = lr.rolling(60).std() / lr.rolling(1440).std()
    _reg("rv_ratio_60_1440", "D_volatility", "std60 / std1440 (co hẹp < 1, mở rộng > 1)", "tỷ lệ")
    F["atr_60_rel"] = atr60 / c / sig
    _reg("atr_60_rel", "D_volatility", "ATR Wilder 60 / c / σ", "tỷ lệ")
    F["range_60_z"] = z(np.log(h.rolling(60).max() / l.rolling(60).min()), 60)
    _reg("range_60_z", "D_volatility", "log(max high_60 / min low_60) / (σ·√60)", "z")
    F["jump_15"] = lr.abs().rolling(15).max() / sig
    _reg("jump_15", "D_volatility", "max |log return 1m| trong 15 nến / σ", "z")
    F["sigma_1m_bps"] = sig * 1e4
    F["vol_ratio_30d"] = reg.vol_ratio_30d
    _reg("sigma_1m_bps", "D_volatility", "σ_1m EWMA (halflife 1 ngày), dịch 1 nến", "bps")
    _reg("vol_ratio_30d", "D_volatility", "σ / trung vị σ 30 ngày trước", "tỷ lệ")

    # E. Khối lượng
    vbase = v.rolling(10080, min_periods=1440).sum() / v.rolling(10080, min_periods=1440).count()
    for n in (15, 60):
        F[f"rvol_{n}"] = v.rolling(n).mean() / vbase.replace(0, np.nan)
        _reg(f"rvol_{n}", "E_volume", f"TB volume {n} nến / TB volume 7 ngày", "tỷ lệ")
    F["vol_chg_15"] = np.log((v.rolling(15).sum() + 1) / (v.rolling(15).sum().shift(15) + 1))
    _reg("vol_chg_15", "E_volume", "log(volume 15 nến / 15 nến trước đó)", "log")
    tb = k.taker_buy_base_volume
    for n in (15, 60, 240):
        F[f"taker_imb_{n}"] = 2 * tb.rolling(n).sum() / v.rolling(n).sum().replace(0, np.nan) - 1
        _reg(f"taker_imb_{n}", "E_volume", f"2·taker_buy/volume − 1 trong {n} nến", "-1..1")
    F["pv_corr_60"] = lr.rolling(60).corr(np.log1p(v))
    _reg("pv_corr_60", "E_volume", "tương quan(log return, log(1+volume)) 60 nến", "-1..1")
    ts = k.quote_volume / k.trade_count.replace(0, np.nan)
    F["trade_size_rel"] = ts.rolling(60).mean() / ts.rolling(10080, min_periods=1440).mean()
    _reg("trade_size_rel", "E_volume", "TB quote/lệnh 60 nến / TB 7 ngày", "tỷ lệ")

    # F. Cấu trúc thị trường
    prior_hi = h.shift(1).rolling(240).max()
    prior_lo = l.shift(1).rolling(240).min()
    F["breakout_240"] = (c > prior_hi).astype(float)
    F["breakdown_240"] = (c < prior_lo).astype(float)
    F["false_breakout_15"] = ((F["breakout_240"].rolling(15).max() == 1) & (c < prior_hi)).astype(float)
    F["false_breakdown_15"] = ((F["breakdown_240"].rolling(15).max() == 1) & (c > prior_lo)).astype(float)
    _reg("breakout_240", "F_structure", "c > max high 240 nến TRƯỚC (không gồm nến hiện tại)", "0/1")
    _reg("breakdown_240", "F_structure", "c < min low 240 nến trước", "0/1")
    _reg("false_breakout_15", "F_structure", "có breakout trong 15 nến nhưng c đã quay lại dưới mức", "0/1")
    _reg("false_breakdown_15", "F_structure", "có breakdown trong 15 nến nhưng c đã quay lại trên mức", "0/1")

    # Trạng thái sóng DC (online)
    for scale in (cfg["waves"]["small_scale"], cfg["waves"]["primary_scale"]):
        dc = run_dc(k, theta_series(c, {"kind": "sigma", "value": scale}, hl))
        mode = pd.Series(dc["st_mode"].astype(float), index=k.index).replace(0, np.nan)
        th = pd.Series(dc["st_theta"], index=k.index)
        F[f"dc{scale}_mode"] = mode
        F[f"dc{scale}_overshoot"] = mode * np.log(c / dc["st_conf_px"]) / th
        F[f"dc{scale}_pullback"] = mode * np.log(c / dc["st_ext"]) / th
        idx = np.arange(len(k))
        F[f"dc{scale}_age"] = np.where(dc["st_conf_idx"] >= 0, idx - dc["st_conf_idx"], np.nan)
        _reg(f"dc{scale}_mode", "F_structure", f"hướng sóng DC thang σ×{scale} hiện tại (+1/−1)", "dấu")
        _reg(f"dc{scale}_overshoot", "F_structure", f"quãng đi từ lúc xác nhận sóng / θ (thang {scale})", "θ")
        _reg(f"dc{scale}_pullback", "F_structure", f"khoảng cách tới cực trị chạy của sóng / θ (thang {scale})", "θ")
        _reg(f"dc{scale}_age", "F_structure", f"số nến từ lần xác nhận sóng gần nhất (thang {scale})", "nến")

    # G. Dữ liệu hợp đồng futures
    bar_close = k.open_time_ms + MS_PER_MIN
    if metrics is not None and len(metrics):
        m = metrics.sort_values("available_ms")
        cols = ["sum_open_interest", "count_long_short_ratio", "sum_toptrader_long_short_ratio",
                "count_toptrader_long_short_ratio", "sum_taker_long_short_vol_ratio"]
        j = pd.merge_asof(pd.DataFrame({"t": bar_close.to_numpy()}), m[["available_ms"] + cols],
                          left_on="t", right_on="available_ms", direction="backward")
        oi = pd.Series(j.sum_open_interest.to_numpy(), index=k.index)
        stale = pd.Series((bar_close.to_numpy() - j.available_ms.to_numpy()) / MS_PER_MIN, index=k.index)
        for n in (60, 240, 1440):
            F[f"oi_chg_{n}"] = np.log(oi / oi.shift(n))
            _reg(f"oi_chg_{n}", "G_futures", f"log(OI_t / OI_(t−{n})), OI dùng từ create_time+5′", "log", "metrics")
        F["oi_price_60"] = F["ret_60_z"] * np.sign(F["oi_chg_60"])
        _reg("oi_price_60", "G_futures", "ret_60_z × sign(ΔOI 60) (H6)", "z", "metrics")
        for col, name in [("count_long_short_ratio", "ls_acct"), ("sum_toptrader_long_short_ratio", "top_ls_pos"),
                          ("count_toptrader_long_short_ratio", "top_ls_acct"),
                          ("sum_taker_long_short_vol_ratio", "taker_lsr_5m")]:
            x = np.log(pd.Series(j[col].to_numpy(), index=k.index).where(lambda s: s > 0))
            F[name] = x
            _reg(name, "G_futures", f"log({col}) gần nhất đã công bố", "log", "metrics")
        F["ls_acct_chg_60"] = F["ls_acct"] - F["ls_acct"].shift(60)
        _reg("ls_acct_chg_60", "G_futures", "thay đổi log long/short tài khoản trong 60′", "log", "metrics")
        F["metrics_staleness_min"] = stale
        _reg("metrics_staleness_min", "G_futures", "số phút kể từ metrics gần nhất khả dụng", "phút", "metrics")
    if funding is not None and len(funding):
        f = funding.sort_values("funding_time_ms")
        f = f.assign(funding_mean3=f.funding_rate.rolling(3, min_periods=1).mean())
        j = pd.merge_asof(pd.DataFrame({"t": bar_close.to_numpy()}), f[["funding_time_ms", "funding_rate", "funding_mean3"]],
                          left_on="t", right_on="funding_time_ms", direction="backward")
        F["funding_last_bps"] = pd.Series(j.funding_rate.to_numpy() * 1e4, index=k.index)
        F["funding_mean3_bps"] = pd.Series(j.funding_mean3.to_numpy() * 1e4, index=k.index)
        _reg("funding_last_bps", "G_futures", "funding đã thanh toán gần nhất", "bps", "fundingRate")
        _reg("funding_mean3_bps", "G_futures", "TB 3 lần funding gần nhất", "bps", "fundingRate")
    mod = (bar_close // MS_PER_MIN) % (8 * 60)
    F["min_to_funding"] = (8 * 60 - mod) % (8 * 60)
    _reg("min_to_funding", "G_futures", "số phút tới mốc funding kế tiếp (lịch 8h: 0/8/16 UTC)", "phút", "lịch")

    # Lịch & liên thị trường
    hour = (k.open_time_ms // 3_600_000) % 24
    F["hour_sin"], F["hour_cos"] = np.sin(2 * np.pi * hour / 24), np.cos(2 * np.pi * hour / 24)
    F["dow"] = ((k.open_time_ms // 86_400_000) + 3) % 7  # 0 = thứ Hai
    _reg("hour_sin", "H_calendar", "sin(2π·giờ UTC/24)", "-1..1")
    _reg("hour_cos", "H_calendar", "cos(2π·giờ UTC/24)", "-1..1")
    _reg("dow", "H_calendar", "thứ trong tuần (0 = thứ Hai)", "0..6")
    if btc_close is not None:
        bret = np.log(btc_close / btc_close.shift(60))
        F["btc_ret_60_z"] = bret / (sig * np.sqrt(60))
        F["rel_ret_60_z"] = F["ret_60_z"] - F["btc_ret_60_z"]
        _reg("btc_ret_60_z", "I_cross", "return 60′ của BTCUSDT / (σ symbol·√60)", "z", "klines BTCUSDT")
        _reg("rel_ret_60_z", "I_cross", "ret_60_z − btc_ret_60_z", "z", "klines BTCUSDT")

    # Kiểm soát chất lượng
    F["filler_last_60"] = k.is_filler.astype(float).rolling(60, min_periods=1).sum()
    _reg("filler_last_60", "Z_quality", "số nến filler trong 60 nến gần nhất (dùng để loại mẫu)", "nến")
    out = pd.DataFrame(F, index=k.index).replace([np.inf, -np.inf], np.nan).astype("float32")
    return out


QUALITY_COLS = ["filler_last_60"]


def feature_names(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c in REGISTRY and REGISTRY[c][0] != "Z_quality"]


def sample_mask(k: pd.DataFrame, every: int) -> np.ndarray:
    """Mẫu tại nến có thời điểm đóng cửa là bội số của `every` phút."""
    return (((k.open_time_ms // MS_PER_MIN) + 1) % every == 0).to_numpy()


def build_all(cfg: dict, P) -> None:
    from kh.labels.triple_barrier import make_labels

    out = P.work / "features"
    out.mkdir(parents=True, exist_ok=True)
    btc = load(P.norm, "klines_1m", "BTCUSDT").set_index("open_time_ms").close
    stats = {}
    for s in cfg["symbols"]:
        k = load(P.norm, "klines_1m", s)
        met = load(P.norm, "metrics", s) if "metrics" in cfg["data"]["datasets"] else None
        fun = load(P.norm, "fundingRate", s) if "fundingRate" in cfg["data"]["datasets"] else None
        bc = pd.Series(btc.reindex(k.open_time_ms).to_numpy(), index=k.index)
        F = compute_features(k, cfg, met, fun, bc)
        L = make_labels(k, F, cfg)
        m = sample_mask(k, cfg["features"]["sample_every_min"])
        S = pd.concat([k.loc[m, ["open_time_ms"]], F[m], L[m]], axis=1)
        S.insert(0, "symbol", s)
        S.to_parquet(out / f"{s}.parquet", index=False)
        fn = feature_names(F)
        stats[s] = {"rows_1m": len(k), "samples": int(m.sum()), "n_features": len(fn),
                    "nan_share": F.loc[m, fn].isna().mean().round(4).to_dict(),
                    "inf_found": 0}
        log.info("%s: %d mẫu, %d đặc trưng", s, int(m.sum()), len(fn))
    write_json(stats, P.reports / "features" / "feature_stats.json")
    write_json({"features": fn, "registry": {k: list(v) for k, v in REGISTRY.items()}},
               P.work / "features" / "feature_list.json")
    _correlation_report(cfg, P)
    write_registry(P)


def write_registry(P) -> None:
    from kh.config import REPO_ROOT

    L = ["# Danh mục đặc trưng (feature registry)", "",
         "Tất cả đặc trưng tại nến t dùng dữ liệu có sẵn khi nến t đóng cửa. σ = σ_1m EWMA (halflife 1 ngày) dịch 1 nến.",
         "Metrics (OI, long/short) chỉ dùng từ create_time + 5 phút. Funding dùng giá trị đã thanh toán gần nhất.",
         "Đã kiểm tra bằng test cắt cụt (`tests/test_lookahead.py`).", "",
         "| Tên | Nhóm | Công thức | Đơn vị | Nguồn | Thời điểm khả dụng |", "|---|---|---|---|---|---|"]
    for name, (g, f, u, src) in REGISTRY.items():
        avail = "đóng cửa nến t" if src != "metrics" else "create_time + 5′ ≤ đóng cửa nến t"
        if src == "fundingRate":
            avail = "sau mốc thanh toán funding"
        L.append(f"| `{name}` | {g} | {f} | {u} | {src} | {avail} |")
    L += ["", "Đặc trưng bị loại để tránh trùng lặp: ROC (= ret_n), Stochastic %K (= pos_range_n), trend_z_1d (= ret_1440_z, tương quan 1,0)."]
    (REPO_ROOT / "docs" / "feature_registry.md").write_text("\n".join(L) + "\n")


def _correlation_report(cfg: dict, P) -> None:
    from kh.config import split_ms

    lo, hi = split_ms(cfg, "train")
    dfs = [pd.read_parquet(P.work / "features" / f"{s}.parquet") for s in cfg["symbols"]]
    D = pd.concat(dfs)
    D = D[(D.open_time_ms >= lo) & (D.open_time_ms < hi)]
    fn = feature_names(D)
    C = D[fn].sample(min(200_000, len(D)), random_state=0).corr(method="spearman")
    pairs = [(a, b, float(C.loc[a, b])) for i, a in enumerate(fn) for b in fn[i + 1:] if abs(C.loc[a, b]) > 0.9]
    write_json({"high_corr_pairs_gt_0.9": sorted(pairs, key=lambda x: -abs(x[2]))}, P.reports / "features" / "feature_correlation.json")
