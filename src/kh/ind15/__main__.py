"""CLI track M15: `python -m kh.ind15 <bước>` (data, labels, indicators, single, combos, final)."""
from __future__ import annotations

from kh.ind.__main__ import main as _main
from kh.ind.track import M15

STEPS = {
    "data": ("kh.ind15.steps", "step_data", "N0: xác minh dữ liệu M1 (manifest SHA256), dựng H4, kiểm số nến M15/H1/H4"),
    "labels": ("kh.ind15.steps", "step_labels", "N1: ZigZag 1,5% trên M15 → sóng, nhịp hồi 0,6%, đi ngang ≥ 8 giờ (đáp án)"),
    "indicators": ("kh.ind15.steps", "step_indicators", "N2: 99 chỉ báo trên M15 (sự kiện + trạng thái), HTF H1 + H4"),
    "single": ("kh.ind15.steps", "step_single", "N3: Bảng A + Bảng B đơn lẻ (Train), thoát lệnh trên đường giá M1"),
    "combos": ("kh.ind15.steps", "step_combos", "N4: ứng viên, tổ hợp kích hoạt + xác nhận, walk-forward"),
    "final": ("kh.ind15.steps", "step_final", "N5b: test 2026-05-16 → 2026-10-08 — chỉ sau khi chủ repo duyệt"),
}


def main(argv: list[str] | None = None) -> None:
    _main(argv, steps=STEPS, prog="python -m kh.ind15", track=M15,
          description="Track M15: vào lệnh khung M15 bằng tổ hợp chỉ báo (chỉ nghiên cứu, không giao dịch).")


if __name__ == "__main__":
    main()
