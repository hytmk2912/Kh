# TASKS.md — Track lướt sóng M1 bằng tổ hợp chỉ báo

Quy tắc: làm việc `[ ]` đầu tiên. Chỉ đổi sang `[x]` khi lệnh ở "Xong khi" chạy qua **và** đã dán kết quả vào mục Log.
Đặc tả: `docs/ind/spec.md`. Quy tắc chung: `CLAUDE.md`.

## Việc

### 0. Khung dự án
- [x] **K1** Tạo `pyproject.toml` (gói `kh`, `src/` layout), `requirements.txt` khoá phiên bản, `src/kh/ind/__main__.py` (CLI các bước), `tests/`, nhánh `ind-scalp`, mở PR nháp vào `master`.
  - Xong khi: `pip install -e . && python -m kh.ind --help && pytest -q` chạy không lỗi; có link PR.

### D. Dữ liệu (spec §1)
- [x] **D1** Tải klines 1m + funding 5 symbol, xác minh SHA256, ghi manifest, chạy lại không tải lại.
  - Xong khi: `python -m kh.ind data` lần 2 báo "0 file tải mới"; manifest có 5 × 32 zip klines (24 tháng + 8 ngày) + 5 × 24 zip funding, tất cả `verified`.
- [x] **D2** Chuẩn hoá Parquet, gắn `is_filler`, resample M15/H1, suy ra tick size, xuất `data_quality.json`.
  - Xong khi: `pytest -q tests/test_data.py` qua; mỗi symbol 1.051.200 nến M1, 70.080 nến M15, 17.520 nến H1, 0 thiếu, 0 trùng; số filler = BTC 126 / ETH 127 / BNB 128 / SOL 128 / XRP 127.

### L. Nhãn sóng (spec §2)
- [x] **L1** ZigZag 0,5% trên high/low (lưu `event_time` + `confirm_time`), nhãn 4 trạng thái + UNKNOWN, cờ sóng nhanh.
  - Xong khi: `pytest -q tests/test_labels.py` qua (gồm chuỗi giá tự tạo có đáp án biết trước, và test module tín hiệu không import module nhãn); `reports/ind/waves_stats.json` có đủ 5 symbol × 3 ngưỡng (0,4 / 0,5 / 0,7%).

### I. Chỉ báo và tín hiệu (spec §3)
- [x] **I1** Registry + phiếu cho **mọi** chỉ báo ở Phụ lục A (kể cả không triển khai được).
  - Xong khi: `python -m kh.ind indicators --list` in số chỉ báo = số tên trong Phụ lục A; `docs/ind/indicator_cards.md` sinh tự động.
- [x] **I2** Triển khai chỉ báo + tín hiệu directional/filter + bộ lọc HTF.
  - Xong khi: `pytest -q tests/test_lookahead.py` qua cho mọi chỉ báo đã triển khai (20 thời điểm ngẫu nhiên/chỉ báo); đối chiếu ≥ 10 chỉ báo phổ biến (EMA, RSI, MACD, ATR, BB, Stoch, ADX, SuperTrend, OBV, VWAP) với một thư viện độc lập, sai số < 1e-4 sau giai đoạn khởi động, kết quả ghi trong phiếu.

### S. Chấm đơn lẻ (spec §4)
- [x] **S1** Bảng A đơn lẻ (Train), có/không HTF, từng symbol + tổng hợp, kèm precision ngẫu nhiên.
  - Xong khi: `reports/ind/single_tableA.csv` có số dòng = số chỉ báo triển khai × 5 symbol × 2 (HTF); không ô nào bịa (ô trống = NaN có lý do).
- [x] **S2** Backtest baseline đơn lẻ (Train), kịch bản phí/trượt giá.
  - Xong khi: `pytest -q tests/test_backtest.py` qua (gồm: vào lệnh ở open nến sau; TP+SL cùng nến → SL; phí tính 2 chiều; không vào lệnh trong filler); `reports/ind/single_tableB.csv` có đủ cột ở spec §4.

### C + W. Tổ hợp và walk-forward (spec §5–6)
- [x] **C1** Chọn 20 ứng viên (16 D + 4 F) theo điểm chốt trước, loại trùng tương quan > 0,8.
  - Xong khi: `reports/ind/candidates.csv` có 20 dòng + điểm từng tiêu chí.
