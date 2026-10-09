# Chiến lược chọn cho test khoá (việc F1)

Trạng thái: **chờ chủ repo duyệt** · Chưa mở tập test khoá (2026-05-16 → 2026-10-08).
Nhãn: [F] đã đo · [A] giả định · [I] suy luận · [L] giới hạn. Mọi số dưới đây đo trên train + validation (walk-forward ngoài mẫu), không phải lợi nhuận thực tế.

## 1. Cách chọn (chốt trước trong spec §6–7)

Lấy dòng đầu của Bảng B walk-forward (`reports/ind/combos_tableB.csv`): chỉ giữ tổ hợp có expectancy ròng > 0 ở phí baseline, xếp theo expectancy ròng → profit factor → max drawdown → số symbol dương. Không chọn lại theo tiêu chí khác sau khi xem kết quả (đó là data snooping — chọn theo kết quả đã nhìn thấy).

→ **Bảng B hạng 1: SuperTrend + 52-Week High/Low + TRIX + Connors RSI, có bộ lọc HTF.** Mã: `i018+i035+i049+i042`, `htf=True`. Commit chứa Bảng B: `113a5c4`.

## 2. Quy tắc giao dịch

Tất cả trên nến M1, tín hiệu tính khi nến t đã đóng, vào lệnh ở giá mở nến t+1.

| Thành phần | Quy tắc | Tham số |
|---|---|---|
| SuperTrend | đổi sang xu hướng tăng → sự kiện Long; đổi sang giảm → sự kiện Short | ATR 10 (RMA), hệ số 3,0 |
| 52-Week High/Low | close vượt đỉnh của 1.440 nến trước → Long; thủng đáy 1.440 nến trước → Short | 1.440 nến (1 ngày) [A] — spec §3 đổi 52 tuần thành 1 ngày |
| TRIX | TRIX cắt lên 0 → Long; cắt xuống 0 → Short | 18 |
| Connors RSI | CRSI cắt lên 50 → Long; cắt xuống 50 → Short | RSI 3, streak 2, rank 100, ngưỡng 50 [A] |
| Đồng thuận | mỗi sự kiện còn hiệu lực 3 nến (nến phát + 2 nến sau). **Long** khi cả 4 chỉ báo có sự kiện Long còn hiệu lực, ít nhất 1 sự kiện Long mới phát ở nến t, và không chỉ báo nào có sự kiện Short còn hiệu lực. Short đối xứng | 3 nến |
| HTF (khung lớn) | hướng mỗi khung M15, H1 (chỉ nến đã đóng): Tăng nếu close > EMA50 và EMA50 > EMA50 cách 3 nến; Giảm nếu ngược lại cả hai. Long chỉ khi không khung nào Giảm; Short chỉ khi không khung nào Tăng | EMA 50, cách 3 nến |
| Chốt lời / cắt lỗ | TP 0,45%, SL 0,30% tính từ giá mở nến vào; TP và SL cùng chạm trong một nến → tính SL | [A] spec §4 |
| Thoát thời gian | giữ tối đa 15 phút, hết giờ đóng ở close nến thứ 15 | spec |
| Thoát sớm | tín hiệu ngược chiều của chính tổ hợp tại nến k → đóng ở open nến k+1 (không mở lệnh đảo chiều cùng lúc) | [A] CHANGELOG |
| Không giao dịch | nến vào là filler hoặc trong 30 phút sau filler; đang có lệnh cùng symbol | [A] |
| Chi phí | phí taker 0,05%/chiều [A]; trượt giá 1 tick/chiều kể cả lệnh TP [A]; funding thật theo mốc 8 giờ | tick suy ra từ dữ liệu [I] |

Bộ lọc và số chứng minh có ích ngoài mẫu (spec §7 yêu cầu):
- **HTF:** trên 32 tổ hợp được đánh giá ngoài mẫu cả hai bản (có/không HTF), expectancy ròng gộp: có HTF −0,071%/lệnh (326 lệnh), không HTF −0,099%/lệnh (564 lệnh) [F]. HTF giảm lỗ nhưng cả hai vẫn âm. Riêng tổ hợp được chọn, bản không HTF không lọt top ở fold nào nên không có số so sánh trực tiếp [L].
- **Chặn 30 phút sau filler:** quy tắc an toàn dữ liệu (nến sàn bảo trì), không phải bộ lọc tối ưu lợi nhuận; không có số đo riêng [L].

## 3. Quản lý vốn (giả định nghiên cứu, spec §7)

- Rủi ro mỗi lệnh: **0,25% equity** [A] (mức thấp của khoảng 0,25–0,5%).
- Notional (giá trị vị thế) = equity × 0,25% ÷ (SL 0,30% + phí 2 chiều 0,10% + trượt giá 2 tick tính theo %).
  Ví dụ trượt giá 0,02%: notional = equity × 0,0025 ÷ 0,0042 ≈ **0,60 × equity**; mức lỗ khi chạm SL ≈ **0,25% equity** (có thể lớn hơn nếu giá mở cửa nhảy qua SL).
