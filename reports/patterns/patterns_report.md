# Báo cáo khai phá quy luật (Giai đoạn 4)

Train = khám phá, validation = xác nhận. Final test không được dùng.
IC = tương quan hạng Spearman GỘP (toàn tập, từng coin) giữa đặc trưng tại t và log return từ giá mở cửa t+1 tới t+H;
t-stat Newey-West trên chuỗi đóng góp theo ngày (đơn vị quan sát hiệu dụng = ngày). Hàng ALL = trung bình 5 coin.
Lưu ý: phiên bản đầu dùng IC trong từng ngày và bị thiên lệch (xem docs/hypotheses.md, nhật ký thay đổi).

## Tóm tắt

- Số kiểm định đơn biến: **900**; tổ hợp hai đặc trưng: **90**.
- Qua FDR (BY, q = 0.1) trên train (hàng ALL): **53**.
- Qua FDR + xác nhận validation: **41**; thêm ≥ 3/5 coin cùng dấu: **41**.
- Tổ hợp qua FDR + validation: **7**.
- Xác suất thắng hòa vốn (TP=SL=rào trung vị, chi phí khứ hồi 14 bps): H=60: **0.619**, H=240: **0.559**

## Giả thuyết định trước

| ID | Kết quả train | Kết quả validation | Đạt? |
|---|---|---|---|
| H2 breakout → tỷ lệ lên | Δ=-0.0214 (p=0.953, n=2540) | Δ=-0.0399 (p=0.919) | False |
| H2 breakdown → tỷ lệ xuống | Δ=-0.0088 (p=0.715) | Δ=+0.0046 (p=0.451) | |
| H3 co hẹp → biên độ 60′/rào | Δ=-0.2289 (p=1.000) | Δ=-0.2346 (p=1.000) | False |
| H4_reversal_ret15 (dấu kỳ vọng -1) | IC=-0.0282, t=-8.94, p=0.000 | IC=-0.0284, t=-4.62, p=0.000, coin cùng dấu 5.0/5 | True |
| H5_funding (dấu kỳ vọng -1) | IC=-0.0039, t=-0.34, p=0.366 | IC=-0.0161, t=-0.90, p=0.185, coin cùng dấu 4.0/5 | False |
| H6_oi_price (dấu kỳ vọng +1) | IC=0.0001, t=0.04, p=0.484 | IC=0.0112, t=1.57, p=0.058, coin cùng dấu 4.0/5 | False |
| H7_taker_imb (dấu kỳ vọng +0) | IC=-0.0237, t=-8.34, p=0.000 | IC=-0.0272, t=-5.72, p=0.000, coin cùng dấu 5.0/5 | True |

H1 (theo sóng DC) được kiểm định ở Giai đoạn 2 — xem `reports/waves/wave_report.md`.

## Ứng viên exploratory qua FDR trên train (hàng ALL)

