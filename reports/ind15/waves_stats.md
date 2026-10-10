# Thống kê sóng (đáp án ZigZag) — train + validation

Sóng nhanh = đi được ≥ ngưỡng trong ≤ 32 nến M15 (8 giờ) tính từ điểm xuất phát. Tỷ lệ nhãn tính trên số nến.
Thứ tự ưu tiên nhãn: UNKNOWN > ĐI NGANG > NHỊP HỒI > SÓNG. Số liệu [F] đo trên dữ liệu thật.

## Ngưỡng 1.5% (chính)

| Symbol | Tăng nhanh | Tăng chậm | Giảm nhanh | Giảm chậm | Đoạn đi ngang | Số nến M15 TB / trung vị (tăng nhanh) | Biên độ TB % (tăng nhanh) | Hồi sâu nhất TV % sóng | % SÓNG | % NHỊP HỒI | % ĐI NGANG | % UNKNOWN |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 681 | 78 | 668 | 91 | 348 | 30.8 / 15.0 | 3.10 | 21.7 | 22.1 | 6.2 | 71.6 | 0.09 |
| ETHUSDT | 1593 | 42 | 1578 | 56 | 280 | 16.4 / 9.0 | 3.20 | 21.3 | 48.5 | 16.3 | 35.1 | 0.05 |
| BNBUSDT | 913 | 61 | 900 | 74 | 304 | 26.6 / 13.0 | 3.27 | 21.8 | 31.5 | 9.3 | 59.1 | 0.06 |
| SOLUSDT | 2069 | 15 | 2065 | 18 | 190 | 13.3 / 7.0 | 3.28 | 17.5 | 60.2 | 18.8 | 20.9 | 0.05 |
| XRPUSDT | 2195 | 32 | 2199 | 28 | 244 | 11.7 / 5.0 | 3.47 | 0.0 | 52.7 | 15.3 | 32.0 | 0.06 |

## Ngưỡng 1.0% (độ nhạy, chỉ báo cáo)

| Symbol | Tăng nhanh | Tăng chậm | Giảm nhanh | Giảm chậm | Đoạn đi ngang | Số nến M15 TB / trung vị (tăng nhanh) | Biên độ TB % (tăng nhanh) | Hồi sâu nhất TV % sóng | % SÓNG | % NHỊP HỒI | % ĐI NGANG | % UNKNOWN |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 1518 | 46 | 1515 | 49 | 293 | 16.4 / 9.0 | 2.14 | 0.0 | 49.7 | 9.2 | 41.0 | 0.09 |
| ETHUSDT | 3196 | 15 | 3196 | 14 | 120 | 8.8 / 5.0 | 2.22 | 0.0 | 74.0 | 13.9 | 12.0 | 0.05 |
| BNBUSDT | 1959 | 24 | 1936 | 47 | 232 | 14.3 / 7.0 | 2.22 | 0.0 | 59.7 | 9.6 | 30.7 | 0.06 |
| SOLUSDT | 4072 | 6 | 4073 | 4 | 50 | 7.0 / 4.0 | 2.27 | 0.0 | 81.2 | 13.8 | 5.0 | 0.05 |
| XRPUSDT | 3997 | 10 | 3994 | 12 | 100 | 6.8 / 3.0 | 2.47 | 0.0 | 77.1 | 12.2 | 10.7 | 0.05 |

## Ngưỡng 2.0% (độ nhạy, chỉ báo cáo)

| Symbol | Tăng nhanh | Tăng chậm | Giảm nhanh | Giảm chậm | Đoạn đi ngang | Số nến M15 TB / trung vị (tăng nhanh) | Biên độ TB % (tăng nhanh) | Hồi sâu nhất TV % sóng | % SÓNG | % NHỊP HỒI | % ĐI NGANG | % UNKNOWN |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 338 | 93 | 328 | 103 | 273 | 47.3 / 22.5 | 4.13 | 24.9 | 9.9 | 3.8 | 86.1 | 0.09 |
| ETHUSDT | 931 | 68 | 918 | 81 | 381 | 25.4 / 14.0 | 4.16 | 24.3 | 29.3 | 12.0 | 58.6 | 0.06 |
| BNBUSDT | 498 | 84 | 491 | 90 | 272 | 39.6 / 20.0 | 4.34 | 24.2 | 16.4 | 6.1 | 77.4 | 0.07 |
| SOLUSDT | 1232 | 45 | 1237 | 40 | 332 | 20.4 / 11.0 | 4.24 | 23.5 | 41.5 | 16.0 | 42.5 | 0.06 |
| XRPUSDT | 1315 | 58 | 1323 | 50 | 307 | 17.1 / 7.0 | 4.55 | 19.8 | 34.3 | 12.5 | 53.2 | 0.06 |

