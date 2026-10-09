# Tổng kết nghiên cứu

Tài liệu sinh tự động từ các báo cáo thành phần. Mọi con số là kết quả backtest/thống kê lịch sử,
không phải lợi nhuận thực tế và không đảm bảo cho tương lai.

- Cửa sổ dữ liệu: 2024-10-09 → 2026-10-08 UTC; symbol: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Train 2024-10-09 → 2025-12-20; validation 2025-12-21 → 2026-05-15; final test 2026-05-16 → 2026-10-08.
- Số lần chạy thí nghiệm đã ghi trong registry: 5.

## 1. Dữ liệu

Tất cả tiêu chí chất lượng đạt: **True**. Nến thiếu: 0 ở mọi coin; nến filler (bảo trì sàn) được gắn cờ và loại khỏi tín hiệu.

## 2. Trạng thái giả thuyết đăng ký trước

| ID | Nội dung | Trạng thái | Bằng chứng chính |
|---|---|---|---|
| H1 | Theo sóng DC σ×4 có lãi trước phí | Không đạt | train 2.0 bps (p=0.415), val 14.8 bps (p=0.176); overshoot/θ ≈ 1.04 |
| H2 | Breakout/breakdown 240′ tiếp diễn | Không đạt | Δ tỷ lệ lên sau breakout: train -0.0214, val -0.0399 |
| H3 | Co hẹp biến động → biến động mạnh hơn | Không đạt | Δ biên độ/rào: train -0.229, val -0.235 (ngược giả thuyết nếu âm) |
| H4 | Đảo chiều ngắn hạn (return 15′) | Đạt (thống kê), chưa đủ để giao dịch | IC train -0.0282 (t=-8.9), val -0.0284 (t=-4.6) |
| H5 | Funding cực dương → giảm | Không đạt | IC train -0.0039 (t=-0.3), val -0.0161 (t=-0.9) |
| H6 | OI + giá → tiếp diễn | Không đạt | IC train 0.0001 (t=0.0), val 0.0112 (t=1.6) |
| H7 | Mất cân bằng taker dự báo return | Đạt (thống kê), chưa đủ để giao dịch | IC train -0.0237 (t=-8.3), val -0.0272 (t=-5.7) |
| H8 (H=60) | LightGBM có skill > 0 walk-forward | Không đạt | skill TB 0.00010, t=0.15, coin > 0: 2/5 |
| H8 (H=240) | LightGBM có skill > 0 walk-forward | Không đạt | skill TB -0.00567, t=-2.39, coin > 0: 0/5 |

## 3. Quét exploratory

- 900 kiểm định đơn biến + 90 tổ hợp; qua FDR train (ALL): 52; qua cả validation và ≥ 3/5 coin: 40; tổ hợp qua FDR + validation: 7.
- Ngưỡng xác suất thắng hòa vốn: H=60: 0.619, H=240: 0.559.
- Không quy luật đơn biến nào có decile cực trị vượt ngưỡng hòa vốn trên validation 

## 4. Chiến lược trên validation (sau chi phí)

