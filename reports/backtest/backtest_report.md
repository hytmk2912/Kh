# Báo cáo backtest (Giai đoạn 7–8) — tập validation

Giai đoạn: 2025-12-22 → 2026-05-16. Vốn giả định 10,000 USD, rủi ro 0.5% vốn/lệnh, đòn bẩy tối đa 3.0× trên phần vốn mỗi coin.
Phí taker 0.050%/chiều (giả định VIP0), slippage 2.0 bps/chiều, funding thực tế.
Vào lệnh ở giá mở cửa nến sau tín hiệu; TP/SL cùng nến → SL trước; mỗi coin tối đa 1 vị thế.
Vốn không tái đầu tư: lỗ có thể vượt 100% vốn trên giấy; cột 'Cháy TK' = đường vốn từng chạm 0 (thực tế sẽ bị thanh lý/dừng).
Chi phí khứ hồi ≈ 14 bps (phí 10 + slippage 4): 'Exp ròng' ≈ 'Exp trước mọi chi phí' − 14 − funding.

Số biến thể đã thử: **14** (cố định trước). PBO (CSCV, giai đoạn walk-forward): **0.000**.
Lưu ý: PBO thấp ở đây KHÔNG có nghĩa là chiến lược tốt — phần lớn biến thể lỗ đều đặn nên thứ hạng ổn định một cách tầm thường.
DSR (xác suất Sharpe thật > 0 sau khi tính số biến thể đã thử) mới là chỉ số chính.
'Ngẫu nhiên %ile' = tỷ lệ 50 lần chạy ngẫu nhiên (cùng kích thước & quy tắc thoát) có expectancy/lệnh thấp hơn chiến lược.
'Exp' là trung bình theo lệnh (bps notional); 'Ròng USD' có trọng số theo kích thước lệnh nên có thể khác dấu.

| Biến thể | Lệnh | Ròng (USD) | Return | Cháy TK | Sharpe | MaxDD | PF | Win | Exp ròng (bps) | Exp trước mọi chi phí (bps) | CI90 exp (bps) | Phí | Funding | Ngẫu nhiên %ile | DSR | Chọn |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lgbm_H60_tau0.55 | 4441 | -29879 | -298.79% | CÓ | -15.11 | 297.03% | 0.53 | 0.399 | -11.8 | 2.2 | [-13.8, -9.8] | 25262 | 21 | 1.00 | 0.000 | False |
| lgbm_H60_tau0.6 | 170 | -269 | -2.69% | không | -0.99 | 3.07% | 0.89 | 0.500 | -1.3 | 12.7 | [-12.4, 7.9] | 875 | 1 | 1.00 | 0.000 | False |
| lgbm_H60_tau0.65 | 8 | 71 | 0.71% | không | 2.21 | 0.00% | 2.32 | 0.750 | 23.4 | 37.0 | [n/a, n/a] | 38 | 1 | 0.98 | 0.000 | False |
| lgbm_H240_tau0.55 | 2992 | -16583 | -165.83% | CÓ | -8.34 | 168.34% | 0.70 | 0.451 | -12.7 | 1.3 | [-18.4, -7.3] | 13126 | 11 | 0.84 | 0.000 | False |
| lgbm_H240_tau0.6 | 609 | -1437 | -14.37% | không | -1.86 | 16.48% | 0.86 | 0.478 | -0.2 | 13.8 | [-12.6, 12.7] | 2427 | 11 | 1.00 | 0.000 | False |
| lgbm_H240_tau0.65 | 77 | 120 | 1.20% | không | 0.53 | 2.28% | 1.11 | 0.519 | 11.8 | 25.9 | [-24.3, 44.0] | 279 | -2 | 0.98 | 0.000 | False |
| rev_ret_15_z_H60 | 10275 | -82054 | -820.54% | CÓ | -23.18 | 818.04% | 0.52 | 0.427 | -13.7 | 0.3 | [-15.2, -12.2] | 59945 | -9 | 0.70 | 0.000 | False |
| rev_ret_15_z_H240 | 4623 | -31201 | -312.01% | CÓ | -11.42 | 315.70% | 0.68 | 0.454 | -14.5 | -0.5 | [-18.0, -11.0] | 21055 | 30 | 0.40 | 0.000 | False |
| rev_taker_imb_15_H60 | 9723 | -77703 | -777.03% | CÓ | -38.16 | 773.01% | 0.42 | 0.365 | -13.5 | 0.5 | [-14.3, -12.6] | 57462 | 2 | 0.80 | 0.000 | False |
| rev_taker_imb_15_H240 | 4193 | -25910 | -259.10% | CÓ | -16.08 | 260.51% | 0.66 | 0.435 | -13.1 | 0.9 | [-15.0, -11.0] | 19830 | 21 | 0.62 | 0.000 | False |
| rev_rsi_14_H60 | 9951 | -84273 | -842.73% | CÓ | -31.04 | 839.17% | 0.46 | 0.390 | -14.7 | -0.7 | [-16.0, -13.4] | 58060 | -6 | 0.10 | 0.000 | False |
| rev_rsi_14_H240 | 4657 | -32669 | -326.69% | CÓ | -13.96 | 326.81% | 0.65 | 0.445 | -15.5 | -1.5 | [-18.5, -12.3] | 21304 | 11 | 0.28 | 0.000 | False |
| dc_sig4 | 515 | -601 | -6.01% | không | -0.58 | 14.43% | 0.94 | 0.332 | 1.7 | 15.7 | [-23.4, 28.8] | 1288 | -0 | 0.86 | 0.000 | False |
| dc_sig8 | 147 | -305 | -3.05% | không | -0.47 | 15.31% | 0.89 | 0.367 | 2.9 | 18.2 | [-98.4, 115.6] | 184 | -13 | 0.30 | 0.000 | False |

