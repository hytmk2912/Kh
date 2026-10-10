"""Kiểm tra chất lượng dữ liệu và báo cáo theo symbol."""
from __future__ import annotations

import io
import random
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from kh.config import MS_PER_MIN, setup_logging, to_dt, window_ms, write_json
from kh.data import normalize as N
from kh.data.vision import RemoteFile, http_get

log = setup_logging("data.quality")


def runs(mask: np.ndarray, t_ms: np.ndarray) -> list[dict]:
    """Gom các vị trí True liên tiếp (theo phút) thành từng đợt."""
    idx = np.flatnonzero(mask)
    if not len(idx):
        return []
    br = np.flatnonzero(np.diff(t_ms[idx]) != MS_PER_MIN) + 1
    out = []
    for g in np.split(idx, br):
        out.append({"start": str(to_dt(t_ms[g[0]])), "end": str(to_dt(t_ms[g[-1]])), "minutes": len(g)})
    return out


def check_klines(df: pd.DataFrame, cfg: dict) -> dict:
    lo, hi = window_ms(cfg)
    t = df.open_time_ms.to_numpy()
    expected = (hi - lo) // MS_PER_MIN
    d = np.diff(t)
    present = np.unique(t)
    grid = np.arange(lo, hi, MS_PER_MIN)
    missing = np.setdiff1d(grid, present)
    ohlc_bad = ((df.high < df[["open", "close"]].max(axis=1)) | (df.low > df[["open", "close"]].min(axis=1))
                | (df.high < df.low))
    r = np.log(df.close).diff().abs()
    thr = cfg["data"]["extreme_return_threshold"]
    zero_vol_nonflat = (df.volume == 0) & ~df.is_filler
    return {
        "rows": len(df), "expected_rows": int(expected),
        "first": str(to_dt(t[0])) if len(t) else None, "last": str(to_dt(t[-1])) if len(t) else None,
        "missing_minutes": int(len(missing)),
        "missing_runs": runs(np.isin(grid, missing), grid)[:50],
        "duplicate_timestamps": int(len(t) - len(present)),
        "non_monotonic_steps": int((d <= 0).sum()),
        "ohlc_violations": int(ohlc_bad.sum()),
        "negative_values": int((df[["open", "high", "low", "close", "volume"]] < 0).sum().sum()),
        "nan_values": int(df[["open", "high", "low", "close", "volume"]].isna().sum().sum()),
        "close_time_offset_ms_values": sorted((df.close_time_ms - df.open_time_ms).unique().tolist())[:5],
        "taker_buy_gt_volume": int((df.taker_buy_base_volume > df.volume * (1 + 1e-9)).sum()),
        "filler_minutes": int(df.is_filler.sum()),
        "filler_runs": runs(df.is_filler.to_numpy(), t),
        "zero_volume_not_flat": int(zero_vol_nonflat.sum()),
        f"abs_1m_return_gt_{thr}": int((r > thr).sum()),
        "max_abs_1m_return": float(r.max()),
    }


def check_metrics(df: pd.DataFrame, cfg: dict) -> dict:
    lo, hi = window_ms(cfg)
    grid = np.arange(lo, hi, 5 * MS_PER_MIN)
    t = df.create_time_ms.to_numpy()
    missing = np.setdiff1d(grid, t)
    vals = df.drop(columns=["create_time_ms", "available_ms", "symbol"])
    return {"rows": len(df), "expected_rows": len(grid), "missing_slots": int(len(missing)),
            "missing_sample": [str(to_dt(x)) for x in missing[:20]],
            "off_grid": int(len(np.setdiff1d(t, grid))), "duplicates": int(len(t) - len(np.unique(t))),
            "nan_by_column": vals.isna().sum().to_dict(),
            "non_positive_open_interest": int((df.sum_open_interest <= 0).sum())}


def check_funding(df: pd.DataFrame, cfg: dict) -> dict:
    d = np.diff(df.funding_time_ms.to_numpy()) / 3_600_000
    return {"rows": len(df), "first": str(to_dt(df.funding_time_ms.iloc[0])),
            "last": str(to_dt(df.funding_time_ms.iloc[-1])),
            "interval_hours_declared": df.funding_interval_hours.value_counts().to_dict(),
            "interval_hours_observed": pd.Series(d).round(3).value_counts().to_dict(),
            "rate_min": float(df.funding_rate.min()), "rate_max": float(df.funding_rate.max()),
            "abs_rate_gt_0.003": int((df.funding_rate.abs() > 0.003).sum())}


def crosscheck_daily(cfg: dict, klines: pd.DataFrame, symbol: str, n_days: int, seed: int = 0) -> dict:
    """Đối chiếu nến từ file tháng với file ngày độc lập của cùng ngày (thay cho REST bị chặn)."""
    rng = random.Random(f"{seed}-{symbol}")
    days = sorted(pd.to_datetime(klines.open_time_ms, unit="ms").dt.strftime("%Y-%m-%d").unique())
    picks = sorted(rng.sample(days[:-10], min(n_days, len(days) - 10)))
    out = []
    for d in picks:
        rf = RemoteFile("klines_1m", symbol, "daily", d)
        status, blob = http_get(f"{cfg['data']['vision_url']}/{rf.key}", cfg["data"]["timeout_s"],
                                cfg["data"]["retries"])
        if status != 200:
            out.append({"day": d, "status": f"http_{status}"})
            continue
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            raw = z.read(z.namelist()[0])
        hdr = not raw[:1].isdigit()
        dd = pd.read_csv(io.BytesIO(raw), header=0 if hdr else None)
        if not hdr:
            dd.columns = N.KLINE_COLS
        dd = dd.rename(columns=N.KLINE_RENAME)
        dd["open_time_ms"] = N._to_ms(dd["open_time_ms"])
        m = klines[klines.open_time_ms.isin(dd.open_time_ms)]
        j = m.merge(dd, on="open_time_ms", suffixes=("", "_d"))
        cols = ["open", "high", "low", "close", "volume"]
        diff = int(sum((~np.isclose(j[c], j[c + "_d"].astype(float))).sum() for c in cols))
        out.append({"day": d, "rows_daily": len(dd), "rows_matched": len(j), "value_mismatches": diff})
    return {"days": out, "all_match": all(x.get("value_mismatches", 1) == 0 and
                                          x.get("rows_matched") == x.get("rows_daily") for x in out)}


