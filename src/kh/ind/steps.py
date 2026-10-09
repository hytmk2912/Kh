"""Các bước của track lướt sóng M1. Mỗi bước được triển khai trong việc tương ứng ở TASKS.md."""
from __future__ import annotations


def step_data(cfg, P, args):
    from kh.ind.data import download

    download(cfg, P)


def step_labels(cfg, P, args):
    raise NotImplementedError("việc L1")


def step_indicators(cfg, P, args):
    raise NotImplementedError("việc I1–I2")


def step_single(cfg, P, args):
    raise NotImplementedError("việc S1–S2")


def step_combos(cfg, P, args):
    raise NotImplementedError("việc C1–W1")


def step_final(cfg, P, args):
    raise NotImplementedError("việc F2 (cần chủ repo duyệt F1 trước)")
