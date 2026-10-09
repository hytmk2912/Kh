"""Điểm chạy chung: `python -m kh.cli <stage>`.

Các stage: data, quality, waves, features, mine, models, backtest, final, report, all, push.
"""
from __future__ import annotations

import argparse
import sys
import time

from kh.config import get_paths, load_config, setup_logging

log = setup_logging("cli")


def stage_data(cfg, P, args):
    from kh.data.normalize import normalize_all
    from kh.data.vision import download_all

    download_all(cfg, P.raw)
    normalize_all(cfg, P.raw, P.norm)


def stage_quality(cfg, P, args):
    from kh.data.quality import quality_report
    from kh.data.vision import data_version
    from kh.tracking.registry import log_experiment

    rep = quality_report(cfg, P.norm, P.reports, crosscheck=not args.no_crosscheck)
    log_experiment(P.reports, "quality", cfg, data_version(P.raw), "all", 0, rep["_gates"],
                   artifacts=["data_quality/quality_report.md"])
    if not rep["_gates"]["all_pass"]:
        log.error("Dữ liệu KHÔNG đạt tiêu chí chất lượng — dừng. Xem reports/data_quality/.")
        sys.exit(2)


def stage_waves(cfg, P, args):
    from kh.waves.report import run_wave_study

    run_wave_study(cfg, P)


def stage_features(cfg, P, args):
    from kh.features.build import build_all

    build_all(cfg, P)


def stage_mine(cfg, P, args):
    from kh.patterns.mining import run_mining

    run_mining(cfg, P)


def stage_models(cfg, P, args):
    from kh.models.walkforward import run_models

    run_models(cfg, P)


def stage_backtest(cfg, P, args):
    from kh.backtest.study import run_backtest_study

    run_backtest_study(cfg, P)


def stage_final(cfg, P, args):
    from kh.evaluation.final_test import run_final_test

    run_final_test(cfg, P, confirm=args.confirm_final, force=args.force)


def stage_report(cfg, P, args):
    from kh.evaluation.summary import write_summary

    write_summary(cfg, P)


def stage_push(cfg, P, args):
    from kh.gitsync import push_reports

    push_reports(P, branch=args.branch, message=args.message)


STAGES = {"data": stage_data, "quality": stage_quality, "waves": stage_waves, "features": stage_features,
          "mine": stage_mine, "models": stage_models, "backtest": stage_backtest, "final": stage_final,
          "report": stage_report, "push": stage_push}
ALL = ["data", "quality", "waves", "features", "mine", "models", "backtest", "report"]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="kh")
    ap.add_argument("stage", choices=list(STAGES) + ["all"])
    ap.add_argument("--config", default=None)
    ap.add_argument("--no-crosscheck", action="store_true", help="bỏ đối chiếu file ngày (cần mạng)")
    ap.add_argument("--confirm-final", action="store_true", help="xác nhận chạy final test (một lần)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--branch", default="colab-results")
    ap.add_argument("--message", default=None)
    args = ap.parse_args(argv)
    cfg, P = load_config(args.config), get_paths()
    for st in (ALL if args.stage == "all" else [args.stage]):
        t0 = time.time()
        log.info("=== Stage %s bắt đầu (config %s) ===", st, cfg["_hash"])
        STAGES[st](cfg, P, args)
        log.info("=== Stage %s xong trong %.1f s ===", st, time.time() - t0)


if __name__ == "__main__":
    main()
