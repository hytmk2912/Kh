# Báo cáo cấu trúc sóng (Giai đoạn 2)

Phạm vi: train + validation (2024-10-09 → 2026-05-15). Final test KHÔNG được dùng.
Thang `sigK` = ngưỡng K × σ_1m × √60 (σ EWMA 1 ngày, dịch 1 nến); `pctX` = ngưỡng X% cố định.
Đây là thống kê MÔ TẢ lịch sử; không tự động có giá trị dự báo.

## Tổng hợp 5 coin theo thang

| Thang | Số sóng | Sóng/ngày | Biên độ trung vị % | p90 % | Thời lượng trung vị (phút) | Hồi sâu nhất trung vị | Overshoot/θ TB | Trễ xác nhận (phút) | Phí/biên độ |
|---|---|---|---|---|---|---|---|---|---|
| pct0.5 | 138,535 | 237.3 | 0.89 | 1.75 | 12 | 0.79 | 1.06 | 4 | 0.16 |
| pct1 | 38,798 | 66.5 | 1.73 | 3.41 | 41 | 0.81 | 1.03 | 16 | 0.08 |
| pct2 | 10,233 | 17.5 | 3.41 | 6.68 | 162 | 0.83 | 1.01 | 62 | 0.04 |
| sig2 | 16,825 | 28.9 | 2.22 | 5.15 | 155 | 0.82 | 1.02 | 60 | 0.06 |
| sig4 | 4,307 | 7.4 | 4.38 | 10.20 | 716 | 0.84 | 1.04 | 276 | 0.03 |
| sig8 | 1,098 | 1.9 | 8.74 | 20.07 | 3145 | 0.86 | 1.14 | 1214 | 0.02 |

## H1 — theo sóng DC (vào ở nến sau xác nhận, thoát ở nến sau xác nhận ngược)

| Thang | Tập | Số lệnh | TB gộp (bps) | CI 90% (bps) | p một phía | TB ròng sau phí (bps) | Tỷ lệ thắng gộp |
|---|---|---|---|---|---|---|---|
| pct0.5 | train | 112,865 | -0.4 | [-0.7, -0.0] | 0.963 | -14.4 | 0.374 |
| pct0.5 | val | 25,670 | -0.6 | [-1.6, 0.3] | 0.840 | -14.6 | 0.368 |
| pct1 | train | 31,831 | -0.0 | [-1.2, 1.2] | 0.494 | -14.0 | 0.370 |
| pct1 | val | 6,967 | -1.4 | [-3.8, 1.2] | 0.825 | -15.4 | 0.367 |
| pct2 | train | 8,463 | -0.7 | [-5.1, 3.8] | 0.593 | -14.7 | 0.372 |
| pct2 | val | 1,770 | -3.3 | [-14.2, 9.8] | 0.664 | -17.3 | 0.360 |
| sig2 | train | 12,690 | -0.2 | [-3.2, 3.2] | 0.523 | -14.2 | 0.373 |
| sig2 | val | 4,135 | 0.6 | [-4.1, 5.4] | 0.401 | -13.4 | 0.378 |
| sig4 | train | 3,270 | 2.0 | [-11.8, 15.8] | 0.415 | -12.0 | 0.377 |
| sig4 | val | 1,037 | 14.8 | [-10.2, 43.1] | 0.176 | 0.8 | 0.365 |
| sig8 | train | 805 | 44.4 | [-1.9, 93.7] | 0.070 | 30.4 | 0.400 |
| sig8 | val | 293 | -7.1 | [-76.6, 71.1] | 0.546 | -21.1 | 0.372 |

## Theo coin (thang chính sig4)

| Symbol | Sóng | Biên độ trung vị % | Thời lượng trung vị | Overshoot/θ | ρ(biên độ, biên độ sau) | H1 gộp (bps) | H1 ròng (bps) |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 857 | 3.19 | 721 | 1.01 | 0.310 | -4.9 | -18.9 |
| ETHUSDT | 893 | 4.52 | 715 | 1.04 | 0.310 | 3.5 | -10.5 |
| BNBUSDT | 886 | 3.57 | 688 | 1.05 | 0.437 | 10.4 | -3.6 |
| SOLUSDT | 854 | 5.72 | 722 | 1.04 | 0.276 | 4.1 | -9.9 |
| XRPUSDT | 817 | 5.30 | 740 | 1.08 | 0.481 | 12.4 | -1.6 |

