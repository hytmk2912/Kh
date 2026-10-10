"""Dữ liệu cho track lướt sóng M1 (spec §1): tải, manifest, chuẩn hoá, resample, kiểm chất lượng.

Dùng lại `kh.data.vision` (Binance Vision, SHA256 từng zip, retry 2/4/8/16 s, bỏ qua file đã xác minh).
"""
from __future__ import annotations

import datetime as dt
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from kh.config import MS_PER_MIN, setup_logging, window_ms, write_json
from kh.data import normalize as N
from kh.data.vision import fetch, plan_files

log = setup_logging("ind.data")

IND_DATASETS = ["klines_1m", "fundingRate"]


def download(cfg: dict, P) -> pd.DataFrame:
    """Tải klines 1m + funding cho mọi symbol. Ghi `data/manifest.parquet`. Trả về manifest."""
    rows = []
    for dataset in IND_DATASETS:
        for symbol in cfg["symbols"]:
            files = plan_files(cfg, dataset, symbol)
            with ThreadPoolExecutor(cfg["data"]["workers"]) as ex:
                res = list(ex.map(lambda f: fetch(cfg, f, P.raw), files))
            now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            for f, r in zip(files, res):
                ok = r["status"] in ("cached", "downloaded")
                path = f.local_path(P.raw)
                rows.append({"dataset": dataset, "symbol": symbol, "freq": f.freq, "date": f.date, "key": f.key,
                             "url": f"{cfg['data']['vision_url']}/{f.key}", "sha256": r["sha256"], "bytes": r["bytes"],
                             "status": "verified" if ok else r["status"],
                             "new_download": r["status"] == "downloaded",
                             "downloaded_at": dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).isoformat(timespec="seconds")
                             if path.exists() else now})
            log.info("%s %s: %d file (%d tải mới)", dataset, symbol, len(files),
                     sum(r["status"] == "downloaded" for r in res))
    man = pd.DataFrame(rows)
    out = Path(P.data) / "manifest.parquet"
    man.to_parquet(out, index=False)
    n_new = int(man.new_download.sum())
    bad = man[man.status != "verified"]
    log.info("Manifest %s: %d file, %.1f MB, %d tải mới, %d chưa xác minh", out, len(man), man.bytes.sum() / 1e6,
             n_new, len(bad))
    print(f"{n_new} file tải mới; {len(man)} file trong manifest; {len(bad)} file lỗi")
    if len(bad):
        raise RuntimeError(f"{len(bad)} file không xác minh được:\n{bad[['key', 'status']].to_string()}")
    return man


# ---------------------------------------------------------------- D2: chuẩn hoá, resample, chất lượng

AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "quote_volume": "sum",
       "trade_count": "sum", "taker_buy_base_volume": "sum", "taker_buy_quote_volume": "sum"}


def norm_path(P, kind: str, symbol: str) -> Path:
    return Path(P.data) / "norm" / kind / f"symbol={symbol}" / "part.parquet"


