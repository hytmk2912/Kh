# Top 10 tổ hợp M15 — walk-forward ngoài mẫu (Bảng B)

Walk-forward lồng nhau: 13 fold, train mở rộng từ 2024-10-09 (≥ 6 tháng), kiểm tra từng tháng 2025-05 → 2026-05, embargo 1 ngày. Trong mỗi fold: Bảng A đơn lẻ, chọn 10 D + 3 F, quét tổ hợp kích hoạt + xác nhận chỉ trên train; top ≤ 30 (≥ 30 tín hiệu/symbol, precision ≥ 1,2× ngẫu nhiên, xếp theo recall sóng nhanh) được backtest baseline trên tháng kiểm tra.
Baseline: tín hiệu khi nến M15 đóng, vào ở open nến M15 sau; TP 1,2% / SL 0,8% [A] kiểm trên từng nến M1; giữ ≤ 8 giờ; phí taker 0,05%/chiều [A]; trượt 1 tick/chiều [A]; funding thật.

- Số lần thử track M15 (dùng cho DSR): **29,394**; cộng M1: 206,180
- PBO (CSCV 16 khối, mọi tổ hợp được đánh giá ngoài mẫu): **0.311**
- Tổ hợp được đánh giá ngoài mẫu: **97**, tổng 252,687 lệnh; gộp: gross 0.0161%/lệnh, ròng **-0.0871%/lệnh**
- Đạt từng tiêu chí §6: ≥ 100 lệnh ngoài mẫu: 97 · expectancy ròng > 0 và cận dưới CI95 > 0: 0 · DSR ≥ 0,95 (lần thử track M15): 0 · expectancy > 0 ở ≥ 3/5 symbol: 3 · không đổi dấu khi tham số × 0,8 / × 1,2: 7 → **đạt cả 5: 0**

| # | Tổ hợp | HTF | Fold chọn | Lệnh | Win | Exp ròng %/lệnh | CI95 | Exp gộp % | PF | MaxDD % | Symbol dương | DSR | DSR (M1+M15) | 1 | 2 | 3 | 4 | 5 | Đạt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Chande Kroll Stop (kích hoạt) + Average Price (xác nhận) + Donchian Channels (xác nhận) | không | 1 | 628 | 0.476 | 0.0476 | [-0.0470, 0.1557] | 0.1510 | 1.11 | 30.49 | 3/5 | 0.001 | 0.000 | ✓ | ✗ | ✗ | ✓ | ✗ | **✗** |
| 2 | Chande Kroll Stop (kích hoạt) + Bollinger Bands (xác nhận) + Average Price (xác nhận) | không | 1 | 635 | 0.460 | 0.0364 | [-0.0623, 0.1398] | 0.1397 | 1.09 | 29.44 | 3/5 | 0.000 | 0.000 | ✓ | ✗ | ✗ | ✓ | ✗ | **✗** |
| 3 | Chande Kroll Stop (kích hoạt) + Average Price (xác nhận) + SuperTrend (xác nhận) | không | 1 | 668 | 0.458 | 0.0127 | [-0.0861, 0.1235] | 0.1159 | 1.03 | 34.07 | 3/5 | 0.000 | 0.000 | ✓ | ✗ | ✗ | ✓ | ✗ | **✗** |
| 4 | Zig Zag (kích hoạt) + Chande Kroll Stop (xác nhận) | không | 5 | 1515 | 0.445 | -0.0255 | [-0.0911, 0.0336] | 0.0776 | 0.95 | 65.89 | 2/5 | 0.000 | 0.000 | ✓ | ✗ | ✗ | ✗ | ✓ | **✗** |
| 5 | Zig Zag (kích hoạt) + Williams Fractal (xác nhận) | không | 4 | 1000 | 0.431 | -0.0425 | [-0.1121, 0.0254] | 0.0608 | 0.91 | 59.34 | 2/5 | 0.000 | 0.000 | ✓ | ✗ | ✗ | ✗ | ✓ | **✗** |
| 6 | Chande Kroll Stop (kích hoạt) + Zig Zag (xác nhận) + Average Price (xác nhận) | không | 2 | 1474 | 0.429 | -0.0456 | [-0.0985, 0.0123] | 0.0573 | 0.90 | 88.70 | 0/5 | 0.000 | 0.000 | ✓ | ✗ | ✗ | ✗ | ✓ | **✗** |
| 7 | SMA (kích hoạt) + Williams %R (xác nhận) | không | 1 | 937 | 0.333 | -0.0458 | [-0.1010, 0.0155] | 0.0571 | 0.87 | 65.16 | 1/5 | 0.000 | 0.000 | ✓ | ✗ | ✗ | ✗ | ✓ | **✗** |
| 8 | Chande Kroll Stop (kích hoạt) + Williams Fractal (xác nhận) + Average Price (xác nhận) | không | 2 | 1588 | 0.399 | -0.0527 | [-0.1103, 0.0075] | 0.0501 | 0.88 | 87.94 | 0/5 | 0.000 | 0.000 | ✓ | ✗ | ✗ | ✗ | ✓ | **✗** |
| 9 | Williams Fractal (kích hoạt) + Median Price (xác nhận) + Parabolic SAR (xác nhận) | không | 2 | 1288 | 0.384 | -0.0545 | [-0.1122, 0.0052] | 0.0481 | 0.87 | 103.21 | 0/5 | 0.000 | 0.000 | ✓ | ✗ | ✗ | ✗ | ✓ | **✗** |
| 10 | Chande Kroll Stop (kích hoạt) + Standard Error Bands (xác nhận) + Average Price (xác nhận) | không | 2 | 1541 | 0.392 | -0.0562 | [-0.1138, 0.0031] | 0.0465 | 0.87 | 90.43 | 1/5 | 0.000 | 0.000 | ✓ | ✗ | ✗ | ✗ | ✓ | **✗** |