## Chuyển tiếp biên độ (sig4, BTCUSDT): P(tercile sóng sau | tercile sóng hiện tại)

Cột = tercile sóng hiện tại, dòng = tercile sóng kế tiếp. Nếu độc lập, mỗi ô ≈ 0,333.

|  | small | mid | large |
|---|---|---|---|
| small | 0.469 | 0.311 | 0.220 |
| mid | 0.326 | 0.365 | 0.309 |
| large | 0.207 | 0.323 | 0.470 |

Tỷ lệ cặp sóng có (biên độ sau / biên độ trước) nằm trong ±5% quanh mốc:

0.382: 0.025, 0.5: 0.033, 0.618: 0.049, 1.0: 0.058, 1.618: 0.035, ctrl_0.45: 0.023, ctrl_0.56: 0.035, ctrl_0.75: 0.062, ctrl_1.3: 0.068

## Theo chế độ thị trường (gộp coin, chỉ nhóm ≥ 30 sóng)

| Thang | Xu hướng | Biến động | Sóng | Biên độ TV % | Thời lượng TV | Overshoot/θ | H1 gộp (bps) |
|---|---|---|---|---|---|---|---|
| sig4 | down | high | 306 | 6.62 | 634 | 0.93 | 20.3 |
| sig4 | down | low | 155 | 3.83 | 625 | 1.22 | 36.7 |
| sig4 | down | normal | 522 | 4.42 | 718 | 0.99 | -9.8 |
| sig4 | range | high | 459 | 6.37 | 850 | 1.01 | 3.0 |
| sig4 | range | low | 628 | 3.22 | 655 | 1.14 | 14.0 |
| sig4 | range | normal | 1326 | 4.23 | 722 | 1.07 | 9.3 |
| sig4 | up | high | 191 | 5.78 | 701 | 0.88 | -47.9 |
| sig4 | up | low | 177 | 3.32 | 581 | 0.99 | -10.6 |
| sig4 | up | normal | 494 | 3.92 | 804 | 0.99 | 3.3 |

## Tỷ lệ thời gian theo chế độ

- BTCUSDT: xu hướng {'range': 0.7553, 'up': 0.1301, 'down': 0.1129, 'na': 0.0017}; biến động {'normal': 0.5822, 'low': 0.2154, 'high': 0.1887, 'na': 0.0137}
- ETHUSDT: xu hướng {'range': 0.7327, 'up': 0.1377, 'down': 0.1278, 'na': 0.0017}; biến động {'normal': 0.5619, 'low': 0.2149, 'high': 0.2094, 'na': 0.0137}
- BNBUSDT: xu hướng {'range': 0.7493, 'up': 0.1363, 'down': 0.1127, 'na': 0.0017}; biến động {'normal': 0.5076, 'low': 0.2581, 'high': 0.2207, 'na': 0.0137}
- SOLUSDT: xu hướng {'range': 0.7275, 'up': 0.1368, 'down': 0.1339, 'na': 0.0017}; biến động {'normal': 0.588, 'low': 0.2027, 'high': 0.1956, 'na': 0.0137}
- XRPUSDT: xu hướng {'range': 0.7553, 'up': 0.1282, 'down': 0.1147, 'na': 0.0017}; biến động {'normal': 0.5074, 'low': 0.258, 'high': 0.2209, 'na': 0.0137}

## Ghi chú phương pháp

- Theo định nghĩa DC, sóng luôn luân phiên tăng/giảm nên “xác suất chuyển từ tăng sang giảm” luôn bằng 1;
  câu hỏi có ý nghĩa là về **độ lớn** sóng kế tiếp (bảng chuyển tiếp tercile).
- Với bước ngẫu nhiên không trôi, overshoot/θ kỳ vọng ≈ 1 và H1 kỳ vọng ≈ 0; độ lệch khỏi mốc này mới là thông tin.
- Đỉnh/đáy (extreme) là nhãn hồi cứu; mọi con số H1 dùng thời điểm xác nhận + giá mở cửa nến kế tiếp.
