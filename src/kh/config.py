"""Đọc cấu hình, đường dẫn, logging và các hàm thời gian dùng chung."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MS_PER_MIN = 60_000


@dataclass
class Paths:
    data: Path
    reports: Path
    logs: Path

    @property
    def raw(self) -> Path:
        return self.data / "raw"

    @property
    def norm(self) -> Path:
        return self.data / "normalized"

    @property
    def work(self) -> Path:
        return self.data / "work"


def load_config(path: str | os.PathLike | None = None) -> dict:
    path = Path(path) if path else REPO_ROOT / "configs" / "default.yaml"
    with open(path) as f:
        cfg = yaml.safe_load(f)
    cfg["_path"] = str(path)
    cfg["_hash"] = config_hash(cfg)
    return cfg


def config_hash(cfg: dict) -> str:
    clean = {k: v for k, v in cfg.items() if not k.startswith("_")}
    return hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest()[:12]


def get_paths() -> Paths:
    data = Path(os.environ.get("KH_DATA_DIR", REPO_ROOT / "data"))
    reports = Path(os.environ.get("KH_REPORTS_DIR", REPO_ROOT / "reports"))
    logs = Path(os.environ.get("KH_LOG_DIR", REPO_ROOT / "logs"))
    for p in (data, reports, logs):
        p.mkdir(parents=True, exist_ok=True)
    return Paths(data, reports, logs)


def setup_logging(name: str = "kh") -> logging.Logger:
    logger = logging.getLogger("kh")
    if logger.handlers:
        return logger.getChild(name) if name != "kh" else logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%dT%H:%M:%S")
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    fh = logging.FileHandler(get_paths().logs / "kh.log")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger.getChild(name) if name != "kh" else logger


def git_hash() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "configs"], cwd=REPO_ROOT,
                               capture_output=True, text=True).stdout.strip()
        return out + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


def day_ms(day: str, end_of_day: bool = False) -> int:
    """Mốc ms UTC của 00:00 ngày `day`; end_of_day=True trả mốc 00:00 ngày kế tiếp (biên mở)."""
    ts = pd.Timestamp(day, tz="UTC")
    if end_of_day:
        ts += pd.Timedelta(days=1)
    return int(ts.value // 1_000_000)


def window_ms(cfg: dict) -> tuple[int, int]:
    return day_ms(cfg["window"]["start"]), day_ms(cfg["window"]["end"], end_of_day=True)


def split_ms(cfg: dict, name: str) -> tuple[int, int]:
    a, b = cfg["splits"][name]
    return day_ms(a), day_ms(b, end_of_day=True)


def to_dt(ms) -> pd.DatetimeIndex | pd.Timestamp:
    return pd.to_datetime(ms, unit="ms", utc=True)


def write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=_json_default)


def _json_default(o):
    import numpy as np

    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def md_table(df: pd.DataFrame, floatfmt: str = "{:.3f}") -> str:
    """Bảng Markdown đơn giản (không cần gói tabulate)."""
    cols = [str(df.index.name or "")] + [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in df.iterrows():
        cells = [floatfmt.format(v) if isinstance(v, float) else str(v) for v in row]
        lines.append("| " + " | ".join([str(idx)] + cells) + " |")
    return "\n".join(lines)
