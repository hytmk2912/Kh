"""CLI track lướt sóng M1: `python -m kh.ind <bước>`.

Các bước theo TASKS.md: data → labels → indicators → single → combos → final.
"""
from __future__ import annotations

import argparse
import sys
import time

from kh.config import get_paths, load_config, setup_logging

log = setup_logging("ind")

STEPS = {
    "data": ("kh.ind.steps", "step_data", "D1–D2: tải klines 1m + funding, SHA256, manifest, chuẩn hoá, resample M15/H1"),
    "labels": ("kh.ind.steps", "step_labels", "L1: ZigZag 0,5% → sóng, nhịp hồi, đi ngang (đáp án để chấm)"),
    "indicators": ("kh.ind.steps", "step_indicators", "I1–I2: registry chỉ báo, tính chỉ báo + tín hiệu"),
    "single": ("kh.ind.steps", "step_single", "S1–S2: Bảng A + backtest baseline cho từng chỉ báo (Train)"),
    "combos": ("kh.ind.steps", "step_combos", "C1–W1: chọn ứng viên, quét tổ hợp, walk-forward"),
    "final": ("kh.ind.steps", "step_final", "F2: test khoá — chỉ chạy một lần, sau khi chủ repo duyệt"),
}


def main(argv: list[str] | None = None, steps: dict | None = None, prog: str = "python -m kh.ind",
         description: str = "Track lướt sóng M1 bằng tổ hợp chỉ báo (chỉ nghiên cứu, không giao dịch).", track=None) -> None:
    from kh.ind.track import M1

    STEPS_ = steps or STEPS
    track = track or M1
    ap = argparse.ArgumentParser(prog=prog, description=description,
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n".join(f"  {k:<11} {v[2]}" for k, v in STEPS_.items()))
    ap.add_argument("step", choices=list(STEPS_), help="bước cần chạy")
    ap.add_argument("--config", default=None, help="file cấu hình (mặc định configs/default.yaml)")
    ap.add_argument("--list", action="store_true", help="indicators: chỉ liệt kê registry")
    ap.add_argument("--symbols", default=None, help="danh sách symbol cách nhau dấu phẩy (mặc định: 5 symbol)")
    ap.add_argument("--part", default="all", choices=["all", "c1", "c2", "w1"], help="combos: chỉ chạy một phần")
    ap.add_argument("--workers", type=int, default=4, help="số tiến trình song song (mặc định 4)")
    ap.add_argument("--confirm-final", action="store_true", help="final: xác nhận đã được duyệt, chạy test khoá")
    args = ap.parse_args(argv)
    args.track = track
    cfg, P = load_config(args.config), get_paths()
    if args.symbols:
        cfg["symbols"] = args.symbols.split(",")
    mod, fn, _ = STEPS_[args.step]
    t0 = time.time()
    log.info("=== %s %s bắt đầu ===", track.name, args.step)
    try:
        import importlib

        getattr(importlib.import_module(mod), fn)(cfg, P, args)
    except NotImplementedError as e:
        log.error("Bước %s chưa triển khai: %s", args.step, e)
        sys.exit(3)
    except Exception:
        log.exception("Bước %s lỗi", args.step)
        sys.exit(1)
    log.info("=== %s %s xong trong %.1f s ===", track.name, args.step, time.time() - t0)


if __name__ == "__main__":
    main()
