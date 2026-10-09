"""Giai đoạn 0 — kiểm tra khả thi nguồn dữ liệu Binance USDT-M Futures.

Chỉ đọc dữ liệu công khai, không cần API key, không gửi lệnh.

Kiểm tra:
  1. REST API fapi.binance.com có truy cập được từ máy đang chạy không (HTTP 451 = vùng bị chặn).
  2. Binance Vision (data.binance.vision): liệt kê file klines 1m / metrics / fundingRate
     cho 5 symbol trong cửa sổ 730 ngày, tìm ngày đầu tiên có dữ liệu.
  3. Tải 1 file mẫu, xác minh SHA256, đọc cột, kiểm tra OHLC, khoảng trống, đo dung lượng Parquet.

Chạy trên Colab:  !python tools/phase0_probe.py --sample-symbol BTCUSDT --sample-month 2025-09
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import re
import sys
import urllib.error
import urllib.request
import zipfile

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]
S3_LIST = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
VISION = "https://data.binance.vision"
FAPI = "https://fapi.binance.com"


def http_get(url: str, timeout: int = 60) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "kh-phase0-probe"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def list_keys(prefix: str) -> list[str]:
    """Liệt kê toàn bộ key dưới prefix (S3 trả tối đa 1000 key/lần nên phải phân trang)."""
    keys, marker = [], ""
    while True:
        url = f"{S3_LIST}?prefix={prefix}" + (f"&marker={marker}" if marker else "")
        status, body = http_get(url)
        if status != 200:
            raise RuntimeError(f"List {prefix} -> HTTP {status}")
        text = body.decode()
        batch = re.findall(r"<Key>([^<]+)</Key>", text)
        keys += [k for k in batch if k.endswith(".zip")]
        if "<IsTruncated>true</IsTruncated>" not in text or not batch:
            return keys
        marker = batch[-1]


def date_of(key: str) -> str:
    m = re.search(r"(\d{4}-\d{2}(?:-\d{2})?)\.zip$", key)
    return m.group(1) if m else ""


def check_rest() -> dict:
    out = {}
    for path in ["/fapi/v1/ping", "/fapi/v1/exchangeInfo"]:
        status, body = http_get(FAPI + path, timeout=20)
        out[path] = {"http": status, "body_head": body[:160].decode(errors="replace")}
    return out


def coverage(symbol: str, start: dt.date, end: dt.date) -> dict:
    res = {}
    specs = {
        "klines_1m_monthly": f"data/futures/um/monthly/klines/{symbol}/1m/",
        "klines_1m_daily": f"data/futures/um/daily/klines/{symbol}/1m/",
        "metrics_daily": f"data/futures/um/daily/metrics/{symbol}/",
        "fundingRate_monthly": f"data/futures/um/monthly/fundingRate/{symbol}/",
    }
    for name, prefix in specs.items():
        dates = sorted(date_of(k) for k in list_keys(prefix))
        in_win = [d for d in dates if start.isoformat()[: len(d)] <= d <= end.isoformat()[: len(d)]]
        info = {"first_available": dates[0] if dates else None,
                "last_available": dates[-1] if dates else None,
                "files_total": len(dates), "files_in_window": len(in_win)}
        if name.endswith("_daily"):
            want = {(start + dt.timedelta(days=i)).isoformat() for i in range((end - start).days + 1)}
            missing = sorted(want - set(in_win))
            info["days_expected"] = len(want)
            info["days_missing"] = len(missing)
            info["missing_sample"] = missing[:10]
        res[name] = info
    return res


def fetch_zip_csv(key: str):
    import pandas as pd

    status, blob = http_get(f"{VISION}/{key}", timeout=180)
    if status != 200:
        raise RuntimeError(f"{key} -> HTTP {status}")
    s2, chk = http_get(f"{VISION}/{key}.CHECKSUM")
    expected = chk.decode().split()[0] if s2 == 200 else None
    actual = hashlib.sha256(blob).hexdigest()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        raw = z.read(z.namelist()[0])
    first = raw.split(b"\n", 1)[0].decode()
    has_header = not first[:1].isdigit()
    df = pd.read_csv(io.BytesIO(raw), header=0 if has_header else None)
    return df, {"zip_bytes": len(blob), "csv_bytes": len(raw), "sha256_ok": expected == actual,
                "has_header": has_header, "first_line": first[:200]}


KLINE_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume",
              "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def sample_klines(symbol: str, month: str) -> dict:
    import pandas as pd

    key = f"data/futures/um/monthly/klines/{symbol}/1m/{symbol}-1m-{month}.zip"
    df, meta = fetch_zip_csv(key)
    if not meta["has_header"]:
        df.columns = KLINE_COLS
    t = df["open_time"].astype("int64")
    ts_unit = "us" if t.iloc[0] > 10**14 else "ms"  # đề phòng file chuyển sang micro-giây
    step = 60_000 * (1000 if ts_unit == "us" else 1)
    diffs = t.diff().dropna()
    y, m = map(int, month.split("-"))
    days = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.date(y, m, 1)).days
    out = {
        "key": key, **meta, "columns": list(df.columns), "rows": len(df),
        "rows_expected": days * 1440, "timestamp_unit": ts_unit,
        "first_open_time_utc": str(pd.to_datetime(t.iloc[0], unit=ts_unit, utc=True)),
        "last_open_time_utc": str(pd.to_datetime(t.iloc[-1], unit=ts_unit, utc=True)),
        "duplicates": int(t.duplicated().sum()), "non_monotonic": int((diffs <= 0).sum()),
        "gaps": int((diffs > step).sum()), "missing_minutes": int(((diffs[diffs > step] // step) - 1).sum()),
        "close_minus_open_time_ms_mode": int((df["close_time"] - df["open_time"]).mode()[0]),
        "ohlc_violations": int(((df.high < df[["open", "close"]].max(axis=1)) |
                                (df.low > df[["open", "close"]].min(axis=1)) | (df.high < df.low)).sum()),
        "negative_values": int((df[["open", "high", "low", "close", "volume"]] < 0).sum().sum()),
        "zero_volume_rows": int((df.volume == 0).sum()),
    }
    try:
        buf = io.BytesIO()
        df.drop(columns=["ignore"], errors="ignore").to_parquet(buf, compression="zstd", index=False)
        out["parquet_zstd_bytes"] = buf.getbuffer().nbytes
    except Exception as e:  # pyarrow chưa cài
        out["parquet_zstd_bytes"] = f"skip: {e}"
    return out


def sample_simple(key: str) -> dict:
    df, meta = fetch_zip_csv(key)
    return {"key": key, **meta, "columns": list(df.columns), "rows": len(df), "head": df.head(3).to_dict("records")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=730)
    ap.add_argument("--end", default=None, help="Ngày UTC cuối (mặc định: hôm qua)")
    ap.add_argument("--sample-symbol", default="BTCUSDT")
    ap.add_argument("--sample-month", default=None, help="YYYY-MM, mặc định: tháng trước")
    ap.add_argument("--out", default="phase0_probe_result.json")
    a = ap.parse_args()

    today = dt.datetime.now(dt.timezone.utc).date()
    end = dt.date.fromisoformat(a.end) if a.end else today - dt.timedelta(days=1)
    start = end - dt.timedelta(days=a.days - 1)
    month = a.sample_month or (today.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
    day = (end - dt.timedelta(days=2)).isoformat()
    report = {"run_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "window": {"start": start.isoformat(), "end": end.isoformat(), "days": a.days}}

    print("[1] REST API fapi.binance.com ..."); report["rest"] = check_rest()
    print("[2] Binance Vision coverage ...")
    report["coverage"] = {}
    for s in SYMBOLS:
        print("   ", s); report["coverage"][s] = coverage(s, start, end)
    ss = a.sample_symbol
    print(f"[3] Sample klines {ss} {month} ..."); report["sample_klines"] = sample_klines(ss, month)
    print(f"[4] Sample metrics {ss} {day} ...")
    report["sample_metrics"] = sample_simple(f"data/futures/um/daily/metrics/{ss}/{ss}-metrics-{day}.zip")
    print(f"[5] Sample fundingRate {ss} {month} ...")
    report["sample_funding"] = sample_simple(f"data/futures/um/monthly/fundingRate/{ss}/{ss}-fundingRate-{month}.zip")

    with open(a.out, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