| Rule | Đặc trưng | H | IC train | t train | IC val | t val | Coin cùng dấu (val) | Trạng thái |
|---|---|---|---|---|---|---|---|---|
| U0011 | `ret_15_z` | 60 | -0.0282 | -8.94 | -0.0284 | -4.62 | 5.0/5 | Đạt một phần (decile tốt nhất 0.521 < ngưỡng hòa vốn 0.619) |
| U0245 | `taker_imb_15` | 60 | -0.0237 | -8.34 | -0.0272 | -5.72 | 5.0/5 | Đạt một phần (decile tốt nhất 0.522 < ngưỡng hòa vốn 0.619) |
| U0155 | `rsi_14` | 60 | -0.0282 | -7.30 | -0.0300 | -4.23 | 5.0/5 | Đạt một phần (decile tốt nhất 0.517 < ngưỡng hòa vốn 0.619) |
| U0107 | `ema_dist_20_z` | 60 | -0.0258 | -7.09 | -0.0279 | -3.79 | 5.0/5 | Đạt một phần (decile tốt nhất 0.516 < ngưỡng hòa vốn 0.619) |
| U0017 | `ret_30_z` | 60 | -0.0302 | -6.73 | -0.0318 | -3.99 | 5.0/5 | Đạt một phần (decile tốt nhất 0.521 < ngưỡng hòa vốn 0.619) |
| U0113 | `ema_dist_60_z` | 60 | -0.0316 | -6.57 | -0.0369 | -4.24 | 5.0/5 | Đạt một phần (decile tốt nhất 0.531 < ngưỡng hòa vốn 0.619) |
| U0065 | `pos_range_1440` | 60 | -0.0332 | -6.53 | -0.0224 | -2.76 | 5.0/5 | Đạt một phần (decile tốt nhất 0.519 < ngưỡng hòa vốn 0.619) |
| U0149 | `di_diff_60` | 60 | -0.0331 | -6.46 | -0.0481 | -5.56 | 5.0/5 | Đạt một phần (decile tốt nhất 0.540 < ngưỡng hòa vốn 0.619) |
| U0071 | `dist_high_1440_z` | 60 | -0.0330 | -6.20 | -0.0201 | -2.35 | 5.0/5 | Đạt một phần (decile tốt nhất 0.530 < ngưỡng hòa vốn 0.619) |
| U0251 | `taker_imb_60` | 60 | -0.0244 | -6.17 | -0.0383 | -5.46 | 5.0/5 | Đạt một phần (decile tốt nhất 0.530 < ngưỡng hòa vốn 0.619) |
| U0161 | `rsi_60` | 60 | -0.0320 | -6.12 | -0.0449 | -5.59 | 5.0/5 | Đạt một phần (decile tốt nhất 0.538 < ngưỡng hòa vốn 0.619) |
| U0053 | `dist_high_240_z` | 60 | -0.0341 | -6.04 | -0.0521 | -4.63 | 5.0/5 | Đạt một phần (decile tốt nhất 0.552 < ngưỡng hòa vốn 0.619) |
| U0041 | `pos_range_60` | 60 | -0.0282 | -5.99 | -0.0283 | -3.56 | 5.0/5 | Đạt một phần (decile tốt nhất 0.514 < ngưỡng hòa vốn 0.619) |
| U0035 | `ret_1440_z` | 60 | -0.0351 | -5.95 | -0.0248 | -2.84 | 5.0/5 | Đạt một phần (decile tốt nhất 0.532 < ngưỡng hòa vốn 0.619) |
| U0083 | `body_15` | 60 | -0.0165 | -5.51 | -0.0108 | -1.87 | 5.0/5 | Đạt một phần (decile tốt nhất 0.509 < ngưỡng hòa vốn 0.619) |
| U0119 | `ema_dist_240_z` | 60 | -0.0298 | -5.25 | -0.0439 | -4.99 | 5.0/5 | Đạt một phần (decile tốt nhất 0.539 < ngưỡng hòa vốn 0.619) |
| U0047 | `pos_range_240` | 60 | -0.0280 | -5.22 | -0.0468 | -5.41 | 5.0/5 | Đạt một phần (decile tốt nhất 0.546 < ngưỡng hòa vốn 0.619) |
| U0137 | `ema_cross_20_60_z` | 60 | -0.0281 | -5.15 | -0.0371 | -3.92 | 5.0/5 | Đạt một phần (decile tốt nhất 0.534 < ngưỡng hòa vốn 0.619) |
| U0389 | `taker_lsr_5m` | 60 | -0.0149 | -4.99 | -0.0076 | -1.57 | 5.0/5 | Không đạt (không xác nhận trên validation) |
| U0125 | `ema_dist_1440_z` | 60 | -0.0272 | -4.93 | -0.0322 | -3.82 | 5.0/5 | Đạt một phần (decile tốt nhất 0.531 < ngưỡng hòa vốn 0.619) |
| U0077 | `dist_low_1440_z` | 60 | -0.0267 | -4.87 | -0.0233 | -2.15 | 5.0/5 | Đạt một phần (decile tốt nhất 0.521 < ngưỡng hòa vốn 0.619) |
| U0131 | `ema_slope_60_z` | 60 | -0.0256 | -4.85 | -0.0345 | -3.73 | 5.0/5 | Đạt một phần (decile tốt nhất 0.523 < ngưỡng hòa vốn 0.619) |
| U0695 | `taker_imb_15` | 240 | -0.0121 | -4.85 | -0.0130 | -2.23 | 5.0/5 | Đạt một phần (decile tốt nhất 0.515 < ngưỡng hòa vốn 0.559) |
| U0347 | `oi_chg_60` | 60 | -0.0193 | -4.83 | -0.0093 | -1.10 | 4.0/5 | Không đạt (không xác nhận trên validation) |
| U0023 | `ret_60_z` | 60 | -0.0263 | -4.72 | -0.0285 | -3.24 | 5.0/5 | Đạt một phần (decile tốt nhất 0.529 < ngưỡng hòa vốn 0.619) |
| U0287 | `false_breakout_15` | 60 | -0.0171 | -4.69 | -0.0226 | -2.63 | 5.0/5 | Đạt một phần (decile tốt nhất 0.502 < ngưỡng hòa vốn 0.619) |
| U0323 | `dc4_mode` | 60 | -0.0215 | -4.52 | -0.0078 | -0.78 | 4.0/5 | Không đạt (không xác nhận trên validation) |
| U0353 | `oi_chg_240` | 60 | -0.0199 | -4.51 | -0.0268 | -2.18 | 5.0/5 | Đạt một phần (decile tốt nhất 0.521 < ngưỡng hòa vốn 0.619) |
| U0461 | `ret_15_z` | 240 | -0.0119 | -4.50 | -0.0098 | -1.87 | 5.0/5 | Đạt một phần (decile tốt nhất 0.522 < ngưỡng hòa vốn 0.559) |
| U0443 | `btc_ret_60_z` | 60 | -0.0232 | -4.38 | -0.0203 | -2.49 | 5.0/5 | Đạt một phần (decile tốt nhất 0.517 < ngưỡng hòa vốn 0.619) |
| U0263 | `pv_corr_60` | 60 | -0.0214 | -4.24 | -0.0405 | -5.38 | 5.0/5 | Đạt một phần (decile tốt nhất 0.529 < ngưỡng hòa vốn 0.619) |
| U0257 | `taker_imb_240` | 60 | -0.0201 | -4.23 | -0.0327 | -3.44 | 5.0/5 | Đạt một phần (decile tốt nhất 0.523 < ngưỡng hòa vốn 0.619) |
| U0797 | `oi_chg_60` | 240 | -0.0210 | -4.06 | -0.0232 | -1.53 | 5.0/5 | Không đạt (không xác nhận trên validation) |
| U0317 | `dc2_age` | 60 | -0.0169 | -3.90 | -0.0261 | -2.38 | 5.0/5 | Đạt một phần (decile tốt nhất 0.521 < ngưỡng hòa vốn 0.619) |
| U0005 | `ret_5_z` | 60 | -0.0136 | -3.83 | -0.0036 | -0.53 | 4.0/5 | Không đạt (không xác nhận trên validation) |
| U0293 | `false_breakdown_15` | 60 | 0.0163 | 3.71 | 0.0269 | 4.32 | 5.0/5 | Đạt một phần (decile tốt nhất 0.502 < ngưỡng hòa vốn 0.619) |
| U0467 | `ret_30_z` | 240 | -0.0124 | -3.55 | -0.0096 | -1.23 | 5.0/5 | Không đạt (không xác nhận trên validation) |
| U0029 | `ret_240_z` | 60 | -0.0195 | -3.48 | -0.0269 | -2.58 | 5.0/5 | Đạt một phần (decile tốt nhất 0.520 < ngưỡng hòa vốn 0.619) |
| U0299 | `dc2_mode` | 60 | -0.0175 | -3.44 | -0.0207 | -2.57 | 4.0/5 | Đạt một phần (decile tốt nhất 0.502 < ngưỡng hòa vốn 0.619) |
| U0221 | `vol_ratio_30d` | 60 | 0.0211 | 3.35 | -0.0222 | -1.61 | 0.0/5 | Không đạt (không xác nhận trên validation) |
| U0605 | `rsi_14` | 240 | -0.0113 | -3.34 | -0.0144 | -1.80 | 5.0/5 | Đạt một phần (decile tốt nhất 0.520 < ngưỡng hòa vốn 0.559) |
| U0449 | `rel_ret_60_z` | 60 | -0.0170 | -3.28 | -0.0217 | -2.44 | 4.0/5 | Đạt một phần (decile tốt nhất 0.524 < ngưỡng hòa vốn 0.619) |
| U0485 | `ret_1440_z` | 240 | -0.0398 | -3.21 | -0.0356 | -1.64 | 5.0/5 | Không đạt (không xác nhận trên validation) |
| U0197 | `atr_60_rel` | 60 | 0.0188 | 3.19 | 0.0273 | 2.46 | 5.0/5 | Đạt một phần (decile tốt nhất 0.518 < ngưỡng hòa vốn 0.619) |
| U0203 | `range_60_z` | 60 | 0.0181 | 3.18 | 0.0172 | 2.29 | 5.0/5 | Đạt một phần (decile tốt nhất 0.516 < ngưỡng hòa vốn 0.619) |
| U0185 | `rv_240_rel` | 60 | 0.0185 | 3.17 | 0.0323 | 2.65 | 5.0/5 | Đạt một phần (decile tốt nhất 0.520 < ngưỡng hòa vốn 0.619) |
| U0635 | `rv_240_rel` | 240 | 0.0352 | 3.09 | 0.0673 | 2.76 | 5.0/5 | Đạt một phần (decile tốt nhất 0.537 < ngưỡng hòa vốn 0.559) |
| U0671 | `vol_ratio_30d` | 240 | 0.0392 | 3.06 | -0.0560 | -1.80 | 0.0/5 | Không đạt (không xác nhận trên validation) |
| U0533 | `body_15` | 240 | -0.0084 | -3.04 | -0.0020 | -0.40 | 4.0/5 | Không đạt (không xác nhận trên validation) |
| U0803 | `oi_chg_240` | 240 | -0.0220 | -3.03 | -0.0357 | -1.81 | 5.0/5 | Đạt một phần (decile tốt nhất 0.527 < ngưỡng hòa vốn 0.559) |
| U0845 | `ls_acct_chg_60` | 240 | -0.0183 | -3.02 | -0.0036 | -0.31 | 2.0/5 | Không đạt (không xác nhận trên validation) |
| U0515 | `pos_range_1440` | 240 | -0.0336 | -2.98 | -0.0161 | -0.98 | 5.0/5 | Không đạt (không xác nhận trên validation) |
| U0491 | `pos_range_60` | 240 | -0.0123 | -2.95 | -0.0169 | -2.08 | 5.0/5 | Đạt một phần (decile tốt nhất 0.521 < ngưỡng hòa vốn 0.559) |

