"""Sổ đăng ký thí nghiệm: mọi lần chạy một giai đoạn đều được ghi lại (kể cả kết quả xấu)."""
from __future__ import annotations

import csv
import datetime as dt
import json
import uuid
from pathlib import Path

from kh.config import git_hash

FIELDS = ["exp_id", "utc_time", "stage", "git", "config_hash", "data_version", "split_used",
          "n_hypotheses_tested", "summary", "warnings", "artifacts"]


def log_experiment(reports_dir: Path, stage: str, cfg: dict, data_version: str, split_used: str,
                   n_tests: int, summary: dict, warnings: list[str] | None = None,
                   artifacts: list[str] | None = None) -> str:
    path = reports_dir / "experiments" / "registry.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    exp_id = f"{stage}-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:6]}"
    row = {"exp_id": exp_id, "utc_time": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "stage": stage, "git": git_hash(), "config_hash": cfg.get("_hash", ""),
           "data_version": data_version, "split_used": split_used, "n_hypotheses_tested": n_tests,
           "summary": json.dumps(summary, ensure_ascii=False, default=str),
           "warnings": json.dumps(warnings or [], ensure_ascii=False),
           "artifacts": json.dumps(artifacts or [], ensure_ascii=False)}
    new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    return exp_id
