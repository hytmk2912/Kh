"""Dữ liệu cho track lướt sóng M1 (spec §1): tải, manifest, chuẩn hoá, resample, kiểm chất lượng.

Dùng lại `kh.data.vision` (Binance Vision, SHA256 từng zip, retry 2/4/8/16 s, bỏ qua file đã xác minh).
"""
from __future__ import annotations

import datetime as dt
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from kh.config import setup_logging
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