- [x] **C2** Quét tổ hợp 2–4 × có/không HTF, Bảng A tổ hợp, top 50.
  - Xong khi: `reports/ind/trials.csv` ghi tổng số lần thử thật; `combos_tableA.csv` có top 50 thoả precision ≥ 1,5 × ngẫu nhiên.
- [x] **W1** Walk-forward (train mở rộng ≥ 6 tháng, kiểm tra 1 tháng, embargo 1 ngày) cho top 50 → Bảng B, DSR, PBO, CI bootstrap, leave-one-coin-out, độ nhạy ±20%.
  - Xong khi: `pytest -q tests/test_walkforward.py` qua (không fold nào có test chồng train, embargo đúng 1 ngày); `combos_tableB.csv` + `top10.md` có đủ cột ở spec §8.

### F. Chiến lược cuối (spec §7) — **dừng hỏi trước khi chạy test khoá**
- [x] **F1** Viết `docs/ind/strategy.md`, ghi chiến lược chọn + hash commit vào `CHANGELOG.md`, **hỏi chủ repo duyệt**.
  - Xong khi: chủ repo trả lời đồng ý trong PR hoặc chat.
- [~] **F2** ~~Chạy test khoá đúng 1 lần~~, viết `docs/ind/conclusion.md`. **Bỏ phần test khoá** theo quyết định chủ repo (phương án 2, 2026-10-10): bằng chứng chọn chiến lược quá yếu, không chạy chiến lược chỉ báo nào trên tập test. `docs/ind/conclusion.md` đã viết.
  - Xong khi (đã đổi theo quyết định chủ repo): conclusion tách [F]/[I]/[A]/[L]; không có `final_test.json` vì test khoá không mở.