### U0011 — `ret_15_z`, H = 60

| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |
|---|---|---|---|---|---|---|
| 1 | 20902 | 0.502 | 2.2 | 6561 | 0.518 | 0.3 |
| 2 | 20902 | 0.516 | 0.8 | 6431 | 0.503 | -2.2 |
| 3 | 20903 | 0.520 | 2.1 | 6821 | 0.515 | 0.6 |
| 4 | 20901 | 0.522 | 1.5 | 7229 | 0.512 | 0.5 |
| 5 | 20902 | 0.500 | 0.2 | 7930 | 0.497 | -0.8 |
| 6 | 20902 | 0.500 | -0.3 | 7752 | 0.487 | -1.7 |
| 7 | 20902 | 0.488 | -2.0 | 7208 | 0.479 | -1.7 |
| 8 | 20902 | 0.490 | -0.9 | 6746 | 0.482 | -1.3 |
| 9 | 20902 | 0.496 | 0.3 | 6247 | 0.495 | -0.2 |
| 10 | 20903 | 0.506 | 0.4 | 6353 | 0.490 | -1.1 |

IC theo chế độ (train+val): trend_regime=down: -0.1494 (t=-7.1); trend_regime=range: -0.0241 (t=-4.7); trend_regime=up: -0.0612 (t=-3.2); vol_regime=high: -0.0438 (t=-4.4); vol_regime=low: +0.0168 (t=1.1); vol_regime=normal: -0.0330 (t=-3.9)

