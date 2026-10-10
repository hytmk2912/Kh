"""Tải dữ liệu công khai từ Binance Vision (data.binance.vision).

Checkpoint: mỗi file zip đã tải và khớp SHA256 có một file `.sha256` đi kèm.
Chạy lại sẽ bỏ qua file đã xác minh, nên có thể tiếp tục sau khi Colab mất phiên.
Không cần API key, không gửi lệnh.
"""
from __future__ import annotations

import hashlib
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from kh.config import setup_logging

log = setup_logging("data.vision")

# Đường dẫn trên Binance Vision cho từng loại dữ liệu USDⓈ-M
DATASET_PREFIX = {
    "klines_1m": ("klines/{symbol}/1m", "{symbol}-1m-{date}.zip"),
    "metrics": ("metrics/{symbol}", "{symbol}-metrics-{date}.zip"),
    "fundingRate": ("fundingRate/{symbol}", "{symbol}-fundingRate-{date}.zip"),
}
HAS_MONTHLY = {"klines_1m": True, "metrics": False, "fundingRate": True}
HAS_DAILY = {"klines_1m": True, "metrics": True, "fundingRate": False}


@dataclass(frozen=True)
class RemoteFile:
    dataset: str
    symbol: str
    freq: str  # "monthly" | "daily"
    date: str  # "YYYY-MM" | "YYYY-MM-DD"

    @property
    def key(self) -> str:
        folder, name = DATASET_PREFIX[self.dataset]
        return f"data/futures/um/{self.freq}/{folder.format(symbol=self.symbol)}/" + \
            name.format(symbol=self.symbol, date=self.date)

    def local_path(self, raw_dir: Path) -> Path:
        return raw_dir / self.dataset / self.symbol / Path(self.key).name


