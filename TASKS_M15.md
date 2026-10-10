# TASKS_M15.md — Track M15: vào lệnh khung M15 bằng tổ hợp chỉ báo

Quy tắc: làm việc `[ ]` đầu tiên. Chỉ đổi sang `[x]` khi lệnh ở "Xong khi" chạy qua **và** đã dán kết quả vào mục Log.
Đặc tả: `docs/ind15/spec.md`. Quy tắc chung: `CLAUDE.md`. Nhánh: `ind15`.

## Việc

### N0. Chuẩn bị
- [x] **N0** Tham số hoá khung thời gian trong code track M1 (`tf=1m|15m`) thay vì chép code; thêm resample H4; CLI `python -m kh.ind15 <bước>` (data, labels, indicators, single, combos, final).
  - Xong khi: `pytest -q` qua toàn bộ test cũ + mới; chạy lại `python -m kh.ind single --symbols BTCUSDT` cho ra `single_tableA.csv` phần BTC **giống hệt** bản đã commit (so SHA256 hoặc so từng ô) → code M1 không bị đổi kết quả; mỗi symbol M15 70.080 / H1 17.520 / H4 4.380 nến.

### N1. Nhãn sóng M15 (spec §1)
- [x] **N1** ZigZag 1,5% trên M15, sóng nhanh ≤ 8 giờ, đi ngang ≥ 8 giờ < 1,5%, nhịp hồi 0,6%.
  - Xong khi: `pytest -q tests/test_labels.py` qua với ca M15 (chuỗi giá tự tạo có đáp án biết trước); `reports/ind15/waves_stats.json` đủ 5 symbol × 3 ngưỡng (1,0 / 1,5 / 2,0%), chỉ train + validation.

### N2. Chỉ báo M15 (spec §3)
- [x] **N2** 99 chỉ báo trên M15 (dạng sự kiện + dạng trạng thái), quy đổi tham số "1 ngày" = 96 nến, HTF H1 + H4.
  - Xong khi: `pytest -q tests/test_lookahead.py` qua cho mọi chỉ báo trên M15, cả dạng sự kiện và trạng thái, cùng H1/H4; `reports/ind15/signal_summary.json` có số tín hiệu mỗi chỉ báo × symbol; mọi tham số quy đổi đã ghi CHANGELOG.