### U0245 — `taker_imb_15`, H = 60

| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |
|---|---|---|---|---|---|---|
| 1 | 20902 | 0.521 | 2.1 | 6979 | 0.521 | 0.7 |
| 2 | 20902 | 0.514 | 1.1 | 6618 | 0.505 | 0.5 |
| 3 | 20903 | 0.507 | 0.8 | 6440 | 0.511 | -0.5 |
| 4 | 20901 | 0.508 | 1.4 | 6347 | 0.500 | -0.1 |
| 5 | 20902 | 0.506 | 1.5 | 6380 | 0.491 | -1.1 |
| 6 | 20903 | 0.503 | -0.3 | 6714 | 0.501 | -0.3 |
| 7 | 20901 | 0.494 | -0.6 | 6833 | 0.488 | -2.0 |
| 8 | 20902 | 0.492 | -1.3 | 7032 | 0.497 | -1.5 |
| 9 | 20902 | 0.498 | -0.4 | 7503 | 0.478 | -2.1 |
| 10 | 20903 | 0.497 | -0.1 | 8432 | 0.488 | -1.1 |

IC theo chế độ (train+val): trend_regime=down: -0.0856 (t=-4.9); trend_regime=range: -0.0204 (t=-5.6); trend_regime=up: -0.0344 (t=-2.1); vol_regime=high: -0.0360 (t=-4.3); vol_regime=low: -0.0043 (t=-0.3); vol_regime=normal: -0.0222 (t=-3.7)

### U0155 — `rsi_14`, H = 60

| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |
|---|---|---|---|---|---|---|
| 1 | 20902 | 0.514 | 1.9 | 6798 | 0.517 | -0.9 |
| 2 | 20902 | 0.514 | 1.6 | 7062 | 0.506 | -0.4 |
| 3 | 20902 | 0.507 | 0.1 | 7015 | 0.512 | -0.2 |
| 4 | 20902 | 0.511 | 0.9 | 7336 | 0.501 | -1.1 |
| 5 | 20902 | 0.502 | 0.2 | 7241 | 0.492 | 0.2 |
| 6 | 20902 | 0.505 | 1.0 | 7311 | 0.494 | -0.7 |
| 7 | 20902 | 0.497 | -1.6 | 7153 | 0.487 | -1.4 |
| 8 | 20902 | 0.504 | 0.4 | 6720 | 0.488 | -0.5 |
| 9 | 20902 | 0.493 | -0.7 | 6389 | 0.488 | -1.7 |
| 10 | 20903 | 0.494 | 0.3 | 6253 | 0.489 | -1.1 |

IC theo chế độ (train+val): trend_regime=down: -0.1578 (t=-6.8); trend_regime=range: -0.0217 (t=-3.6); trend_regime=up: -0.0702 (t=-3.5); vol_regime=high: -0.0353 (t=-3.3); vol_regime=low: +0.0250 (t=1.5); vol_regime=normal: -0.0312 (t=-3.9)

### U0107 — `ema_dist_20_z`, H = 60

| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |
|---|---|---|---|---|---|---|
| 1 | 20902 | 0.506 | 2.5 | 6283 | 0.516 | 0.6 |
| 2 | 20902 | 0.511 | 0.4 | 6646 | 0.510 | -0.4 |
| 3 | 20902 | 0.513 | 0.6 | 7271 | 0.503 | -1.2 |
| 4 | 20902 | 0.506 | 0.5 | 7440 | 0.500 | -0.9 |
| 5 | 20902 | 0.512 | 1.7 | 7773 | 0.493 | -0.9 |
| 6 | 20903 | 0.497 | -0.9 | 7833 | 0.496 | -1.2 |
| 7 | 20901 | 0.498 | -0.3 | 7196 | 0.486 | -1.1 |
| 8 | 20902 | 0.502 | -0.5 | 6655 | 0.492 | -0.9 |
| 9 | 20902 | 0.495 | -0.5 | 6146 | 0.484 | -0.4 |
| 10 | 20903 | 0.501 | 0.6 | 6035 | 0.495 | -1.0 |

IC theo chế độ (train+val): trend_regime=down: -0.1467 (t=-6.5); trend_regime=range: -0.0192 (t=-3.1); trend_regime=up: -0.0612 (t=-3.1); vol_regime=high: -0.0372 (t=-3.6); vol_regime=low: +0.0342 (t=2.0); vol_regime=normal: -0.0313 (t=-3.1)

### U0017 — `ret_30_z`, H = 60

| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |
|---|---|---|---|---|---|---|
| 1 | 20902 | 0.502 | 2.6 | 6541 | 0.512 | 1.6 |
| 2 | 20902 | 0.516 | 0.9 | 6657 | 0.502 | -0.0 |
| 3 | 20902 | 0.518 | 0.5 | 7064 | 0.519 | -0.3 |
| 4 | 20902 | 0.514 | 0.8 | 7342 | 0.506 | -1.4 |
| 5 | 20902 | 0.512 | 0.9 | 7358 | 0.494 | -0.9 |
| 6 | 20903 | 0.500 | -0.0 | 7514 | 0.493 | -1.8 |
| 7 | 20901 | 0.491 | -0.8 | 7083 | 0.483 | -2.0 |
| 8 | 20902 | 0.493 | -0.5 | 6744 | 0.479 | -2.2 |
| 9 | 20902 | 0.495 | -0.5 | 6510 | 0.483 | -2.1 |
| 10 | 20903 | 0.499 | 0.4 | 6465 | 0.505 | 1.7 |

IC theo chế độ (train+val): trend_regime=down: -0.1484 (t=-6.1); trend_regime=range: -0.0233 (t=-3.4); trend_regime=up: -0.0918 (t=-5.0); vol_regime=high: -0.0448 (t=-3.4); vol_regime=low: +0.0240 (t=1.4); vol_regime=normal: -0.0346 (t=-3.8)

### U0113 — `ema_dist_60_z`, H = 60

| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |
|---|---|---|---|---|---|---|
| 1 | 20902 | 0.510 | 3.2 | 6425 | 0.512 | -0.1 |
| 2 | 20902 | 0.508 | -0.6 | 6929 | 0.515 | -0.4 |
| 3 | 20903 | 0.517 | 0.3 | 7388 | 0.514 | -0.8 |
| 4 | 20901 | 0.507 | 0.3 | 7493 | 0.512 | -1.2 |
| 5 | 20902 | 0.509 | 0.8 | 7582 | 0.487 | -1.6 |
| 6 | 20903 | 0.507 | 0.1 | 7436 | 0.500 | 0.4 |
| 7 | 20901 | 0.499 | 0.1 | 7076 | 0.482 | -1.3 |
| 8 | 20902 | 0.496 | -0.6 | 6382 | 0.485 | -0.6 |
| 9 | 20902 | 0.496 | 0.2 | 6107 | 0.469 | -2.2 |
| 10 | 20903 | 0.491 | 0.6 | 6460 | 0.495 | 0.1 |

IC theo chế độ (train+val): trend_regime=down: -0.1869 (t=-7.3); trend_regime=range: -0.0203 (t=-2.7); trend_regime=up: -0.0979 (t=-5.5); vol_regime=high: -0.0418 (t=-2.8); vol_regime=low: +0.0377 (t=1.8); vol_regime=normal: -0.0373 (t=-3.5)

### U0065 — `pos_range_1440`, H = 60

| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |
|---|---|---|---|---|---|---|
| 1 | 20902 | 0.512 | 1.0 | 8645 | 0.517 | -2.0 |
| 2 | 20902 | 0.516 | -0.5 | 7929 | 0.496 | -3.8 |
| 3 | 20902 | 0.510 | -0.4 | 7230 | 0.501 | -0.1 |
| 4 | 20902 | 0.510 | -0.2 | 7044 | 0.504 | 0.7 |
| 5 | 20902 | 0.515 | 1.1 | 6642 | 0.498 | -1.1 |
| 6 | 20902 | 0.509 | 0.2 | 6673 | 0.507 | -0.3 |
| 7 | 20902 | 0.501 | 0.0 | 7157 | 0.497 | 0.1 |
| 8 | 20902 | 0.499 | 0.3 | 6711 | 0.481 | -2.2 |
| 9 | 20902 | 0.488 | 1.4 | 6226 | 0.481 | 0.3 |
| 10 | 20903 | 0.481 | 1.3 | 5021 | 0.483 | 2.3 |