def resample(m1: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Dựng nến khung lớn từ M1. `available_at_ms` = thời điểm nến khung lớn đóng (dùng được từ đó trở đi).

    Nến khung lớn chứa nến filler vẫn được dựng (giá filler phẳng, volume 0) và đếm số filler bên trong.
    """
    step = minutes * MS_PER_MIN
    b = (m1.open_time_ms // step) * step
    g = m1.groupby(b.to_numpy(), sort=True)
    out = g.agg(AGG)
    out["n_m1"] = g.size()
    out["n_filler"] = g["is_filler"].sum().astype("int64")
    out.index.name = "open_time_ms"
    out = out.reset_index()
    out["available_at_ms"] = out.open_time_ms + step
    out.insert(1, "open_time", pd.to_datetime(out.open_time_ms, unit="ms", utc=True))
    return out


def infer_tick(close: np.ndarray) -> dict:
    """Suy ra tick size từ dữ liệu: số chữ số thập phân nhỏ nhất biểu diễn đúng mọi giá, rồi ƯCLN các bước giá."""
    u = np.unique(close[np.isfinite(close)])
    for d in range(0, 9):
        sc = u * 10 ** d
        if np.all(np.abs(sc - np.round(sc)) < 1e-6 * np.maximum(1, sc / 1e6)):
            break
    ints = np.round(u * 10 ** d).astype(np.int64)
    g = int(np.gcd.reduce(np.diff(ints))) if len(ints) > 1 else 1
    return {"tick_size": g / 10 ** d, "decimals": d, "min_observed_step": float(np.diff(u).min()) if len(u) > 1 else None,
            "n_unique_close": int(len(u)), "label": "[I] suy ra từ dữ liệu close, chưa đối chiếu exchangeInfo (HTTP 451)"}


def quality(m1: pd.DataFrame, m15: pd.DataFrame, h1: pd.DataFrame, cfg: dict) -> dict:
    lo, hi = window_ms(cfg)
    t = m1.open_time_ms.to_numpy()
    grid = np.arange(lo, hi, MS_PER_MIN)
    px = m1[["open", "high", "low", "close", "volume"]].to_numpy()
    return {"rows_m1": int(len(m1)), "expected_m1": int(len(grid)), "missing_m1": int(len(np.setdiff1d(grid, t))),
            "duplicates_m1": int(len(t) - len(np.unique(t))), "unsorted_steps": int((np.diff(t) <= 0).sum()),
            "ohlc_violations": int(((m1.high < m1[["open", "close"]].max(axis=1)) | (m1.low > m1[["open", "close"]].min(axis=1))
                                    | (m1.high < m1.low)).sum()),
            "negative_values": int((px < 0).sum()), "non_finite_values": int((~np.isfinite(px)).sum()),
            "filler_m1": int(m1.is_filler.sum()), "rows_m15": int(len(m15)), "rows_h1": int(len(h1)),
            "m15_incomplete": int((m15.n_m1 != 15).sum()), "h1_incomplete": int((h1.n_m1 != 60).sum()),
            "first": str(pd.to_datetime(t[0], unit="ms", utc=True)), "last": str(pd.to_datetime(t[-1], unit="ms", utc=True))}


def normalize(cfg: dict, P) -> dict:
    """Chuẩn hoá từng symbol (xử lý tuần tự để tiết kiệm RAM), ghi Parquet và báo cáo chất lượng."""
    man = pd.read_parquet(Path(P.data) / "manifest.parquet")
    rep, ticks = {"_source": {"site": cfg["data"]["vision_url"], "sample_url": man.url.iloc[0],
                              "files": int(len(man)), "sha256_verified": int((man.status == "verified").sum()),
                              "funding_note": "[L] funding chỉ có file tháng; 2026-10-01..08 chưa có trên server"}}, {}
    for s in cfg["symbols"]:
        m1 = N.normalize_klines(P.raw, s, cfg)
        m1.insert(2, "open_time", pd.to_datetime(m1.open_time_ms, unit="ms", utc=True))
        m15, h1 = resample(m1, 15), resample(m1, 60)
        for kind, df in (("klines_1m", m1), ("klines_15m", m15), ("klines_1h", h1)):
            p = norm_path(P, kind, s)
            p.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(p, compression="zstd", index=False)
        f = N.normalize_funding(P.raw, s, cfg)
        p = norm_path(P, "funding", s)
        p.parent.mkdir(parents=True, exist_ok=True)
        f.to_parquet(p, compression="zstd", index=False)
        rep[s] = quality(m1, m15, h1, cfg) | {"funding_rows": int(len(f)),
                                              "funding_last": str(pd.to_datetime(f.funding_time_ms.iloc[-1], unit="ms", utc=True))}
        ticks[s] = infer_tick(m1.close.to_numpy())
        log.info("%s: M1 %d, M15 %d, H1 %d, thiếu %d, trùng %d, filler %d, tick %s", s, len(m1), len(m15), len(h1),
                 rep[s]["missing_m1"], rep[s]["duplicates_m1"], rep[s]["filler_m1"], ticks[s]["tick_size"])
    out = P.reports / "ind"
    write_json(rep, out / "data_quality.json")
    write_json(ticks, out / "tick_size.json")
    return rep


def load_m1(P, symbol: str) -> pd.DataFrame:
    return pd.read_parquet(norm_path(P, "klines_1m", symbol))


def load_htf(P, symbol: str, minutes: int) -> pd.DataFrame:
    return pd.read_parquet(norm_path(P, {15: "klines_15m", 60: "klines_1h"}[minutes], symbol))


def load_funding(P, symbol: str) -> pd.DataFrame:
    return pd.read_parquet(norm_path(P, "funding", symbol))


def load_ticks(P) -> dict:
    with open(P.reports / "ind" / "tick_size.json") as fh:
        return {k: v["tick_size"] for k, v in json.load(fh).items()}