### N3. Chấm đơn lẻ (spec §4)
- [x] **N3** Bảng A + Bảng B đơn lẻ trên train, có/không HTF, mô phỏng thoát lệnh trên đường giá M1.
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
- 2026-10-10 · N0 · `pytest -q` · 140 passed (135 cũ + 5 mới ở `tests/test_track.py`: tham số Track, H4, ngữ cảnh quy đổi tham số, HTF trên nến M15 = bản M1 tại phút đóng nến, HTF M15 không nhìn tương lai)
- 2026-10-10 · N0 · `python -m kh.ind labels/indicators/single --symbols BTCUSDT` (code mới) so với bản đã commit · `single_tableA.csv` phần BTC 198 dòng × 35 cột **giống hệt từng ô** (SHA256 e6ba0617… = e6ba0617…); `single_tableB.csv` 158 dòng và `single_tableB_sensitivity.csv` 1.422 dòng giống hệt; Parquet tín hiệu + nhãn + sóng BTC giống hệt; `trials.csv` không đổi → code M1 không đổi kết quả (đã khôi phục file báo cáo 5 symbol sau khi so)
- 2026-10-10 · N0 · `python -m kh.ind15 data` · manifest 280 file, 0 tải mới, 0 lỗi; mỗi symbol M15 70.080 / H1 17.520 / H4 4.380 nến, 0 nến thiếu nến con [F]; nến M15 có filler: BTC 13, ETH/BNB/SOL/XRP 14 [F] → `reports/ind15/data_quality.json`
- 2026-10-10 · N1 · `pytest -q tests/test_labels.py && python -m kh.ind15 labels` · 7 passed (gồm 2 ca M15 chuỗi giá tự tạo: sóng nhanh 1,6%/10 nến, sóng chậm 1,6%/40 nến, đi ngang 40 nến, nhịp hồi 0,7% trong sóng giảm, UNKNOWN = filler + 2 nến); `waves_stats.json` 5 symbol × 3 ngưỡng (1,0 / 1,5 / 2,0%), train + validation; sóng 1,5% nhanh tăng/giảm: BTC 681/668 · ETH 1.593/1.578 · BNB 913/900 · SOL 2.069/2.065 · XRP 2.195/2.199 [F]; sóng chậm rất ít (BTC 78/91, SOL 15/18) [F]; tỷ lệ nến ĐI NGANG ở 1,5%: BTC 71,6% · ETH 35,1% · BNB 59,1% · SOL 20,9% · XRP 32,0% [F]
- 2026-10-10 · N2 · `pytest -q tests/test_lookahead.py` · 203 passed: 99 chỉ báo × 20 thời điểm trên M1 (cũ) + 99 chỉ báo × 20 thời điểm trên M15 (giá trị + sự kiện + trạng thái) + chỉ báo theo ngày có tín hiệu trên M15; HTF H1/H4 trên M15 ở `tests/test_track.py` (khớp bản M1 tại phút đóng nến, không nhìn tương lai); toàn bộ `pytest -q` 242 passed
- 2026-10-10 · N2 · `python -m kh.ind15 indicators` · 99 chỉ báo × 5 symbol, 79 directional có thêm cột trạng thái (178 cột), 9 s; HTF H1+H4 cho phép long 35,8–44,7% / short 36,4–45,3% số nến [F]; trung vị số sự kiện/symbol trên cả cửa sổ: thấp nhất Envelopes 3, TRIX 1.428, SuperTrend 1.605; trung vị các chỉ báo 8.199 [F] → `reports/ind15/signal_summary.json`; tham số quy đổi: CHANGELOG + `docs/ind15/indicator_params.md`; M1 BTC: Multi-Timeframe MA và HTF giống hệt bản cũ sau khi sửa `htf_closed`
- 2026-10-10 · N3 · `pytest -q tests/test_backtest.py` · 15 passed (5 ca M15 mới: vào ở open nến M15 sau; TP/SL kiểm từng nến M1; TP+SL cùng nến M1 → SL; hết 32 nến M15 → đóng ở close nến M1 cuối, giữ 480 phút; tín hiệu ngược → thoát ở open nến M15 sau; funding đúng mốc trong (vào, ra]; không vào nến M15 có filler và 2 nến sau)
- 2026-10-10 · N3 · `python -m kh.ind15 single` (344 s) · `single_tableA.csv` 990 dòng = 99 × 5 symbol × 2 HTF, 0 ô NaN thiếu lý do; precision ngẫu nhiên trung vị 0,42 [F]; lift trung bình Long/Short cao nhất (≥ 100 tín hiệu mỗi chiều): SuperTrend+HTF 1,43 · Bollinger+HTF 1,42 · Donchian+HTF 1,41 · 52-Week High/Low 1,40 [F]. `single_tableB.csv` 790 dòng (79 directional × 5 × 2), `single_tableB_sensitivity.csv` 7.110 dòng (9 kịch bản), `single_tableB_summary.csv` có cột gross/lệnh: **0/158** cấu hình có expectancy ròng trung vị > 0; 125/158 có gross trung vị > 0; gross trung vị +0,011%/lệnh (M1: +0,0012%), ròng trung vị −0,093%/lệnh; tốt nhất SuperTrend+HTF gross +0,081%, ròng −0,020% (2/5 symbol dương) [F]; ròng trung vị theo kịch bản: phí 0,02% −0,034% · phí 0,07% −0,134% · không funding −0,094% · TP 1,8% −0,092% · slip 3 tick −0,099% [F]

## Ghi chú phiên
<!-- Việc đang làm dở, file đang sửa, vấn đề chưa giải quyết. Cập nhật trước khi hết phiên. -->
- Code: `src/kh/ind/track.py` (`M1`, `M15`) — mọi hàm track M1 nhận `tr`, mặc định `M1`. CLI `python -m kh.ind15 <bước>` gọi cùng code với `M15`. Kết quả M15: `reports/ind15/`, trung gian `data/ind15/`.
- Chạy lại kiểm tra M1 không đổi: `python -m kh.ind labels/indicators/single --symbols BTCUSDT`, so phần BTC với `git show HEAD:reports/ind/...`, rồi `git checkout -- reports/ind` (lệnh chạy 1 symbol ghi đè báo cáo 5 symbol).
