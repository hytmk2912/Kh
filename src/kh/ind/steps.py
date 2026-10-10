"""Các bước của track lướt sóng M1. Mỗi bước được triển khai trong việc tương ứng ở TASKS.md."""
from __future__ import annotations


def step_data(cfg, P, args):
    from kh.ind.data import download, normalize

    download(cfg, P)
    normalize(cfg, P)


def step_labels(cfg, P, args):
    from kh.ind.labels import run_labels

    run_labels(cfg, P)


def step_indicators(cfg, P, args):
    from kh.config import REPO_ROOT
    from kh.ind.indicators.registry import CARDS, cards_markdown, status

    (REPO_ROOT / "docs" / "ind" / "indicator_cards.md").write_text(cards_markdown())
    if args.list:
        for i, c in enumerate(CARDS, 1):
            print(f"{i:3d}. [{c.kind}] {c.name} — {status(c)}")
        n_impl = sum(status(c) == "đã triển khai" for c in CARDS)
        n_no = sum(status(c) == "không triển khai" for c in CARDS)
        print(f"Tổng: {len(CARDS)} chỉ báo ({n_impl} đã triển khai, {n_no} không triển khai được)")
        return
    from kh.ind.signals import run_indicators

    run_indicators(cfg, P)


def step_single(cfg, P, args):
    from kh.ind.single import run_table_a, run_table_b

    run_table_a(cfg, P)
    run_table_b(cfg, P)


def step_combos(cfg, P, args):
    from kh.ind.candidates import run_candidates
    from kh.ind.combos import run_scan
    from kh.ind.wf import run_w1

    part = getattr(args, "part", "all")
    if part in ("all", "c1"):
        run_candidates(cfg, P)
    if part in ("all", "c2"):
        run_scan(cfg, P)
    if part in ("all", "w1"):
        run_w1(cfg, P)


def step_final(cfg, P, args):
    raise SystemExit("Không chạy: chủ repo chọn không mở tập test khoá (CHANGELOG 2026-10-10, docs/ind/conclusion.md)")
