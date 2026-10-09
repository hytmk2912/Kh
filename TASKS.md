# TASKS.md — Track lướt sóng M1 bằng tổ hợp chỉ báo

Quy tắc: làm việc `[ ]` đầu tiên. Chỉ đổi sang `[x]` khi lệnh ở "Xong khi" chạy qua **và** đã dán kết quả vào mục Log.
Đặc tả: `docs/ind/spec.md`. Quy tắc chung: `CLAUDE.md`.

## Việc

### 0. Khung dự án
- [ ] **K1** Tạo `pyproject.toml` (gói `kh`, `src/` layout), `requirements.txt` khoá phiên bản, `src/kh/ind/__main__.py` (CLI các bước), `tests/`, nhánh `ind-scalp`, mở PR nháp vào `master`.
  - Xong khi: `pip install -e . && python -m kh.ind --help && pytest -q` chạy không lỗi; có link PR.

### D. Dữ liệu (spec §1)
- [ ] **D1** Tải klines 1m + funding 5 symbol, xác minh SHA256, ghi manifest, chạy lại không tải lại.
  - Xong khi: `python -m kh.ind data` lần 2 báo "0 file tải mới"; manifest có 5 × 32 zip klines (24 tháng + 8 ngày) + 5 × 24 zip funding, tất cả `verified`.
- [ ] **D2** Chuẩn hoá Parquet, gắn `is_filler`, resample M15/H1, suy ra tick size, xuất `data_quality.json`.
  - Xong khi: `pytest -q tests/test_data.py` qua; mỗi symbol 1.051.200 nến M1, 70.080 nến M15, 17.520 nến H1, 0 thiếu, 0 trùng; số filler = BTC 126 / ETH 127 / BNB 128 / SOL 128 / XRP 127.

### L. Nhãn sóng (spec §2)
- [ ] **L1** ZigZag 0,5% trên high/low (lưu `event_time` + `confirm_time`), nhãn 4 trạng thái + UNKNOWN, cờ sóng nhanh.
  - Xong khi: `pytest -q tests/test_labels.py` qua (gồm chuỗi giá tự tạo có đáp án biết trước, và test module tín hiệu không import module nhãn); `reports/ind/waves_stats.json` có đủ 5 symbol × 3 ngưỡng (0,4 / 0,5 / 0,7%).

### I. Chỉ báo và tín hiệu (spec §3)
- [ ] **I1** Registry + phiếu cho **mọi** chỉ báo ở Phụ lục A (kể cả không triển khai được).
  - Xong khi: `python -m kh.ind indicators --list` in số chỉ báo = số tên trong Phụ lục A; `docs/ind/indicator_cards.md` sinh tự động.
- [ ] **I2** Triển khai chỉ báo + tín hiệu directional/filter + bộ lọc HTF.
  - Xong khi: `pytest -q tests/test_lookahead.py` qua cho mọi chỉ báo đã triển khai (20 thời điểm ngẫu nhiên/chỉ báo); đối chiếu ≥ 10 chỉ báo phổ biến (EMA, RSI, MACD, ATR, BB, Stoch, ADX, SuperTrend, OBV, VWAP) với một thư viện độc lập, sai số < 1e-4 sau giai đoạn khởi động, kết quả ghi trong phiếu.

### S. Chấm đơn lẻ (spec §4)
- [ ] **S1** Bảng A đơn lẻ (Train), có/không HTF, từng symbol + tổng hợp, kèm precision ngẫu nhiên.
  - Xong khi: `reports/ind/single_tableA.csv` có số dòng = số chỉ báo triển khai × 5 symbol × 2 (HTF); không ô nào bịa (ô trống = NaN có lý do).
- [ ] **S2** Backtest baseline đơn lẻ (Train), kịch bản phí/trượt giá.
  - Xong khi: `pytest -q tests/test_backtest.py` qua (gồm: vào lệnh ở open nến sau; TP+SL cùng nến → SL; phí tính 2 chiều; không vào lệnh trong filler); `reports/ind/single_tableB.csv` có đủ cột ở spec §4.

### C + W. Tổ hợp và walk-forward (spec §5–6)
- [ ] **C1** Chọn 20 ứng viên (16 D + 4 F) theo điểm chốt trước, loại trùng tương quan > 0,8.
  - Xong khi: `reports/ind/candidates.csv` có 20 dòng + điểm từng tiêu chí.
- [ ] **C2** Quét tổ hợp 2–4 × có/không HTF, Bảng A tổ hợp, top 50.
  - Xong khi: `reports/ind/trials.csv` ghi tổng số lần thử thật; `combos_tableA.csv` có top 50 thoả precision ≥ 1,5 × ngẫu nhiên.
- [ ] **W1** Walk-forward (train mở rộng ≥ 6 tháng, kiểm tra 1 tháng, embargo 1 ngày) cho top 50 → Bảng B, DSR, PBO, CI bootstrap, leave-one-coin-out, độ nhạy ±20%.
  - Xong khi: `pytest -q tests/test_walkforward.py` qua (không fold nào có test chồng train, embargo đúng 1 ngày); `combos_tableB.csv` + `top10.md` có đủ cột ở spec §8.

### F. Chiến lược cuối (spec §7) — **dừng hỏi trước khi chạy test khoá**
- [ ] **F1** Viết `docs/ind/strategy.md`, ghi chiến lược chọn + hash commit vào `CHANGELOG.md`, **hỏi chủ repo duyệt**.
  - Xong khi: chủ repo trả lời đồng ý trong PR hoặc chat.
- [ ] **F2** Chạy test khoá đúng 1 lần, viết `docs/ind/conclusion.md`.
  - Xong khi: `reports/ind/final_test.json` + SHA256 đã commit; conclusion tách [F]/[I]/[A]/[L].

## Log bằng chứng
<!-- Mỗi dòng: YYYY-MM-DD · mã việc · lệnh · kết quả chính -->

## Ghi chú phiên
<!-- Việc đang làm dở, file đang sửa, vấn đề chưa giải quyết. Cập nhật trước khi hết phiên. -->