IC theo chế độ (train+val): trend_regime=down: -0.0653 (t=-2.5); trend_regime=range: +0.0404 (t=4.7); trend_regime=up: -0.0729 (t=-3.7); vol_regime=high: -0.0451 (t=-3.4); vol_regime=low: -0.0082 (t=-0.4); vol_regime=normal: -0.0153 (t=-1.3)

### U0149 — `di_diff_60`, H = 60

| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |
|---|---|---|---|---|---|---|
| 1 | 20902 | 0.523 | 3.2 | 7504 | 0.517 | -2.2 |
| 2 | 20902 | 0.510 | -0.4 | 6722 | 0.533 | 0.8 |
| 3 | 20902 | 0.507 | -1.4 | 6569 | 0.519 | 1.2 |
| 4 | 20902 | 0.510 | -0.5 | 6553 | 0.506 | -1.4 |
| 5 | 20902 | 0.508 | 0.4 | 6377 | 0.497 | -0.6 |
| 6 | 20903 | 0.502 | -0.4 | 6495 | 0.500 | -0.3 |
| 7 | 20901 | 0.502 | 0.5 | 6545 | 0.494 | 0.3 |
| 8 | 20902 | 0.497 | 0.8 | 6667 | 0.492 | 0.4 |
| 9 | 20902 | 0.494 | 1.0 | 7172 | 0.469 | -3.0 |
| 10 | 20903 | 0.486 | 1.1 | 8674 | 0.460 | -2.2 |

IC theo chế độ (train+val): trend_regime=down: -0.1843 (t=-6.3); trend_regime=range: -0.0178 (t=-2.7); trend_regime=up: -0.0980 (t=-5.1); vol_regime=high: -0.0492 (t=-2.8); vol_regime=low: +0.0207 (t=1.1); vol_regime=normal: -0.0395 (t=-3.7)

### U0071 — `dist_high_1440_z`, H = 60

| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |
|---|---|---|---|---|---|---|
| 1 | 20902 | 0.504 | 1.1 | 8298 | 0.530 | -0.6 |
| 2 | 20902 | 0.511 | 0.1 | 8199 | 0.485 | -2.5 |
| 3 | 20902 | 0.517 | 0.5 | 7354 | 0.498 | -0.3 |
| 4 | 20902 | 0.512 | -0.9 | 6964 | 0.494 | -1.5 |
| 5 | 20902 | 0.511 | -1.0 | 6949 | 0.497 | -2.5 |
| 6 | 20903 | 0.514 | 0.9 | 6545 | 0.501 | -0.8 |
| 7 | 20901 | 0.506 | 0.3 | 6623 | 0.493 | -0.9 |
| 8 | 20902 | 0.499 | 0.5 | 6663 | 0.496 | -0.6 |
| 9 | 20902 | 0.487 | 1.1 | 6335 | 0.488 | 1.2 |
| 10 | 20903 | 0.479 | 1.5 | 5348 | 0.486 | 1.9 |

IC theo chế độ (train+val): trend_regime=down: +0.3165 (t=9.1); trend_regime=range: +0.0346 (t=4.0); trend_regime=up: -0.1311 (t=-6.4); vol_regime=high: -0.0531 (t=-3.7); vol_regime=low: -0.0024 (t=-0.1); vol_regime=normal: -0.0088 (t=-0.7)

### U0251 — `taker_imb_60`, H = 60

| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |
|---|---|---|---|---|---|---|
| 1 | 20902 | 0.520 | 0.8 | 7136 | 0.526 | 1.3 |
| 2 | 20902 | 0.520 | 2.0 | 6373 | 0.504 | -0.9 |
| 3 | 20903 | 0.512 | 1.7 | 6043 | 0.512 | 0.8 |
| 4 | 20901 | 0.504 | 0.7 | 5941 | 0.505 | -0.3 |
| 5 | 20902 | 0.496 | -1.2 | 6142 | 0.495 | -0.5 |
| 6 | 20903 | 0.505 | -0.3 | 6198 | 0.493 | -0.0 |
| 7 | 20901 | 0.500 | 0.4 | 6719 | 0.509 | -0.6 |
| 8 | 20902 | 0.504 | 0.3 | 7065 | 0.493 | -1.9 |
| 9 | 20902 | 0.490 | -0.3 | 8059 | 0.484 | -2.1 |
| 10 | 20903 | 0.489 | 0.2 | 9602 | 0.470 | -2.3 |

IC theo chế độ (train+val): trend_regime=down: -0.0942 (t=-3.9); trend_regime=range: -0.0228 (t=-3.8); trend_regime=up: -0.0499 (t=-2.8); vol_regime=high: -0.0379 (t=-3.0); vol_regime=low: -0.0043 (t=-0.3); vol_regime=normal: -0.0181 (t=-2.1)

### U0161 — `rsi_60`, H = 60

| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |
|---|---|---|---|---|---|---|
| 1 | 20902 | 0.518 | 2.8 | 7180 | 0.518 | -1.5 |
| 2 | 20902 | 0.511 | -0.3 | 7291 | 0.523 | -0.5 |
| 3 | 20902 | 0.508 | -0.3 | 7333 | 0.513 | -1.0 |
| 4 | 20902 | 0.507 | -0.6 | 7201 | 0.516 | 0.2 |
| 5 | 20902 | 0.504 | 0.0 | 7176 | 0.490 | -1.1 |
| 6 | 20902 | 0.510 | 0.5 | 6773 | 0.498 | 0.0 |
| 7 | 20902 | 0.502 | 0.1 | 6596 | 0.488 | 0.9 |
| 8 | 20902 | 0.504 | 0.7 | 6811 | 0.494 | -0.1 |
| 9 | 20902 | 0.489 | 0.1 | 6505 | 0.462 | -2.4 |
| 10 | 20903 | 0.488 | 1.2 | 6412 | 0.466 | -2.4 |

IC theo chế độ (train+val): trend_regime=down: -0.2045 (t=-7.1); trend_regime=range: -0.0163 (t=-2.2); trend_regime=up: -0.1140 (t=-6.1); vol_regime=high: -0.0427 (t=-2.8); vol_regime=low: +0.0261 (t=1.3); vol_regime=normal: -0.0377 (t=-3.7)

### U0053 — `dist_high_240_z`, H = 60

| Decile | n train | Tỷ lệ lên train | Return TB train (bps) | n val | Tỷ lệ lên val | Return TB val (bps) |
|---|---|---|---|---|---|---|
| 1 | 20902 | 0.502 | 1.2 | 7194 | 0.520 | 0.4 |
| 2 | 20902 | 0.516 | 1.3 | 7098 | 0.528 | 0.8 |
| 3 | 20903 | 0.516 | 0.4 | 7313 | 0.515 | -0.3 |
| 4 | 20901 | 0.503 | -0.1 | 7475 | 0.510 | 0.3 |
| 5 | 20902 | 0.508 | -0.1 | 7446 | 0.486 | -1.8 |
| 6 | 20903 | 0.506 | -0.1 | 7124 | 0.501 | -0.3 |
| 7 | 20901 | 0.511 | 1.2 | 7085 | 0.496 | -1.4 |
| 8 | 20902 | 0.503 | 1.4 | 6810 | 0.483 | -0.1 |
| 9 | 20902 | 0.494 | -0.2 | 6581 | 0.470 | -2.3 |
| 10 | 20903 | 0.481 | -0.9 | 5152 | 0.448 | -4.0 |

IC theo chế độ (train+val): trend_regime=down: -0.1029 (t=-4.3); trend_regime=range: -0.0281 (t=-3.3); trend_regime=up: -0.1191 (t=-5.3); vol_regime=high: -0.0596 (t=-3.3); vol_regime=low: +0.0161 (t=0.7); vol_regime=normal: -0.0396 (t=-3.5)

## Tổ hợp hai đặc trưng (tương tác hạng trong ngày)

| Cặp | H | IC train | t train | IC val | t val | FDR train | Xác nhận val |
|---|---|---|---|---|---|---|---|
| `rsi_14*dist_high_1440_z` | 60 | 0.0148 | 3.69 | 0.0151 | 1.65 | True | True |
| `ema_dist_60_z*dist_high_1440_z` | 60 | 0.0171 | 3.58 | 0.0167 | 1.64 | True | False |
| `ema_dist_20_z*dist_high_1440_z` | 60 | 0.0134 | 3.52 | 0.0144 | 1.70 | True | True |
| `rsi_14*ema_dist_60_z` | 240 | 0.0109 | 3.39 | 0.0124 | 2.42 | True | True |
| `ema_dist_20_z*ema_dist_60_z` | 240 | 0.0126 | 3.37 | 0.0188 | 3.35 | True | True |
| `ret_30_z*dist_high_1440_z` | 60 | 0.0148 | 3.35 | 0.0185 | 1.91 | True | True |
| `rsi_14*ema_dist_20_z` | 240 | 0.0117 | 3.34 | 0.0153 | 3.26 | True | True |
| `ret_15_z*dist_high_1440_z` | 60 | 0.0110 | 3.21 | 0.0113 | 1.69 | True | True |
| `taker_imb_15*ema_dist_60_z` | 240 | 0.0070 | 2.98 | 0.0044 | 1.01 | False | False |
| `ret_15_z*ema_dist_20_z` | 60 | 0.0093 | 2.93 | 0.0096 | 1.68 | False | True |
| `ret_15_z*rsi_14` | 240 | 0.0098 | 2.92 | 0.0111 | 2.10 | False | True |
| `ret_15_z*ema_dist_20_z` | 240 | 0.0133 | 2.89 | 0.0183 | 2.68 | False | True |
| `taker_imb_15*ret_30_z` | 240 | 0.0069 | 2.84 | 0.0090 | 2.25 | False | True |
| `taker_imb_15*taker_imb_60` | 60 | -0.0048 | -2.83 | -0.0071 | -1.65 | False | True |
| `taker_imb_15*ema_dist_20_z` | 240 | 0.0078 | 2.73 | 0.0063 | 1.45 | False | False |
| `ret_15_z*taker_imb_15` | 240 | 0.0087 | 2.70 | 0.0078 | 1.66 | False | True |
| `ema_dist_20_z*ret_30_z` | 240 | 0.0102 | 2.66 | 0.0174 | 2.96 | False | True |
| `rsi_14*ret_30_z` | 240 | 0.0091 | 2.61 | 0.0123 | 2.18 | False | True |
| `ret_15_z*ret_30_z` | 240 | 0.0086 | 2.58 | 0.0159 | 3.12 | False | True |
| `di_diff_60*dist_high_1440_z` | 60 | 0.0129 | 2.56 | 0.0150 | 1.38 | False | False |