def quality_report(cfg: dict, norm_dir: Path, reports_dir: Path, crosscheck: bool = True) -> dict:
    rep = {}
    for s in cfg["symbols"]:
        k = N.load(norm_dir, "klines_1m", s)
        rep[s] = {"klines_1m": check_klines(k, cfg)}
        if "metrics" in cfg["data"]["datasets"]:
            rep[s]["metrics"] = check_metrics(N.load(norm_dir, "metrics", s), cfg)
        if "fundingRate" in cfg["data"]["datasets"]:
            rep[s]["fundingRate"] = check_funding(N.load(norm_dir, "fundingRate", s), cfg)
        if crosscheck:
            rep[s]["crosscheck_monthly_vs_daily"] = crosscheck_daily(
                cfg, k, s, cfg["data"]["crosscheck_days_per_symbol"])
        log.info("QA %s: %s", s, {kk: rep[s]["klines_1m"][kk] for kk in
                                   ["rows", "missing_minutes", "ohlc_violations", "filler_minutes"]})
    rep["_gates"] = gates(rep, cfg)
    write_json(rep, reports_dir / "data_quality" / "quality_report.json")
    write_markdown(rep, cfg, reports_dir / "data_quality" / "quality_report.md")
    return rep


def gates(rep: dict, cfg: dict) -> dict:
    """Tiêu chí chất lượng đã thống nhất. Không đạt thì không sang giai đoạn sau."""
    g = {}
    for s in cfg["symbols"]:
        k = rep[s]["klines_1m"]
        g[s] = {
            "no_duplicates": k["duplicate_timestamps"] == 0,
            "sorted": k["non_monotonic_steps"] == 0,
            "ohlc_valid": k["ohlc_violations"] == 0 and k["negative_values"] == 0 and k["nan_values"] == 0,
            "missing_le_0.1pct": k["missing_minutes"] <= 0.001 * k["expected_rows"],
            "filler_le_0.1pct": k["filler_minutes"] <= 0.001 * k["expected_rows"],
            "crosscheck_ok": rep[s].get("crosscheck_monthly_vs_daily", {}).get("all_match", True),
        }
        g[s]["pass"] = all(g[s].values())
    g["all_pass"] = all(g[s]["pass"] for s in cfg["symbols"])
    return g


def write_markdown(rep: dict, cfg: dict, path: Path) -> None:
    L = ["# Báo cáo chất lượng dữ liệu", "",
         f"Cửa sổ: {cfg['window']['start']} → {cfg['window']['end']} (UTC). "
         f"Tất cả tiêu chí đạt: **{rep['_gates']['all_pass']}**", "",
         "| Symbol | Nến | Kỳ vọng | Thiếu | Trùng | OHLC sai | Filler | |r1m|>10% | Đối chiếu ngày | Đạt |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for s in cfg["symbols"]:
        k = rep[s]["klines_1m"]
        thr = [v for kk, v in k.items() if kk.startswith("abs_1m_return_gt")][0]
        L.append(f"| {s} | {k['rows']:,} | {k['expected_rows']:,} | {k['missing_minutes']} | "
                 f"{k['duplicate_timestamps']} | {k['ohlc_violations']} | {k['filler_minutes']} | {thr} | "
                 f"{rep[s].get('crosscheck_monthly_vs_daily', {}).get('all_match', 'n/a')} | "
                 f"{rep['_gates'][s]['pass']} |")
    L += ["", "## Các đợt nến filler (volume = 0, O=H=L=C)", ""]
    for s in cfg["symbols"]:
        fr = rep[s]["klines_1m"]["filler_runs"]
        L.append(f"- **{s}**: " + "; ".join(f"{r['start'][:16]} ({r['minutes']}′)" for r in fr))
    if "metrics" in rep[cfg["symbols"][0]]:
        L += ["", "## Metrics 5 phút", "", "| Symbol | Dòng | Kỳ vọng | Thiếu | NaN |", "|---|---|---|---|---|"]
        for s in cfg["symbols"]:
            m = rep[s]["metrics"]
            L.append(f"| {s} | {m['rows']:,} | {m['expected_rows']:,} | {m['missing_slots']} | "
                     f"{sum(m['nan_by_column'].values())} |")
    if "fundingRate" in rep[cfg["symbols"][0]]:
        L += ["", "## Funding", "", "| Symbol | Bản ghi | Từ | Đến | Chu kỳ quan sát (giờ) | min | max |",
              "|---|---|---|---|---|---|---|"]
        for s in cfg["symbols"]:
            f = rep[s]["fundingRate"]
            L.append(f"| {s} | {f['rows']} | {f['first'][:16]} | {f['last'][:16]} | "
                     f"{f['interval_hours_observed']} | {f['rate_min']:.5f} | {f['rate_max']:.5f} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n")