- Ký quỹ: cách ly (isolated), đòn bẩy **5×** [A] → ký quỹ ≈ 0,12 × equity/lệnh; tối đa 5 lệnh cùng lúc (mỗi symbol 1 lệnh) ≈ 0,60 × equity ký quỹ. Giá thanh lý cách giá vào khoảng 19%, rất xa SL 0,30% [I].
- Không dùng đòn bẩy cao để làm đẹp kết quả: kết quả backtest báo theo **% notional mỗi lệnh**; quản lý vốn chỉ đổi quy mô, không đổi dấu.

## 4. Bằng chứng hiện có — đọc kỹ trước khi duyệt

| Số đo | Giá trị | Nhãn |
|---|---|---|
| Số lệnh ngoài mẫu (13 tháng walk-forward) | **1** (SOLUSDT, short, chạm TP) | [F] |
| Expectancy ròng ngoài mẫu | +0,348%/lệnh (từ 1 lệnh) | [F] |
| Fold được chọn | 1/13 (tháng 2026-04) | [F] |
| Cùng tổ hợp trên toàn bộ train (trong mẫu) | 23 lệnh, expectancy ròng −0,041%/lệnh | [F] |
| DSR (Sharpe đã trừ hao 176.786 lần thử) | ≈ 0,000 (cần ≥ 0,95 mới gọi là có ý nghĩa) | [F] |
| PBO (xác suất chọn quá khớp, mọi tổ hợp) | 0,504 — ngang tung đồng xu | [F] |
| CI95 bootstrap | không tính được (< 10 lệnh) | [L] |
| Độ nhạy tham số × 0,8 / × 1,2 | +0,242% (2 lệnh) / +0,050% (2 lệnh), không đổi dấu | [F] |
| Leave-one-coin-out | không có lệnh (bỏ SOL ra thì tổ hợp không lọt top) | [F] |
| Toàn bộ 34 tổ hợp "lãi" ở Bảng B | 1–25 lệnh mỗi tổ hợp; 0 tổ hợp có ≥ 30 lệnh mà lãi | [F] |
| Gộp mọi lệnh ngoài mẫu của mọi tổ hợp | gộp phí +0,005%/lệnh, ròng −0,098%/lệnh | [F] |

Suy luận [I]:
- Một lệnh thắng không phân biệt được với may mắn. Với 176.786 lần thử, việc có vài tổ hợp lãi trên 1–5 lệnh là điều chắc chắn xảy ra ngay cả khi không có tổ hợp nào có lợi thế thật (DSR ≈ 0 và PBO ≈ 0,5 nói đúng điều này).
- Dự kiến trên test khoá (≈ 4,8 tháng): khoảng 5–10 lệnh nếu tần suất giống train (23 lệnh / 14,4 tháng) — quá ít để kết luận lãi hay lỗ.
- Bức tranh chung từ S2 + W1: chỉ báo trên M1 có chút khả năng bắt sóng (lift ≤ ~1,34) nhưng lợi thế gộp phí ≈ 0, nên sau phí 0,10%/vòng thì âm.

## 5. Test khoá sẽ chạy thế nào (việc F2, chỉ sau khi được duyệt)

- Đúng 1 lần, quy tắc ở mục 2, không chỉnh gì; 5 symbol, 2026-05-16 → 2026-10-08, phí baseline.
- Báo cáo có và không có funding (funding 2026-10-01..08 chưa có trên Binance Vision [L]).
- Lưu `reports/ind/final_test.json` + SHA256; viết `docs/ind/conclusion.md` tách [F]/[I]/[A]/[L].

## 6. Câu hỏi cho chủ repo

Theo quy tắc chốt trước, chiến lược trên là lựa chọn bắt buộc. Nhưng bằng chứng ở mục 4 cho thấy **không có tổ hợp nào có lợi thế đáng tin sau phí**. Chủ repo chọn một:

1. **Duyệt chạy test khoá với chiến lược hạng 1** (đúng quy tắc). Kết quả sẽ có rất ít lệnh; kết luận cuối vẫn ghi "chưa chứng minh được lợi thế".
2. **Không mở test khoá**, kết luận ngay: "không có chiến lược nào lãi sau phí một cách đáng tin" (spec §7: đây là kết quả hợp lệ). Test khoá được giữ nguyên cho một nghiên cứu sau.
3. Hướng khác (đổi tiêu chí, phạm vi…) — cần chủ repo ghi rõ; mọi thay đổi ghi vào CHANGELOG và tính là lần thử mới.