## Log bằng chứng
<!-- Mỗi dòng: YYYY-MM-DD · mã việc · lệnh · kết quả chính -->
- 2026-10-09 · K1 · `pip install -e . && python -m kh.ind --help && pytest -q` · cài OK, CLI in 6 bước (data, labels, indicators, single, combos, final), 20 passed · PR nháp https://github.com/hytmk2912/Kh/pull/5
- 2026-10-09 · D1 · `python -m kh.ind data` (lần 1) · 280 file tải mới, 215,0 MB, 127 s, 0 lỗi [F]
- 2026-10-09 · D1 · `python -m kh.ind data` (lần 2) · "0 file tải mới; 280 file trong manifest; 0 file lỗi"; manifest: 5 × 32 klines (24 tháng + 8 ngày) + 5 × 24 funding (tháng), tất cả `verified` [F]. Funding 2026-10 chưa có trên server (đúng như spec §1, [L])
- 2026-10-09 · D2 · `python -m kh.ind data && pytest -q tests/test_data.py` · 6 passed; mỗi symbol M1 1.051.200 / M15 70.080 / H1 17.520, thiếu 0, trùng 0, OHLC sai 0, không hữu hạn 0; filler BTC 126 / ETH 127 / BNB 128 / SOL 128 / XRP 127 [F]; funding 2.166 bản ghi/symbol, cuối 2026-09-30 16:00 [F]; tick suy ra BTC 0,1 · ETH 0,01 · BNB 0,01 · SOL 0,001 · XRP 0,0001 [I] → `reports/ind/data_quality.json`, `tick_size.json`
- 2026-10-09 · L1 · `pytest -q tests/test_labels.py && python -m kh.ind labels` · 5 passed (chuỗi giá có đáp án biết trước, filler, đi ngang/nhịp hồi, module tín hiệu không import nhãn); `waves_stats.json` đủ 5 symbol × 3 ngưỡng; sóng 0,5% nhanh tăng/giảm (train+val): BTC 4.268/4.023 · ETH 11.392/11.120 · BNB 5.910/5.687 · SOL 16.662/16.451 · XRP 18.462/18.183 [F]; tỷ lệ nến ĐI NGANG BTC 85,0% · ETH 63,7% · BNB 79,2% · SOL 48,6% · XRP 54,3% [F]
- 2026-10-09 · I1 · `python -m kh.ind indicators --list && pytest -q tests/test_registry.py` · in 101 chỉ báo = 101 tên Phụ lục A (test so khớp đúng tên và thứ tự), 2 không triển khai (Volatility Region, Sure Thing); `docs/ind/indicator_cards.md` sinh tự động
- 2026-10-09 · I2 · `pytest -q tests/test_lookahead.py` · 103 passed: 99 chỉ báo × 20 thời điểm ngẫu nhiên (giá trị + tín hiệu khớp khi tính trên data[:t+1]) + bộ lọc HTF; thử cài một chỉ báo rò rỉ (SMA căn giữa) → test phát hiện
- 2026-10-09 · I2 · `python tools/ind_crosscheck.py --pandas-ta-python <venv>` (BTCUSDT M1 thật, 30.000 nến, bỏ 2.000 khởi động, ngưỡng 1e-4) · khớp 25 chỉ báo, gồm đủ 10 bắt buộc: EMA 6,6e-16 · RSI 1,1e-15 · MACD 2,7e-12 · ATR 4,3e-15 · BB 5,0e-08 · Stoch 2,3e-14 · ADX 2,8e-15 · SuperTrend 2,2e-16 (talipp, hướng trùng 100%) · OBV 9,3e-14 · VWAP 0 (pandas-ta); không khớp chỉ để tham khảo: CMO (TA-Lib khác định nghĩa TradingView), SuperTrend vs pandas-ta, SAR vs talipp → `reports/ind/indicator_crosscheck.json`, kết quả in trong phiếu
- 2026-10-09 · I2 · `python -m kh.ind indicators` · 99 chỉ báo × 5 symbol, 122 s; HTF cho phép long 38–43% / short 38–43% số nến [F]; Envelopes (mặc định 10%) 0 tín hiệu trên BTC [F] → `reports/ind/signal_summary.json`
- 2026-10-09 · S1 · `python -m kh.ind single && pytest -q tests/test_score.py` · `single_tableA.csv` 990 dòng = 99 chỉ báo × 5 symbol × 2 (HTF); 0 ô NaN thiếu lý do; precision ngẫu nhiên ≈ 0,40 [F]; lift Long trung vị cao nhất (n đủ lớn): Zig Zag 1,33–1,34 · Keltner 1,33 · Donchian 1,31–1,33 [F]; recall sóng nhanh cao nhất Connors RSI 0,85 nhưng lift 1,05 [F]; Envelopes lift 2,5 chỉ từ vài tín hiệu (mẫu quá nhỏ) [I]; filter lift cao nhất ATR 1,34 [F]; `trials.csv` 198 lần thử
- 2026-10-09 · S2 · `pytest -q tests/test_backtest.py && python -m kh.ind single` · 10 passed (vào ở open nến sau; TP+SL cùng nến → SL; phí 2 chiều; không vào lệnh trong filler/30′ sau; thoát khi tín hiệu ngược; trượt giá theo tick); `single_tableB.csv` 790 dòng (79 directional × 5 × 2 HTF; filter không backtest riêng vì không có hướng) đủ cột spec §4; 0/158 cấu hình có expectancy ròng trung vị > 0; kỳ vọng gộp trung vị +0,0012%/lệnh, ròng trung vị −0,10%/lệnh (baseline), −0,04% (phí 0,02%), −0,14% (phí 0,07%) [F] → `single_tableB_summary.csv`, `single_tableB_sensitivity.csv`
- 2026-10-09 · C1 · `python -m kh.ind combos` (bước chọn ứng viên) · `candidates.csv` 20 dòng (16 D + 4 F) kèm điểm từng tiêu chí; D (thứ tự): Zig Zag, Chande Kroll Stop, Williams Fractal, Standard Error Bands, Donchian, Bollinger, Keltner, SuperTrend, Parabolic SAR, 52-Week High/Low, MA Channel, Price Channel, Awesome Osc., TRIX, Adaptive MA, Average Price; F: ATR, O-H-L-C Volatility, Standard Error, Non-Directional C2C (tương quan lớn nhất với ứng viên đã chọn ≤ 0,80) [F]; quy tắc chốt trước trong CHANGELOG
- 2026-10-09 · C2 · `python -m kh.ind combos` (quét) · 6.164 tổ hợp hợp lệ × 2 HTF = 12.328 lần thử, 220 s; `trials.csv` tổng 13.948 lần thử thật (S1 198 + S2 1.422 + C2 12.328) [F]; chỉ **30** tổ hợp đạt precision ≥ 1,5× ngẫu nhiên (cả Long và Short, trung vị 5 symbol) → `combos_tableA.csv` có 30 dòng (không đủ 50; KHÔNG hạ ngưỡng vì đó là tiêu chí chủ repo chọn) [F]; cả 30 có rất ít tín hiệu (trung vị 1–52/symbol trong 14 tháng, 0 tổ hợp đạt điều kiện mà có ≥ 100 tín hiệu mỗi chiều), recall sóng nhanh ≤ 0,2% [F]; thêm cột thông tin p binomial gộp 5 symbol (chưa điều chỉnh multiple testing): 11/30 có p < 0,05 cả hai chiều [F]
- 2026-10-09 · W1 · `python -m kh.ind combos --part w1 && pytest -q tests/test_walkforward.py` · 1 passed (không fold nào chồng train, embargo đúng 1 ngày, không chạm test khoá); 13 fold (kiểm tra 2025-05 → 2026-05), 3.209 s; 242 tổ hợp được đánh giá ngoài mẫu; tổng số lần thử 176.786 [F]; PBO 0,504 [F]; 34/242 có expectancy ròng > 0 nhưng **tất cả chỉ 1–25 lệnh** (trung vị 5), 0 tổ hợp có ≥ 30 lệnh mà lãi [F]; DSR lớn nhất 0,0003 (không tổ hợp nào gần 0,95) [F]; gộp mọi lệnh ngoài mẫu: gộp phí +0,005%/lệnh, ròng −0,098%/lệnh [F]; top 1 Bảng B: SuperTrend + 52-Week High/Low + TRIX + Connors RSI (HTF) — 1 lệnh, +0,35% [F]; train của top 10 đều âm (−0,03 → −0,10%), ±20% tham số đổi dấu ở 8/10 [F] → `combos_tableB.csv` (62 cột), `top10.md`, `wf/summary.json`
- 2026-10-10 · F1 · chủ repo trả lời trong chat: chọn **phương án 2** (không mở test khoá) · ghi CHANGELOG
- 2026-10-10 · F2 · bỏ chạy test khoá (quyết định chủ repo); viết `docs/ind/conclusion.md` tách [F]/[I]/[A]/[L] + mục chưa kiểm chứng; `python -m kh.ind final` từ chối chạy kèm lý do