## Top 25 theo |t| train (mọi hàng, kể cả từng coin)

| Rule | Đặc trưng | Symbol | H | IC train | t train | IC val | t val | FDR | Val |
|---|---|---|---|---|---|---|---|---|---|
| U0011 | `ret_15_z` | ALL | 60 | -0.0282 | -8.94 | -0.0284 | -4.62 | True | True |
| U0006 | `ret_15_z` | BTCUSDT | 60 | -0.0335 | -8.83 | -0.0353 | -5.59 | True | True |
| U0150 | `rsi_14` | BTCUSDT | 60 | -0.0388 | -8.38 | -0.0388 | -4.67 | True | True |
| U0245 | `taker_imb_15` | ALL | 60 | -0.0237 | -8.34 | -0.0272 | -5.72 | True | True |
| U0010 | `ret_15_z` | XRPUSDT | 60 | -0.0325 | -8.17 | -0.0234 | -2.54 | True | True |
| U0102 | `ema_dist_20_z` | BTCUSDT | 60 | -0.0354 | -8.08 | -0.0368 | -4.24 | True | True |
| U0016 | `ret_30_z` | XRPUSDT | 60 | -0.0381 | -7.51 | -0.0195 | -1.80 | True | True |
| U0007 | `ret_15_z` | ETHUSDT | 60 | -0.0313 | -7.33 | -0.0318 | -5.91 | True | True |
| U0155 | `rsi_14` | ALL | 60 | -0.0282 | -7.30 | -0.0300 | -4.23 | True | True |
| U0112 | `ema_dist_60_z` | XRPUSDT | 60 | -0.0395 | -7.16 | -0.0297 | -2.33 | True | True |
| U0107 | `ema_dist_20_z` | ALL | 60 | -0.0258 | -7.09 | -0.0279 | -3.79 | True | True |
| U0108 | `ema_dist_60_z` | BTCUSDT | 60 | -0.0389 | -6.78 | -0.0459 | -5.34 | True | True |
| U0012 | `ret_30_z` | BTCUSDT | 60 | -0.0350 | -6.75 | -0.0410 | -4.75 | True | True |
| U0036 | `pos_range_60` | BTCUSDT | 60 | -0.0404 | -6.74 | -0.0420 | -4.94 | True | True |
| U0017 | `ret_30_z` | ALL | 60 | -0.0302 | -6.73 | -0.0318 | -3.99 | True | True |
| U0154 | `rsi_14` | XRPUSDT | 60 | -0.0310 | -6.69 | -0.0234 | -2.38 | True | True |
| U0060 | `pos_range_1440` | BTCUSDT | 60 | -0.0424 | -6.60 | -0.0278 | -3.35 | True | True |
| U0113 | `ema_dist_60_z` | ALL | 60 | -0.0316 | -6.57 | -0.0369 | -4.24 | True | True |
| U0065 | `pos_range_1440` | ALL | 60 | -0.0332 | -6.53 | -0.0224 | -2.76 | True | True |
| U0149 | `di_diff_60` | ALL | 60 | -0.0331 | -6.46 | -0.0481 | -5.56 | True | True |
| U0106 | `ema_dist_20_z` | XRPUSDT | 60 | -0.0289 | -6.34 | -0.0219 | -2.19 | True | True |
| U0243 | `taker_imb_15` | SOLUSDT | 60 | -0.0273 | -6.26 | -0.0313 | -3.65 | True | True |
| U0071 | `dist_high_1440_z` | ALL | 60 | -0.0330 | -6.20 | -0.0201 | -2.35 | True | True |
| U0251 | `taker_imb_60` | ALL | 60 | -0.0244 | -6.17 | -0.0383 | -5.46 | True | True |
| U0148 | `di_diff_60` | XRPUSDT | 60 | -0.0399 | -6.15 | -0.0443 | -3.48 | True | True |

Ghi chú: IC có ý nghĩa thống kê chưa chắc có ý nghĩa kinh tế. Quy luật chỉ đáng giao dịch nếu decile cực trị
vượt ngưỡng hòa vốn và vượt qua backtest có chi phí (Giai đoạn 7–8).