Baseline: không giao dịch = 0%; mua & giữ 5 coin (1× vốn, có funding) = -22.54% (MaxDD 46.28%, Sharpe -1.26).

## Độ bền (PnL ròng USD)

| Biến thể | Gốc | Chi phí ×1,5 | Chi phí ×2 | Slippage ×3 | Trễ 1 nến | Bỏ 5% lệnh lãi nhất | Train (trong mẫu) |
|---|---|---|---|---|---|---|---|
| lgbm_H60_tau0.55 | -29879 | -47561 | -65243 | -50085 | -31586 | -39541 | n/a |
| lgbm_H60_tau0.6 | -269 | -882 | -1494 | -969 | -265 | -680 | n/a |
| lgbm_H60_tau0.65 | 71 | 45 | 18 | 41 | 117 | 40 | n/a |
| lgbm_H240_tau0.55 | -16583 | -25770 | -34957 | -27081 | -16476 | -23569 | n/a |
| lgbm_H240_tau0.6 | -1437 | -3135 | -4834 | -3378 | -1934 | -2919 | n/a |
| lgbm_H240_tau0.65 | 120 | -75 | -271 | -103 | 99 | -73 | n/a |
| rev_ret_15_z_H60 | -82054 | -124016 | -165977 | -130009 | -78305 | -104097 | -275788 |
| rev_ret_15_z_H240 | -31201 | -45939 | -60676 | -48042 | -27864 | -41976 | -83586 |
| rev_taker_imb_15_H60 | -77703 | -117927 | -158152 | -123676 | -76429 | -95701 | -210314 |
| rev_taker_imb_15_H240 | -25910 | -39791 | -53673 | -41775 | -25737 | -35513 | -72482 |
| rev_rsi_14_H60 | -84273 | -124915 | -165556 | -130718 | -84618 | -104796 | -248674 |
| rev_rsi_14_H240 | -32669 | -47581 | -62493 | -49710 | -31574 | -43448 | -84626 |
| dc_sig4 | -601 | -1504 | -2406 | -1633 | -1454 | -4995 | n/a |
| dc_sig8 | -305 | -434 | -562 | -452 | -977 | -1690 | n/a |

## Tiêu chí lựa chọn (docs/hypotheses.md)

| Biến thể | 1. Exp & CI > 0 | 2. PF > 1,1 & ≥ 100 lệnh | 3. Chi phí ×1,5 & trễ | 4. Bỏ top 5% | 5. DSR & PBO | Chọn |
|---|---|---|---|---|---|---|
| lgbm_H60_tau0.55 | False | False | False | False | False | False |
| lgbm_H60_tau0.6 | False | False | False | False | False | False |
| lgbm_H60_tau0.65 | False | False | True | True | False | False |
| lgbm_H240_tau0.55 | False | False | False | False | False | False |
| lgbm_H240_tau0.6 | False | False | False | False | False | False |
| lgbm_H240_tau0.65 | False | False | False | False | False | False |
| rev_ret_15_z_H60 | False | False | False | False | False | False |
| rev_ret_15_z_H240 | False | False | False | False | False | False |
| rev_taker_imb_15_H60 | False | False | False | False | False | False |
| rev_taker_imb_15_H240 | False | False | False | False | False | False |
| rev_rsi_14_H60 | False | False | False | False | False | False |
| rev_rsi_14_H240 | False | False | False | False | False | False |
| dc_sig4 | False | False | False | False | False | False |
| dc_sig8 | False | False | False | False | False | False |

**Chiến lược được chọn vào final test:** KHÔNG CÓ.
Biến thể tốt nhất mỗi họ trên validation (chạy final test chỉ để THAM KHẢO, không phải lựa chọn): dc_follow: dc_sig8, model: lgbm_H60_tau0.65, reversal: rev_ret_15_z_H240

## PnL theo coin trên validation (USD)

| Biến thể | BTCUSDT | ETHUSDT | BNBUSDT | SOLUSDT | XRPUSDT |
|---|---|---|---|---|---|
| lgbm_H60_tau0.55 | -6610 | -6333 | -6269 | -4788 | -5879 |
| lgbm_H60_tau0.6 | 1 | -160 | 47 | -203 | 45 |
| lgbm_H60_tau0.65 | n/a | n/a | 12 | 54 | 5 |
| lgbm_H240_tau0.55 | -4114 | -3559 | -3849 | -2133 | -2928 |
| lgbm_H240_tau0.6 | -704 | -49 | -660 | 96 | -120 |
| lgbm_H240_tau0.65 | -32 | -56 | -15 | 227 | -4 |
| rev_ret_15_z_H60 | -15552 | -17289 | -17406 | -16905 | -14902 |
| rev_ret_15_z_H240 | -6826 | -4251 | -6299 | -6933 | -6893 |
| rev_taker_imb_15_H60 | -16752 | -12947 | -19456 | -14702 | -13845 |
| rev_taker_imb_15_H240 | -5203 | -5749 | -5671 | -3936 | -5351 |
| rev_rsi_14_H60 | -15882 | -17081 | -17765 | -16572 | -16973 |
| rev_rsi_14_H240 | -7481 | -5739 | -6442 | -6162 | -6845 |
| dc_sig4 | -506 | -118 | -291 | 58 | 255 |
| dc_sig8 | -4 | 19 | -200 | 2 | -122 |
