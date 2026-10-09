# Top 10 tổ hợp — walk-forward ngoài mẫu (Bảng B)

Walk-forward lồng nhau: 13 fold, train mở rộng từ 2024-10-09 (≥ 6 tháng), kiểm tra từng tháng 2025-05 → 2026-05, embargo 1 ngày. Trong mỗi fold: Bảng A đơn lẻ, 20 ứng viên, quét tổ hợp chỉ trên train; top ≤ 50 (precision ≥ 1,5× ngẫu nhiên, xếp theo recall sóng nhanh) được backtest baseline trên tháng kiểm tra.
Baseline: TP 0,45% / SL 0,30% [A], giữ ≤ 15 phút, phí taker 0,05%/chiều [A], trượt 1 tick/chiều [A], funding thật.

- Số lần thử tổng (trials.csv, dùng cho DSR): **176,786**
- PBO (CSCV 16 khối, mọi tổ hợp được đánh giá ngoài mẫu): **0.504**
- Tổ hợp được đánh giá ngoài mẫu: **242**; có expectancy ròng > 0: **34**

| # | Tổ hợp | HTF | Fold chọn | Lệnh | Win | Exp ròng %/lệnh | CI95 | Exp gộp % | PF | MaxDD % | Symbol dương | Sharpe năm | DSR |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | SuperTrend + 52-Week High/Low + TRIX + Connors RSI | có | 1 | 1 | 1.000 | 0.3478 | [, ] | 0.4500 | ∞ | 0.00 | 1/5 | 3.49 | 0.000 |
| 2 | Zig Zag + Williams Fractal + 52-Week High/Low + TRIX | không | 1 | 2 | 1.000 | 0.3449 | [, ] | 0.4500 | ∞ | 0.00 | 2/5 | 5.02 | 0.000 |
| 3 | 52-Week High/Low + TRIX + Average Price + Connors RSI | không | 1 | 1 | 1.000 | 0.2116 | [, ] | 0.3137 | ∞ | 0.00 | 1/5 | 3.43 | 0.000 |
| 4 | SuperTrend + 52-Week High/Low + TRIX + Adaptive MA | không | 4 | 4 | 0.750 | 0.1569 | [, ] | 0.2625 | 2.56 | 0.40 | 2/5 | 0.99 | 0.000 |
| 5 | SuperTrend + 52-Week High/Low + TRIX + Adaptive MA | có | 4 | 4 | 0.750 | 0.1569 | [, ] | 0.2625 | 2.56 | 0.40 | 2/5 | 0.99 | 0.000 |
| 6 | 52-Week High/Low + TRIX + Adaptive MA + Standard Error | có | 2 | 4 | 0.750 | 0.1569 | [, ] | 0.2625 | 2.56 | 0.40 | 2/5 | 1.41 | 0.000 |
| 7 | Parabolic SAR + 52-Week High/Low + TRIX | có | 1 | 2 | 0.500 | 0.1507 | [, ] | 0.2519 | 7.49 | 0.05 | 1/5 | 2.98 | 0.000 |
| 8 | 52-Week High/Low + Median Price + Adaptive MA + TRIX | không | 1 | 1 | 1.000 | 0.1306 | [, ] | 0.2309 | ∞ | 0.00 | 1/5 | 3.49 | 0.000 |
| 9 | Keltner Channels + Price Channel + TRIX + ATR | có | 1 | 6 | 0.667 | 0.0969 | [, ] | 0.1977 | 1.86 | 0.68 | 2/5 | 2.46 | 0.000 |
| 10 | 52-Week High/Low + TRIX + Median Price + Adaptive MA | không | 1 | 3 | 0.667 | 0.0937 | [, ] | 0.2000 | 1.70 | 0.40 | 2/5 | 1.26 | 0.000 |

## Theo symbol, chế độ biến động, train, leave-one-coin-out, độ nhạy ±20% (expectancy ròng %/lệnh)

