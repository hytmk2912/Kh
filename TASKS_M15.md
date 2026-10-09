# TASKS_M15.md — Track M15: vào lệnh khung M15 bằng tổ hợp chỉ báo

Quy tắc: làm việc `[ ]` đầu tiên. Chỉ đổi sang `[x]` khi lệnh ở "Xong khi" chạy qua **và** đã dán kết quả vào mục Log.
Đặc tả: `docs/ind15/spec.md`. Quy tắc chung: `CLAUDE.md`. Nhánh: `ind15`.

## Việc

### N0. Chuẩn bị
- [ ] **N0** Tham số hoá khung thời gian trong code track M1 (`tf=1m|15m`) thay vì chép code; thêm resample H4; CLI `python -m kh.ind15 <bước>` (data, labels, indicators, single, combos, final).
  - Xong khi: `pytest -q` qua toàn bộ test cũ + mới; chạy lại `python -m kh.ind single --symbols BTCUSDT` cho ra `single_tableA.csv` phần BTC **giống hệt** bản đã commit (so SHA256 hoặc so từng ô) → code M1 không bị đổi kết quả; mỗi symbol M15 70.080 / H1 17.520 / H4 4.380 nến.

### N1. Nhãn sóng M15 (spec §1)
- [ ] **N1** ZigZag 1,5% trên M15, sóng nhanh ≤ 8 giờ, đi ngang ≥ 8 giờ < 1,5%, nhịp hồi 0,6%.
  - Xong khi: `pytest -q tests/test_labels.py` qua với ca M15 (chuỗi giá tự tạo có đáp án biết trước); `reports/ind15/waves_stats.json` đủ 5 symbol × 3 ngưỡng (1,0 / 1,5 / 2,0%), chỉ train + validation.

### N2. Chỉ báo M15 (spec §3)
- [ ] **N2** 99 chỉ báo trên M15 (dạng sự kiện + dạng trạng thái), quy đổi tham số "1 ngày" = 96 nến, HTF H1 + H4.
  - Xong khi: `pytest -q tests/test_lookahead.py` qua cho mọi chỉ báo trên M15, cả dạng sự kiện và trạng thái, cùng H1/H4; `reports/ind15/signal_summary.json` có số tín hiệu mỗi chỉ báo × symbol; mọi tham số quy đổi đã ghi CHANGELOG.

### N3. Chấm đơn lẻ (spec §4)
- [ ] **N3** Bảng A + Bảng B đơn lẻ trên train, có/không HTF, mô phỏng thoát lệnh trên đường giá M1.
  - Xong khi: `pytest -q tests/test_backtest.py` qua với ca M15 (vào ở open nến M15 sau; TP/SL kiểm trên từng nến M1; cùng nến M1 → SL; hết 32 nến M15 → đóng ở close; funding đúng mốc); `reports/ind15/single_tableA.csv`, `single_tableB.csv`, `single_tableB_summary.csv` (có cột gross/lệnh) đủ 5 symbol × 2 HTF.

### N4. Tổ hợp + walk-forward (spec §5–6)
- [ ] **N4a** Chọn 10 D + 3 F, quét 1 kích hoạt + 1–2 xác nhận × filter × HTF, Bảng A top 30.
  - Xong khi: `reports/ind15/candidates.csv` 13 dòng; `trials.csv` ghi số lần thử thật (≈ 1.800 + đơn lẻ); `combos_tableA.csv` chỉ gồm tổ hợp ≥ 30 lệnh/symbol và precision ≥ 1,2× ngẫu nhiên.
- [ ] **N4b** Walk-forward → Bảng B, DSR, PBO, CI95, leave-one-coin-out, độ nhạy ±20%; áp tiêu chí "đạt" §6.
  - Xong khi: `pytest -q tests/test_walkforward.py` qua; `combos_tableB.csv` + `top10.md` có cột đạt/không đạt từng tiêu chí §6; `reports/ind15/m1_vs_m15.md` có bảng so sánh.

### N5. Kết luận — **dừng hỏi chủ repo trước khi mở test**
- [ ] **N5a** Có tổ hợp đạt §6 → viết `docs/ind15/strategy.md` + hỏi duyệt. Không có → viết `docs/ind15/conclusion.md` và hỏi hướng tiếp.
  - Xong khi: file tương ứng đã commit, câu hỏi đã gửi chủ repo, chủ repo đã trả lời.
- [ ] **N5b** (chỉ khi được duyệt) Chạy test 2026-05-16 → 2026-10-08 đúng 1 lần, ghi "test bán sạch"; đăng ký forward holdout từ 2026-10-09 vào `configs/locked_strategies_ind15.yaml`.
  - Xong khi: `reports/ind15/final_test.json` + SHA256 đã commit; conclusion tách [F]/[I]/[A]/[L].

## Log bằng chứng
<!-- Mỗi dòng: YYYY-MM-DD · mã việc · lệnh · kết quả chính -->

## Ghi chú phiên
<!-- Việc đang làm dở, file đang sửa, vấn đề chưa giải quyết. Cập nhật trước khi hết phiên. -->
