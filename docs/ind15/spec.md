# Đặc tả — Track M15: vào lệnh khung M15 bằng tổ hợp chỉ báo

Ngày chốt: 2026-10-10. Chủ repo yêu cầu: "M1 không khả quan thì đổi sang vào lệnh bằng khung M15".
Track này **dùng lại toàn bộ code của track M1** (`src/kh/ind/`, `src/kh/backtest/`), chỉ đổi khung và các tham số dưới đây.
Phần nào không nói ở đây thì giữ như `docs/ind/spec.md`.

## 0. Vì sao đổi và bài học từ M1

Kết quả M1 [F]: lợi nhuận trước phí trung vị mỗi lệnh ≈ +0,001%, phí + trượt giá ≈ 0,12% → mọi cấu hình âm. Tổ hợp 4 chỉ báo trong cửa sổ 3 nến bắn quá ít tín hiệu (1–25 lệnh), 176.786 lần thử, DSR ≈ 0, PBO 0,50.

Track M15 sửa 4 điểm:

1. **Sóng lớn hơn, giữ lâu hơn** → chi phí chỉ còn ~10% mục tiêu thay vì ~25%.
2. **Ít lần thử hơn** (≤ 2.000 thay vì 177 nghìn) → giảm "trúng nhờ may".
3. **Tổ hợp kiểu kích hoạt + xác nhận** thay vì "mọi chỉ báo cùng phát sự kiện trong 3 nến" → đủ lệnh để đo.
4. **Tiêu chí "đạt" chốt trước** (§6) → biết khi nào dừng.

## 1. Đã chốt

| Mục | Giá trị |
|---|---|
| Symbol, cửa sổ, chia tập | như track M1 (train 2024-10-09 → 2025-12-20, validation → 2026-05-15, test 2026-05-16 → 2026-10-08) |
| Khung vào lệnh | **M15**: tín hiệu tính khi nến M15 đóng, vào lệnh ở giá mở nến M15 kế tiếp |
| Khung lọc hướng | **H1 + H4** (resample từ M1, chỉ dùng nến đã đóng) |
| Mô phỏng thoát lệnh | trên **đường giá M1** bên trong (biết thứ tự chạm TP/SL chính xác hơn); TP và SL cùng chạm trong 1 nến M1 → tính SL |
| Sóng hợp lệ | ZigZag **1,5%** trên high/low M15 [A]; độ nhạy 1,0% / 2,0% chỉ để báo cáo |
| Sóng nhanh | đi được ≥ 1,5% trong ≤ **8 giờ** (32 nến M15) tính từ nến sau điểm xuất phát |
| Giữ lệnh tối đa | **8 giờ** (32 nến M15), hết giờ đóng ở close |
| "Bắt được sóng" | tín hiệu cùng chiều trong sóng, phần còn lại từ giá vào ≥ **0,9%** (60% ngưỡng, như M1: 0,3/0,5) |
| Đi ngang | cửa sổ ≥ 8 giờ mà (high max − low min)/close < 1,5% |
| Nhịp hồi | ZigZag 0,6% bên trong sóng 1,5% |

## 2. Dữ liệu (việc N0)

- Dùng lại dữ liệu M1 đã tải (manifest + SHA256). Thêm resample **H4** (4.380 nến/symbol).
- Bảng M15 (70.080 nến/symbol) là "nến tín hiệu"; bảng M1 là "đường giá" để mô phỏng lệnh.
- `is_filler` của M15/H1/H4 = có ít nhất 1 nến M1 filler bên trong. Không vào lệnh ở nến filler và 2 nến M15 sau đó.

## 3. Chỉ báo trên M15 (việc N2)

- Cùng registry 99 chỉ báo đã triển khai, tham số mặc định TradingView, tính trên nến M15.
- Tham số tính theo **thời gian** được quy đổi: cửa sổ "1 ngày" = 96 nến M15 (52-Week High/Low, trung vị của filter, VWAP reset 00:00 UTC giữ nguyên). Zig Zag (chỉ báo) dùng độ lệch 1,5%. Ghi từng thay đổi vào phiếu và CHANGELOG.
- Mỗi chỉ báo directional có **2 dạng**, tính cùng lúc:
  - **Sự kiện** (như M1): nến điều kiện vừa chuyển sang đúng, ví dụ giá cắt lên EMA → +1.
  - **Trạng thái**: điều kiện đang đúng, ví dụ giá đang trên EMA → +1, dưới → −1, còn lại 0.