| # | BTCUSDT | ETHUSDT | BNBUSDT | SOLUSDT | XRPUSDT | Biến động thấp | vừa | cao | Train | LOCO BTC | LOCO ETH | LOCO BNB | LOCO SOL | LOCO XRP | ×0,8 | ×1,2 | Đổi dấu |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 |  |  |  | 0.3478 |  | 0.3478 |  |  | -0.0414 |  |  |  |  |  | 0.2423 | 0.0499 | False |
| 2 |  |  | 0.3479 |  | 0.3418 |  | 0.3418 | 0.3479 | -0.0270 |  |  |  |  |  | -0.1033 | -0.0296 | True |
| 3 |  |  | 0.2116 |  |  |  |  | 0.2116 | -0.0722 |  |  |  |  |  | 0.0131 |  | False |
| 4 |  | 0.3488 | -0.0285 |  | 0.3358 |  |  | 0.1569 | -0.0633 |  | 0.3492 |  |  |  | -0.1425 |  | True |
| 5 |  | 0.3488 | -0.0285 |  | 0.3358 |  |  | 0.1569 | -0.0633 |  | 0.3492 |  |  |  | -0.1615 |  | True |
| 6 |  | 0.3488 | -0.0285 |  | 0.3358 |  |  | 0.1569 | -0.0939 |  |  |  |  |  | -0.1295 | 0.3465 | True |
| 7 | -0.0465 |  | 0.3479 |  |  |  |  | 0.1507 | -0.0892 |  |  |  | -0.4012 | 0.3419 | -0.3482 | -0.4004 | True |
| 8 | 0.1306 |  |  |  |  | 0.1306 |  |  | -0.0550 | 0.1306 |  |  |  |  | -0.4000 |  | True |
| 9 | -0.4000 | 0.2799 | 0.3485 | -0.2757 |  | -0.2757 | 0.2101 | 0.1617 | -0.1008 |  |  |  | -0.2757 |  | -0.0874 | -0.1929 | True |
| 10 |  | 0.3488 | -0.4034 |  | 0.3358 |  |  | 0.0937 | -0.0550 |  | 0.3488 |  |  |  | -0.2148 |  | True |

Ô trống: CI95 khi < 10 lệnh (bootstrap khối ngày không có nghĩa); PF = ∞ khi không có lệnh lỗ; theo symbol/chế độ khi không có lệnh; LOCO khi bỏ coin đó ra thì tổ hợp không lọt top ở fold nào hoặc không có lệnh trên coin bị bỏ; ×0,8/×1,2 khi không có lệnh.

## Vì sao các chỉ báo bổ trợ nhau

