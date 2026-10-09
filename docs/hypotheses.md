# Đăng ký giả thuyết trước (pre-registration)

Tài liệu này được commit **trước** khi chạy phân tích sóng, khai phá quy luật và mô hình.
Thời điểm commit trên Git là bằng chứng. Mọi giả thuyết thêm sau khi đã xem dữ liệu được gắn nhãn
**exploratory** và phải qua cùng quy trình kiểm định, có điều chỉnh multiple testing.

## Dữ liệu và phân chia (đã khóa)

- 5 symbol, nến 1m, 2024-10-09 → 2026-10-08 UTC.
- Train 2024-10-09 → 2025-12-20 · Validation 2025-12-21 → 2026-05-15 · Final test 2026-05-16 → 2026-10-08.
- Embargo 1 ngày giữa các tập. Mọi phân tích mô tả và lựa chọn chỉ dùng train + validation.
- Final test chạy **một lần** bằng `python -m kh.cli final --confirm-final` sau khi khóa
  `configs/locked_strategies.yaml`.

## Nhãn dự báo (đã khóa)

- Điểm lấy mẫu: đóng cửa mỗi nến thứ 15 (phút chia hết cho 15), bỏ mẫu có nến filler trong 60 phút trước
  hoặc trong khoảng dự báo.
- Vào lệnh giả định: giá mở cửa nến kế tiếp (t+1).
- Rào đối xứng b = 1,0 × σ_1m(t) × √H, với σ_1m là EWMA (halflife 1 ngày) của log return 1 phút.
- H ∈ {60, 240} phút. Nhãn = hướng chạm rào trước; nếu cả hai rào bị chạm trong cùng một nến → nhãn
  "ambiguous" (loại khỏi bài toán hướng, nhưng trong backtest tính là chạm SL trước); nếu hết H mà
  chưa chạm → dấu của return tại t+H.
- Ngưỡng hòa vốn: với phí taker 0,05% + slippage 2 bps mỗi chiều (14 bps khứ hồi), xác suất thắng cần
  thiết p* = 0,5 + 0,0014 / (2b). Một quy luật chỉ có ý nghĩa giao dịch nếu vượt p*.

## Giả thuyết định trước

| ID | Giả thuyết | Kiểm định chính | Chiều |
|---|---|---|---|
| H1 | Theo sóng DC (thang σ×4): vào lệnh theo hướng tại xác nhận, thoát tại xác nhận ngược → log return trung bình > 0 trước phí | trung bình, block bootstrap theo ngày | > 0 |
| H2 | Breakout (đóng cửa > đỉnh 240 phút trước đó) → P(chạm rào trên trước, H=60) > tần suất cơ sở; breakdown đối xứng | chênh lệch tỷ lệ, bootstrap | > 0 |
| H3 | Co hẹp biến động (vol_ratio_60_1440 thuộc decile thấp nhất) → |return 60 phút|/σ lớn hơn bình thường | chênh lệch trung bình | > 0 |
| H4 | Đảo chiều ngắn hạn: return 15 phút (chuẩn hóa) có IC âm với return 60 phút tới | IC Spearman theo ngày, Newey-West | < 0 |
| H5 | Funding cực dương (decile cao nhất) → return 240 phút tới thấp hơn | IC funding vs return 240 | < 0 |
| H6 | OI tăng cùng giá tăng (60 phút) → tiếp diễn; OI tăng cùng giá giảm → tiếp diễn giảm | IC của ret60 × sign(ΔOI60) | > 0 |
| H7 | Mất cân bằng taker 15 phút có IC khác 0 với return 60 phút tới | IC hai phía | ≠ 0 |
| H8 | Mô hình LightGBM gộp có log-loss skill > 0 so với tần suất cơ sở trong walk-forward, ở ≥ 3/5 coin | skill trung bình theo fold | > 0 |

**Quét exploratory**: mọi đặc trưng × symbol (+ gộp) × H ∈ {60, 240}: IC Spearman theo ngày.
Kiểm soát FDR Benjamini–Yekutieli q = 0,10 trên toàn bộ p-value của train; quy luật sống sót phải
cùng dấu trên validation với p < 0,05 (một phía) và cùng dấu ở ≥ 3/5 coin.

## Tiêu chí trạng thái quy luật

- **Không đạt**: không qua FDR trên train, hoặc đổi dấu / p ≥ 0,05 trên validation.
- **Đạt một phần**: qua train + validation nhưng không cùng dấu ở ≥ 3/5 coin, hoặc không vượt ngưỡng hòa vốn p*.
- **Có tiềm năng nhưng chưa đủ bằng chứng**: qua tất cả tiêu chí thống kê nhưng chưa qua backtest có chi phí.

## Tiêu chí chọn chiến lược vào final test (trên validation, sau chi phí)

1. Expectancy ròng > 0 và cận dưới khoảng tin cậy bootstrap 90% > 0.
2. Profit factor > 1,1 và ≥ 100 giao dịch.
3. Vẫn dương khi chi phí × 1,5 và khi trễ vào lệnh 1 nến.
4. Vẫn dương khi bỏ 5% giao dịch lãi lớn nhất.
5. Deflated Sharpe Ratio > 0,95 khi tính toàn bộ số biến thể đã thử; PBO < 0,5.

## Tiêu chí trên final test

- **Đạt kiểm định ngoài mẫu**: expectancy ròng > 0 với p bootstrap một phía < 0,05; PF > 1,1;
  ≥ 100 giao dịch; dương ở ≥ 3/5 coin; dương khi chi phí × 1,5; dương khi bỏ 5% giao dịch lãi lớn nhất.
- **Đạt một phần**: ròng > 0 nhưng thiếu ít nhất một tiêu chí trên.
- **Không đạt**: ròng ≤ 0.

Không có chiến lược nào được gọi là "có lợi nhuận" chỉ dựa trên train hoặc validation.
