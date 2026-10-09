"""Chuẩn hóa file zip thô thành Parquet (một file/symbol/loại dữ liệu).

Quy ước:
- Thời gian lưu dạng int64 mili-giây UTC (`*_ms`) để tránh khác biệt phiên bản pandas.
- Không nội suy, không xóa nến. Nến volume = 0 và O=H=L=C được gắn cờ `is_filler`.
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from kh.config import MS_PER_MIN, setup_logging, window_ms

log = setup_logging("data.normalize")

KLINE_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume",
              "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]
KLINE_RENAME = {"open_time": "open_time_ms", "close_time": "close_time_ms", "count": "trade_count",
                "taker_buy_volume": "taker_buy_base_volume"}


def _read_zip_csv(path: Path, names: list[str] | None = None) -> pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        raw = z.read(z.namelist()[0])
    has_header = not raw[:1].isdigit()
    df = pd.read_csv(io.BytesIO(raw), header=0 if has_header else None)
    if not has_header and names:
        df.columns = names[: df.shape[1]]
    return df


def _to_ms(x: pd.Series) -> pd.Series:
    """Một số file có thể dùng micro-giây; đưa tất cả về mili-giây."""
    x = x.astype("int64")
    return np.where(x > 10**14, x // 1000, x).astype("int64")


def normalize_klines(raw_dir: Path, symbol: str, cfg: dict) -> pd.DataFrame:
    files = sorted((raw_dir / "klines_1m" / symbol).glob("*.zip"))
    df = pd.concat([_read_zip_csv(f, KLINE_COLS) for f in files], ignore_index=True)
    df = df.rename(columns=KLINE_RENAME).drop(columns=["ignore"], errors="ignore")
    df["open_time_ms"] = _to_ms(df["open_time_ms"])
    df["close_time_ms"] = _to_ms(df["close_time_ms"])
    lo, hi = window_ms(cfg)
    df = df[(df.open_time_ms >= lo) & (df.open_time_ms < hi)]
    n_before = len(df)
    # Bản ghi trùng hoàn toàn (file tháng và file ngày chồng nhau) được loại; trùng timestamp
    # nhưng khác giá trị thì giữ lại để báo cáo chất lượng phát hiện.
    df = df.drop_duplicates().sort_values("open_time_ms", kind="stable").reset_index(drop=True)
    if n_before != len(df):
        log.info("%s: bỏ %d dòng trùng hoàn toàn", symbol, n_before - len(df))
    for c in ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_base_volume",
              "taker_buy_quote_volume"]:
        df[c] = df[c].astype("float64")
    df["trade_count"] = df["trade_count"].astype("int64")
    df["is_filler"] = (df.volume == 0) & (df.open == df.high) & (df.high == df.low) & (df.low == df.close)
    df.insert(0, "symbol", symbol)
    return df


def normalize_metrics(raw_dir: Path, symbol: str, cfg: dict) -> pd.DataFrame:
    files = sorted((raw_dir / "metrics" / symbol).glob("*.zip"))
    df = pd.concat([_read_zip_csv(f) for f in files], ignore_index=True)
    t = pd.to_datetime(df.pop("create_time"), utc=True)  # [A] create_time là UTC
    df.insert(0, "create_time_ms", (t - pd.Timestamp(0, tz="UTC")) // pd.Timedelta(milliseconds=1))
    lag = cfg["data"]["metrics_availability_lag_min"] * MS_PER_MIN
    df.insert(1, "available_ms", df["create_time_ms"] + lag)
    lo, hi = window_ms(cfg)
    df = df[(df.create_time_ms >= lo) & (df.create_time_ms < hi)]
    df = df.drop_duplicates().sort_values("create_time_ms").reset_index(drop=True)
    df["symbol"] = symbol
    return df


def normalize_funding(raw_dir: Path, symbol: str, cfg: dict) -> pd.DataFrame:
    files = sorted((raw_dir / "fundingRate" / symbol).glob("*.zip"))
    df = pd.concat([_read_zip_csv(f) for f in files], ignore_index=True)
    df["calc_time_ms"] = _to_ms(df.pop("calc_time"))
    # Mốc thanh toán funding làm tròn xuống phút (file có lệch vài ms, vd ...005)
    df["funding_time_ms"] = (df["calc_time_ms"] // MS_PER_MIN) * MS_PER_MIN
    lo, hi = window_ms(cfg)
    df = df[(df.funding_time_ms >= lo) & (df.funding_time_ms < hi)]
    df = df.rename(columns={"last_funding_rate": "funding_rate"})
    df = df.drop_duplicates().sort_values("funding_time_ms").reset_index(drop=True)
    df["symbol"] = symbol
    return df[["symbol", "funding_time_ms", "calc_time_ms", "funding_interval_hours", "funding_rate"]]


NORMALIZERS = {"klines_1m": normalize_klines, "metrics": normalize_metrics, "fundingRate": normalize_funding}


def normalize_all(cfg: dict, raw_dir: Path, norm_dir: Path) -> None:
    for dataset in cfg["data"]["datasets"]:
        for symbol in cfg["symbols"]:
            df = NORMALIZERS[dataset](raw_dir, symbol, cfg)
            out = norm_dir / dataset / f"{symbol}.parquet"
            out.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(out, compression="zstd", index=False)
            log.info("%s %s: %d dòng -> %s", dataset, symbol, len(df), out)


def load(norm_dir: Path, dataset: str, symbol: str) -> pd.DataFrame:
    return pd.read_parquet(norm_dir / dataset / f"{symbol}.parquet")
