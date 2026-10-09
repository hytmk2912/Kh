"""Đếm mọi lần thử (chỉ báo/tổ hợp/tham số) vào reports/ind/trials.csv — dùng cho multiple testing (DSR)."""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

FIELDS = ["utc_time", "stage", "trial_id", "indicators", "htf", "params", "split", "symbols", "note"]


def log_trials(reports_dir: Path, rows: list[dict]) -> int:
    path = Path(reports_dir) / "ind" / "trials.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    if not new:  # chạy lại cùng cấu hình không phải lần thử mới
        with open(path) as f:
            seen = {r["trial_id"] for r in csv.DictReader(f)}
        rows = [r for r in rows if r.get("trial_id") not in seen]
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({"utc_time": now, **{k: r.get(k, "") for k in FIELDS if k != "utc_time"}})
    return len(rows)


def count_trials(reports_dir: Path, stage: str | None = None) -> int:
    path = Path(reports_dir) / "ind" / "trials.csv"
    if not path.exists():
        return 0
    with open(path) as f:
        return sum(1 for r in csv.DictReader(f) if stage is None or r["stage"] == stage)
