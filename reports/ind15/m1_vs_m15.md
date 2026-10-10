# So sánh track M1 và M15

Mọi số [F] đo trên dữ liệu thật, train (đơn lẻ) và walk-forward 13 tháng 2025-05 → 2026-05 (tổ hợp); chưa dùng giai đoạn test.
Kết quả backtest tính theo % notional mỗi lệnh, phí taker 0,05%/chiều, trượt 1 tick/chiều, funding thật.

| Chỉ số | M1 | M15 |
|---|---|---|
| Khung vào lệnh / giữ tối đa | M1 / 15 phút | M15 / 8 giờ |
| TP / SL baseline [A] | 0,45% / 0,30% | 1,2% / 0,8% |
| Chi phí khứ hồi ≈ (phí 0,10% + trượt) | ≈ 22% TP | ≈ 8–9% TP |
| Đơn lẻ (train): số lệnh trung vị/symbol | 25410 | 1704 |
| Đơn lẻ: gross trung vị %/lệnh | 0.0012 | 0.0114 |
| Đơn lẻ: ròng trung vị %/lệnh | -0.1005 | -0.0930 |
| Đơn lẻ: số cấu hình có ròng trung vị > 0 | 0/158 | 0/158 |
| Số lần thử (trials.csv) | 176,786 | 29,394 |
| Walk-forward: tổ hợp đánh giá ngoài mẫu | 242 | 97 |
| Walk-forward: tổng lệnh ngoài mẫu | 5,502 | 252,687 |
| Walk-forward: lệnh trung vị mỗi tổ hợp | 14 | 1501 |
| Walk-forward gộp: gross %/lệnh | 0.0048 | 0.0161 |
| Walk-forward gộp: ròng %/lệnh | -0.0984 | -0.0871 |
| Tổ hợp ròng > 0 / có ≥ 100 lệnh mà ròng > 0 | 34 / 0 | 3 / 3 |
| DSR lớn nhất | 0.0003 | 0.0008 |
| PBO | 0.504 | 0.311 |
| Tổ hợp đạt tiêu chí chốt trước | — (M1 không có tiêu chí §6) | 0 / 97 |

Đọc bảng [I]: M15 có lợi thế gộp phí lớn hơn M1 khoảng 3–10 lần và đủ lệnh để đo (mỗi tổ hợp hàng trăm–hàng nghìn lệnh), nhưng lợi thế đó (≈ +0,01–0,02%/lệnh) vẫn nhỏ hơn nhiều chi phí ≈ 0,10%/lệnh, nên ròng vẫn âm ≈ −0,09%/lệnh như M1. PBO M15 thấp hơn (ít lần thử hơn) nhưng DSR vẫn ≈ 0.
