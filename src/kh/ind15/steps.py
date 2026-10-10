"""Các bước track M15. Mỗi bước gọi code track M1 với `args.track` = M15; việc tương ứng ở TASKS_M15.md."""
from __future__ import annotations


def step_data(cfg, P, args):
    from kh.ind.data import build_higher, download

    download(cfg, P)  # chỉ xác minh: file đã `verified` (SHA256) thì bỏ qua
    build_higher(cfg, P, args.track)


def step_labels(cfg, P, args):
    from kh.ind.labels import run_labels

    run_labels(cfg, P, args.track)


def step_indicators(cfg, P, args):
    from kh.ind.signals import run_indicators

    run_indicators(cfg, P, args.track)


def step_single(cfg, P, args):
    from kh.ind.single import run_table_a, run_table_b

    run_table_a(cfg, P, args.track)
    run_table_b(cfg, P, args.track)


def step_combos(cfg, P, args):
    raise NotImplementedError("việc N4 (TASKS_M15.md)")


def step_final(cfg, P, args):
    raise NotImplementedError("việc N5b — chỉ chạy sau khi chủ repo duyệt N5a")