## Ghi chú phiên
<!-- Việc đang làm dở, file đang sửa, vấn đề chưa giải quyết. Cập nhật trước khi hết phiên. -->
- Nhánh `ind-scalp` = `ind-scalp-setup` (PR #4) + merge `phase-0` (PR #2, chưa merge vào master) để dùng lại `src/kh/data` (tải Binance Vision có SHA256/retry), `src/kh/backtest`, `src/kh/evaluation`. Code riêng của track nằm ở `src/kh/ind/`.
- C2: Bảng A tổ hợp chỉ có 30 dòng đạt điều kiện → W1 chạy walk-forward cho 30 tổ hợp này ("top 50" = tối đa 50). Kết quả chi tiết theo symbol: `data/ind/combos_train_by_symbol.parquet` (không commit), tổng hợp mọi tổ hợp: `reports/ind/combos_tableA_all.csv.gz`.
- W1 xong. Kết quả chọn từng fold lưu ở `data/ind/wf/foldNN/` (không commit) → chạy lại `--part w1` dùng lại cache, chỉ tính lại Bảng B + độ bền.
- Track M1 đã đóng (2026-10-10): kết luận "không có chiến lược lãi sau phí đáng tin"; test khoá chưa mở. Việc tiếp theo ở track M15 (nhánh `ind15`, `TASKS_M15.md`).
- Ngày trong log theo UTC (đồng hồ container).
- Đối chiếu chỉ báo cần môi trường riêng: `python -m venv /tmp/xenv && /tmp/xenv/bin/pip install pandas-ta talipp pyarrow`, rồi `python tools/ind_crosscheck.py --pandas-ta-python /tmp/xenv/bin/python`.
- Dữ liệu: đặt `KH_DATA_DIR` (mặc định `data/` trong repo, đã gitignore). Phiên mới phải chạy lại `python -m kh.ind data`.