def http_get(url: str, timeout: int, retries: int) -> tuple[int, bytes]:
    """GET có retry + exponential backoff (2, 4, 8, 16 ... giây). 404 không retry."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "kh-research"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, b""
            last_err = e
        except Exception as e:  # lỗi mạng tạm thời (SSL EOF, reset, timeout)
            last_err = e
        wait = 2 ** (attempt + 1)
        log.warning("GET %s lỗi (%s), thử lại sau %ss", url.rsplit("/", 1)[-1], last_err, wait)
        time.sleep(wait)
    raise RuntimeError(f"Hết lượt thử: {url}: {last_err}")


def list_remote(cfg: dict, dataset: str, symbol: str, freq: str) -> list[str]:
    """Danh sách ngày/tháng có file trên Binance Vision (phân trang S3)."""
    folder, _ = DATASET_PREFIX[dataset]
    prefix = f"data/futures/um/{freq}/{folder.format(symbol=symbol)}/"
    dates, marker = [], ""
    while True:
        url = f"{cfg['data']['list_url']}?prefix={prefix}" + (f"&marker={marker}" if marker else "")
        status, body = http_get(url, cfg["data"]["timeout_s"], cfg["data"]["retries"])
        text = body.decode()
        keys = re.findall(r"<Key>([^<]+)</Key>", text)
        for k in keys:
            m = re.search(r"(\d{4}-\d{2}(?:-\d{2})?)\.zip$", k)
            if m:
                dates.append(m.group(1))
        if "<IsTruncated>true</IsTruncated>" not in text or not keys:
            return sorted(set(dates))
        marker = keys[-1]


def plan_files(cfg: dict, dataset: str, symbol: str) -> list[RemoteFile]:
    """Chọn file cần tải: file tháng cho tháng đã đủ trên server, file ngày cho phần còn lại."""
    start = pd.Timestamp(cfg["window"]["start"])
    end = pd.Timestamp(cfg["window"]["end"])
    months = pd.period_range(start, end, freq="M")
    monthly = set(list_remote(cfg, dataset, symbol, "monthly")) if HAS_MONTHLY[dataset] else set()
    daily = set(list_remote(cfg, dataset, symbol, "daily")) if HAS_DAILY[dataset] else set()
    files: list[RemoteFile] = []
    for p in months:
        m = p.strftime("%Y-%m")
        if m in monthly:
            files.append(RemoteFile(dataset, symbol, "monthly", m))
            continue
        days = pd.date_range(max(p.start_time, start), min(p.end_time.normalize(), end), freq="D")
        got = [d.strftime("%Y-%m-%d") for d in days if d.strftime("%Y-%m-%d") in daily]
        if len(got) < len(days):
            log.warning("%s %s %s: thiếu %d/%d file ngày trên server", dataset, symbol, m,
                        len(days) - len(got), len(days))
        files += [RemoteFile(dataset, symbol, "daily", d) for d in got]
    return files


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(cfg: dict, rf: RemoteFile, raw_dir: Path) -> dict:
    """Tải một file nếu chưa có bản đã xác minh. Trả về dòng manifest."""
    path = rf.local_path(raw_dir)
    marker = path.with_suffix(".zip.sha256")
    if path.exists() and marker.exists() and marker.read_text().strip() == _sha256(path):
        return {"key": rf.key, "sha256": marker.read_text().strip(), "bytes": path.stat().st_size,
                "status": "cached"}
    url = f"{cfg['data']['vision_url']}/{rf.key}"
    t, r = cfg["data"]["timeout_s"], cfg["data"]["retries"]
    for attempt in range(r):
        status, blob = http_get(url, t, r)
        if status != 200:
            return {"key": rf.key, "sha256": None, "bytes": 0, "status": f"http_{status}"}
        _, chk = http_get(url + ".CHECKSUM", t, r)
        expected = chk.decode().split()[0] if chk else None
        actual = hashlib.sha256(blob).hexdigest()
        if expected == actual:
            break
        log.warning("Checksum sai %s (lần %d)", rf.key, attempt + 1)
    else:
        return {"key": rf.key, "sha256": actual, "bytes": len(blob), "status": "checksum_mismatch"}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".zip.part")
    tmp.write_bytes(blob)
    tmp.replace(path)  # ghi nguyên tử: không để lại file zip dở dang
    marker.write_text(actual)
    return {"key": rf.key, "sha256": actual, "bytes": len(blob), "status": "downloaded"}


def download_all(cfg: dict, raw_dir: Path) -> pd.DataFrame:
    """Tải toàn bộ dữ liệu theo cấu hình, ghi manifest.csv."""
    rows = []
    for dataset in cfg["data"]["datasets"]:
        for symbol in cfg["symbols"]:
            files = plan_files(cfg, dataset, symbol)
            log.info("%s %s: %d file", dataset, symbol, len(files))
            with ThreadPoolExecutor(cfg["data"]["workers"]) as ex:
                res = list(ex.map(lambda f: fetch(cfg, f, raw_dir), files))
            for f, r in zip(files, res):
                rows.append({"dataset": dataset, "symbol": symbol, "freq": f.freq, "date": f.date,
                             "path": str(f.local_path(raw_dir).relative_to(raw_dir)), **r})
    man = pd.DataFrame(rows)
    man.to_csv(raw_dir / "manifest.csv", index=False)
    bad = man[~man.status.isin(["cached", "downloaded"])]
    if len(bad):
        log.error("%d file lỗi:\n%s", len(bad), bad[["key", "status"]].to_string())
    log.info("Manifest: %d file, %.1f MB, trạng thái %s", len(man), man.bytes.sum() / 1e6,
             man.status.value_counts().to_dict())
    return man


def data_version(raw_dir: Path) -> str:
    """Phiên bản dữ liệu = hash của (key, sha256) trong manifest."""
    p = raw_dir / "manifest.csv"
    if not p.exists():
        return "none"
    man = pd.read_csv(p).sort_values("key")
    return hashlib.sha256("\n".join(man.key + ":" + man.sha256.astype(str)).encode()).hexdigest()[:12]