1. SuperTrend (xu hướng/kênh, tín hiệu) + 52-Week High/Low (xu hướng/kênh, tín hiệu) + TRIX (động lượng, tín hiệu) + Connors RSI (động lượng, tín hiệu) — nguồn thông tin: xu hướng, động lượng. Tín hiệu chỉ phát khi các nguồn khác nhau cùng đồng ý → ít lệnh, chọn lọc hơn. [I] Đây là giả thuyết; bằng chứng ngoài mẫu: 1 lệnh.
2. Zig Zag (xu hướng/kênh, tín hiệu) + Williams Fractal (xu hướng/kênh, tín hiệu) + 52-Week High/Low (xu hướng/kênh, tín hiệu) + TRIX (động lượng, tín hiệu) — nguồn thông tin: xu hướng, động lượng. Tín hiệu chỉ phát khi các nguồn khác nhau cùng đồng ý → ít lệnh, chọn lọc hơn. [I] Đây là giả thuyết; bằng chứng ngoài mẫu: 2 lệnh.
3. 52-Week High/Low (xu hướng/kênh, tín hiệu) + TRIX (động lượng, tín hiệu) + Average Price (giá/khác, tín hiệu) + Connors RSI (động lượng, tín hiệu) — nguồn thông tin: giá, xu hướng, động lượng. Tín hiệu chỉ phát khi các nguồn khác nhau cùng đồng ý → ít lệnh, chọn lọc hơn. [I] Đây là giả thuyết; bằng chứng ngoài mẫu: 1 lệnh.
4. SuperTrend (xu hướng/kênh, tín hiệu) + 52-Week High/Low (xu hướng/kênh, tín hiệu) + TRIX (động lượng, tín hiệu) + Adaptive MA (xu hướng (MA), tín hiệu) — nguồn thông tin: xu hướng, động lượng. Tín hiệu chỉ phát khi các nguồn khác nhau cùng đồng ý → ít lệnh, chọn lọc hơn. [I] Đây là giả thuyết; bằng chứng ngoài mẫu: 4 lệnh.
5. SuperTrend (xu hướng/kênh, tín hiệu) + 52-Week High/Low (xu hướng/kênh, tín hiệu) + TRIX (động lượng, tín hiệu) + Adaptive MA (xu hướng (MA), tín hiệu) — nguồn thông tin: xu hướng, động lượng. Tín hiệu chỉ phát khi các nguồn khác nhau cùng đồng ý → ít lệnh, chọn lọc hơn. [I] Đây là giả thuyết; bằng chứng ngoài mẫu: 4 lệnh.
6. 52-Week High/Low (xu hướng/kênh, tín hiệu) + TRIX (động lượng, tín hiệu) + Adaptive MA (xu hướng (MA), tín hiệu) + Standard Error (giá/khác, bộ lọc) — nguồn thông tin: giá, xu hướng, động lượng. Tín hiệu chỉ phát khi các nguồn khác nhau cùng đồng ý → ít lệnh, chọn lọc hơn. [I] Đây là giả thuyết; bằng chứng ngoài mẫu: 4 lệnh.
7. Parabolic SAR (xu hướng/kênh, tín hiệu) + 52-Week High/Low (xu hướng/kênh, tín hiệu) + TRIX (động lượng, tín hiệu) — nguồn thông tin: xu hướng, động lượng. Tín hiệu chỉ phát khi các nguồn khác nhau cùng đồng ý → ít lệnh, chọn lọc hơn. [I] Đây là giả thuyết; bằng chứng ngoài mẫu: 2 lệnh.
8. 52-Week High/Low (xu hướng/kênh, tín hiệu) + Median Price (giá/khác, tín hiệu) + Adaptive MA (xu hướng (MA), tín hiệu) + TRIX (động lượng, tín hiệu) — nguồn thông tin: giá, xu hướng, động lượng. Tín hiệu chỉ phát khi các nguồn khác nhau cùng đồng ý → ít lệnh, chọn lọc hơn. [I] Đây là giả thuyết; bằng chứng ngoài mẫu: 1 lệnh.
9. Keltner Channels (xu hướng/kênh, tín hiệu) + Price Channel (xu hướng/kênh, tín hiệu) + TRIX (động lượng, tín hiệu) + ATR (biến động, bộ lọc) — nguồn thông tin: biến động, xu hướng, động lượng. Tín hiệu chỉ phát khi các nguồn khác nhau cùng đồng ý → ít lệnh, chọn lọc hơn. [I] Đây là giả thuyết; bằng chứng ngoài mẫu: 6 lệnh.
10. 52-Week High/Low (xu hướng/kênh, tín hiệu) + TRIX (động lượng, tín hiệu) + Median Price (giá/khác, tín hiệu) + Adaptive MA (xu hướng (MA), tín hiệu) — nguồn thông tin: giá, xu hướng, động lượng. Tín hiệu chỉ phát khi các nguồn khác nhau cùng đồng ý → ít lệnh, chọn lọc hơn. [I] Đây là giả thuyết; bằng chứng ngoài mẫu: 3 lệnh.

Ghi chú: [F] số đo trên dữ liệu thật trong train + validation; chưa chạm tập test khoá. Kết quả backtest không phải lợi nhuận thực tế.