## Theo symbol, chế độ biến động, train, leave-one-coin-out, độ nhạy ±20% (expectancy ròng %/lệnh)

| # | BTCUSDT | ETHUSDT | BNBUSDT | SOLUSDT | XRPUSDT | Biến động thấp | vừa | cao | Train | LOCO BTC | LOCO ETH | LOCO BNB | LOCO SOL | LOCO XRP | ×0,8 | ×1,2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | -0.0020 | 0.1283 | 0.1319 | 0.0078 | -0.0236 | -0.0383 | 0.1277 | 0.0292 | -0.0673 | -0.0020 | 0.1283 | 0.1319 | 0.0078 | -0.0236 | -0.0058 | 0.0498 |
| 2 | -0.1152 | 0.1257 | 0.1046 | -0.0024 | 0.0277 | -0.0208 | 0.1001 | 0.0148 | -0.0671 | -0.1152 |  | 0.1046 | -0.0024 | 0.0277 | -0.0090 | 0.0080 |
| 3 | -0.1319 | 0.0901 | 0.0215 | 0.0392 | -0.0144 | -0.0289 | 0.0532 | 0.0064 | -0.0677 | -0.1319 | 0.0901 | 0.0215 | 0.0392 | -0.0144 | -0.0044 | 0.0077 |
| 4 | 0.0022 | -0.0092 | -0.0079 | -0.0956 | 0.0132 | -0.0519 | -0.0185 | -0.0122 | -0.0369 | -0.0269 | -0.0092 | -0.0675 | -0.1699 | 0.1078 | -0.0412 | -0.0542 |
| 5 | -0.0492 | -0.1137 | 0.0881 | -0.1032 | 0.0340 | -0.0533 | -0.0086 | -0.0727 | -0.0499 | -0.0488 | -0.0819 | 0.0455 | -0.0220 | -0.0294 | -0.0668 | -0.0291 |
| 6 | -0.1065 | -0.0169 | -0.0413 | -0.0520 | -0.0397 | -0.0575 | -0.0465 | -0.0368 | -0.0647 | -0.1065 | -0.0169 | -0.0413 | -0.0520 | -0.0397 | -0.0973 | -0.0400 |
| 7 | -0.0495 | -0.0598 | 0.0038 | -0.0923 | -0.0220 | -0.0738 | 0.0022 | -0.0597 | -0.0851 | -0.0495 | -0.0598 | 0.0038 | -0.0923 | -0.0220 | -0.0756 | -0.0520 |
| 8 | -0.0981 | -0.0490 | -0.0928 | -0.0263 | -0.0265 | -0.0886 | -0.0330 | -0.0464 | -0.0815 | -0.0981 | -0.0490 | -0.0928 | -0.0263 | -0.0265 | -0.0772 | -0.0509 |
| 9 | -0.0803 | -0.0492 | -0.0424 | -0.0385 | -0.0688 | -0.0290 | -0.1186 | -0.0033 | -0.0913 | -0.0803 | -0.0492 | -0.0424 | -0.0385 | -0.0688 | -0.0485 | -0.0421 |
| 10 | -0.1700 | 0.0108 | -0.1290 | -0.0054 | -0.0522 | -0.0822 | -0.0438 | -0.0478 | -0.0824 | -0.1700 | 0.0108 | -0.1290 | -0.0054 | -0.0522 | -0.0714 | -0.0564 |

Tiêu chí §6 (chốt trước): 1. ≥ 100 lệnh ngoài mẫu · 2. expectancy ròng > 0 và cận dưới CI95 > 0 · 3. DSR ≥ 0,95 (lần thử track M15) · 4. expectancy > 0 ở ≥ 3/5 symbol · 5. không đổi dấu khi tham số × 0,8 / × 1,2.
Ô trống: CI95 khi < 10 lệnh; theo symbol/chế độ khi không có lệnh; LOCO khi bỏ coin đó ra thì tổ hợp không lọt top ở fold nào; ×0,8/×1,2 khi không có lệnh (tính là đổi dấu → không đạt tiêu chí 5).

Ghi chú: [F] số đo trên dữ liệu thật trong train + validation; chưa chạm giai đoạn test. Kết quả backtest không phải lợi nhuận thực tế.