| Biến thể | Lệnh | Ròng USD | Cháy TK | Sharpe | PF | Exp ròng bps | Exp trước chi phí bps | DSR | Chọn |
|---|---|---|---|---|---|---|---|---|---|
| lgbm_H60_tau0.55 | 4441 | -29879 | CÓ | -15.11 | 0.53 | -11.8 | 2.2 | 0.000 | False |
| lgbm_H60_tau0.6 | 170 | -269 | không | -0.99 | 0.89 | -1.3 | 12.7 | 0.000 | False |
| lgbm_H60_tau0.65 | 8 | 71 | không | 2.21 | 2.32 | 23.4 | 37.0 | 0.000 | False |
| lgbm_H240_tau0.55 | 2992 | -16583 | CÓ | -8.34 | 0.70 | -12.7 | 1.3 | 0.000 | False |
| lgbm_H240_tau0.6 | 609 | -1437 | không | -1.86 | 0.86 | -0.2 | 13.8 | 0.000 | False |
| lgbm_H240_tau0.65 | 77 | 120 | không | 0.53 | 1.11 | 11.8 | 25.9 | 0.000 | False |
| rev_ret_15_z_H60 | 10275 | -82054 | CÓ | -23.18 | 0.52 | -13.7 | 0.3 | 0.000 | False |
| rev_ret_15_z_H240 | 4623 | -31201 | CÓ | -11.42 | 0.68 | -14.5 | -0.5 | 0.000 | False |
| rev_taker_imb_15_H60 | 9723 | -77703 | CÓ | -38.16 | 0.42 | -13.5 | 0.5 | 0.000 | False |
| rev_taker_imb_15_H240 | 4193 | -25910 | CÓ | -16.08 | 0.66 | -13.1 | 0.9 | 0.000 | False |
| rev_rsi_14_H60 | 9951 | -84273 | CÓ | -31.04 | 0.46 | -14.7 | -0.7 | 0.000 | False |
| rev_rsi_14_H240 | 4657 | -32669 | CÓ | -13.96 | 0.65 | -15.5 | -1.5 | 0.000 | False |
| dc_sig4 | 515 | -601 | không | -0.58 | 0.94 | 1.7 | 15.7 | 0.000 | False |
| dc_sig8 | 147 | -305 | không | -0.47 | 0.89 | 2.9 | 18.2 | 0.000 | False |

PBO = 0.000. Được chọn vào final test: **không có**.

## 5. Final test

Chưa chạy.


## 6. Kết luận

- Không có quy luật hay chiến lược nào đạt tiêu chí đã đăng ký trước để được coi là có lợi thế sau chi phí.
- Có hiệu ứng đảo chiều ngắn hạn (H4, H7) ổn định về mặt thống kê ở cả 5 coin, nhưng quá nhỏ (≈ 0–1 bps/lệnh trước chi phí)
  so với chi phí khứ hồi ≈ 14 bps khi khớp lệnh taker.
- Mô hình LightGBM ở ngưỡng tự tin cao có edge trước chi phí ≈ 13 bps/lệnh, vượt baseline ngẫu nhiên trên validation,
  nhưng vẫn bị chi phí xóa sạch; log-loss skill gần 0 và không ổn định theo fold.
- Các khẳng định phổ biến như Fibonacci, breakout tiếp diễn, co hẹp → bùng nổ không được dữ liệu ủng hộ ở khung 1 phút–4 giờ.

### Hướng nghiên cứu tiếp theo (cần đăng ký giả thuyết mới, dùng dữ liệu forward sau 2026-10-08)
- Giảm chi phí: mô phỏng lệnh maker (phí 0,02%, không slippage nhưng có rủi ro không khớp) — cần dữ liệu aggTrades/bookDepth.
- Khung thời gian dài hơn (4h–1 ngày) nơi chi phí nhỏ hơn so với biên độ di chuyển.
- Forward holdout: chạy lại chính các biến thể đã khóa trên dữ liệu mới sau ≥ 3 tháng, không chỉnh sửa.

## 7. Giới hạn chính

- 2 năm dữ liệu, 5 coin vốn hóa lớn tương quan cao; final test 146 ngày có thể chỉ chứa một vài chế độ thị trường.
- Không có dữ liệu spread lịch sử; slippage là giả định (2 bps/chiều, kiểm tra thêm ×3).
- Phí giả định VIP0 taker 0,05%; tài khoản thật có thể khác.
- Thứ tự giá trong nến 1 phút không biết → TP/SL cùng nến tính là SL (thận trọng).
- Không mô phỏng sổ lệnh, độ trễ mạng, thanh lý theo mark price; đường vốn tính theo lệnh đã đóng.
- Funding tháng 10/2026 chưa được Binance công bố tại thời điểm chạy → ước tính bằng mức cuối cùng.
- Một lỗi phương pháp (IC trong ngày) đã được phát hiện và sửa; xem nhật ký thay đổi trong docs/hypotheses.md.