- HTF: hướng H1 và H4 theo quy tắc EMA50 như M1 (Tăng nếu close > EMA50 và EMA50 > EMA50 cách 3 nến). Long chỉ khi không khung nào Giảm; Short chỉ khi không khung nào Tăng.
- Test chống nhìn tương lai chạy lại cho mọi chỉ báo trên M15 và cho H1/H4 (nến khung lớn chỉ có hiệu lực sau khi đóng).

## 4. Chấm đơn lẻ (việc N3) — chỉ Train

- Bảng A, Bảng B như M1 nhưng trên M15, có/không HTF, từng symbol + trung vị + kém nhất.
- Backtest baseline [A], cố định cho mọi chỉ báo:

| Tham số | Baseline | Độ nhạy |
|---|---|---|
| Take profit | 1,2% | 0,8% / 1,8% |
| Stop loss | 0,8% | 0,5% / 1,2% |
| Phí | taker 0,05%/chiều | 0,02% / 0,07% |
| Trượt giá | 1 tick/chiều | 3 tick |
| Funding | tính thật theo mốc 8 giờ | có / không |
| Thoát khác | tín hiệu ngược chiều; hết 8 giờ | — |

- Báo thêm **lợi nhuận trước phí (gross) mỗi lệnh** ở bảng tóm tắt, để so trực tiếp với M1.

## 5. Tổ hợp (việc N4) — chỉ Train, rồi walk-forward

1. **Ứng viên:** 10 directional + 3 filter, chọn theo điểm như M1 (C1), yêu cầu trung vị ≥ 100 sự kiện mỗi chiều/symbol trong train. Loại trùng tương quan > 0,8.
2. **Cấu trúc tổ hợp:** 1 chỉ báo **kích hoạt** (dạng sự kiện) + 1 hoặc 2 chỉ báo **xác nhận** (dạng trạng thái, cùng chiều tại nến kích hoạt) + bộ lọc ∈ {không lọc, filter tốt nhất trong 3}.
   - Số tổ hợp: 10 × (9 + 36) = 450 × 2 (filter) × 2 (HTF) = **1.800 lần thử**. Ghi số thật vào `reports/ind15/trials.csv`.
3. **Bảng A tổ hợp:** điều kiện ≥ 30 lệnh/symbol (trung vị) trong train **và** precision ≥ 1,2 × ngẫu nhiên. Xếp theo recall sóng nhanh, hoà theo precision. Giữ top 30.
4. **Bảng B:** walk-forward như M1 (fold = tháng 2025-05 → 2026-05, train mở rộng, embargo 1 ngày, làm lại chọn ứng viên + Bảng A trong train của từng fold). Xếp theo expectancy ròng → profit factor → max drawdown.
5. DSR (dùng số lần thử của track M15; báo thêm bản dùng tổng M1 + M15), PBO, CI95 bootstrap khối ngày, leave-one-coin-out, độ nhạy ±20% tham số — như M1.

## 6. Tiêu chí "đạt" (chốt trước khi chạy)

Một tổ hợp chỉ được gọi là **đạt** khi trên walk-forward ngoài mẫu (gộp 5 symbol, phí baseline):

1. ≥ 100 lệnh;
2. expectancy ròng > 0 **và** cận dưới CI95 bootstrap > 0;
3. DSR ≥ 0,95 (theo số lần thử của track M15);
4. expectancy ròng > 0 ở ≥ 3/5 symbol;
5. không đổi dấu khi tham số × 0,8 và × 1,2.

Không tổ hợp nào đạt → viết `docs/ind15/conclusion.md` và **dừng, hỏi chủ repo**. Không nới tiêu chí sau khi xem kết quả.

## 7. Test cuối (việc N5) — dừng hỏi trước

- [L] Giai đoạn 2026-05-16 → 2026-10-08 **đã bị mở** ở track chính (PR #2, `reports/final_test/`, 2026-10-09). Không tổ hợp chỉ báo M15 nào được đánh giá trên đó, nhưng người nghiên cứu đã thấy kết quả giai đoạn này → ghi rõ là "test bán sạch".
- Nếu có tổ hợp đạt §6: hỏi chủ repo, rồi chạy test 2026-05-16 → 2026-10-08 đúng 1 lần **và** đăng ký **forward holdout** từ 2026-10-09 trở đi (dữ liệu mới hoàn toàn): ghi quy tắc + hash vào `configs/locked_strategies_ind15.yaml`, kiểm tra lại sau ≥ 3 tháng mà không chỉnh gì.

## 8. Bàn giao

Như M1, đặt trong `reports/ind15/` và `docs/ind15/`; thêm `reports/ind15/m1_vs_m15.md`: bảng so sánh gross/net mỗi lệnh, số lệnh, DSR, PBO giữa hai track.
