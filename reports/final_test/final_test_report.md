# Báo cáo FINAL TEST

Chế độ: **first_run** · chạy lúc 2026-10-09T16:37:29+00:00 · git e8fdcbd · file khóa cee83e99e588
Giai đoạn: 2026-05-17 → 2026-10-09 (sau embargo 1 ngày).
Chiến lược được chọn trên validation: **không có**.

| Biến thể | Trạng thái | Lệnh | Ròng (USD) | Return | Sharpe | MaxDD | PF | Exp ròng (bps) | p bootstrap | Ngẫu nhiên %ile | Chi phí ×1,5 | Trễ 1 nến | Bỏ top 5% |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lgbm_H60_tau0.65 | Tham khảo (không được chọn trên validation) | 1 | 25 | 0.25% | 1.59 | 0.00% | n/a | 71.0 | n/a | 0.92 | 23 | 15 | 0 |
| rev_ret_15_z_H240 | Tham khảo (không được chọn trên validation) | 4616 | -33330 | -333.30% | -12.14 | 333.66% | 0.65 | -14.0 | 1.000 | 0.50 | -49283 | -33382 | -43935 |
| dc_sig8 | Tham khảo (không được chọn trên validation) | 143 | 1646 | 16.46% | 1.52 | 10.02% | 1.56 | 13.7 | 0.391 | 0.46 | 1499 | 872 | -1758 |

Baseline mua & giữ 5 coin: 9.60% (MaxDD 21.94%, Sharpe 0.55). Không giao dịch: 0%.

- Mô hình LGBM H=60 trên test: skill -0.0010, AUC 0.5127, n 69,269.

Funding sau mốc cuối cùng có dữ liệu được ước tính bằng mức funding cuối cùng đã biết.

Kết quả backtest không phải lợi nhuận thực tế. Không có chiến lược nào được coi là chắc chắn hiệu quả.
