# Kết luận — Track M15: vào lệnh khung M15 bằng tổ hợp chỉ báo

Ngày: 2026-10-10 · Nhánh `ind15` · Việc N5a (spec M15 §6: không tổ hợp nào đạt → viết kết luận, dừng hỏi chủ repo).
Nhãn: [F] đã đo trên dữ liệu thật · [A] giả định · [I] suy luận · [L] giới hạn.

## Kết luận một câu

**Không tổ hợp nào đạt tiêu chí "đạt" chốt trước (0/97).** Chuyển từ M1 sang M15 làm lợi thế trước phí lớn hơn
3–10 lần và đủ lệnh để đo, nhưng lợi thế đó (≈ +0,016%/lệnh) vẫn nhỏ hơn nhiều chi phí ≈ 0,10%/lệnh, nên sau phí
vẫn âm (≈ −0,09%/lệnh), gần như y hệt M1. Giai đoạn test 2026-05-16 → 2026-10-08 **không được dùng**.

Đây không phải lời hứa hay dự báo lợi nhuận. Kết quả backtest không phải lợi nhuận thực tế.

## 1. Đã chạy trên dữ liệu thật [F]

Dữ liệu như track M1 (Binance Vision, SHA256), nến M15 70.080 / H1 17.520 / H4 4.380 mỗi symbol, dựng từ M1.
Đơn lẻ chỉ trên train (2024-10-09 → 2025-12-20); tổ hợp qua walk-forward 13 tháng (2025-05 → 2026-05).

| Bước | Kết quả chính |
|---|---|
| Sóng 1,5% (đáp án) | sóng nhanh ≤ 8 giờ tăng/giảm: BTC 681/668 · ETH 1.593/1.578 · BNB 913/900 · SOL 2.069/2.065 · XRP 2.195/2.199; nến đi ngang 21–72% |
| 99 chỉ báo đơn lẻ, Bảng A | lift cao nhất ≈ 1,40–1,43 (SuperTrend+HTF, Bollinger+HTF, Donchian+HTF, 52-Week High/Low); precision ngẫu nhiên ≈ 0,42 |
| Đơn lẻ, Bảng B (TP 1,2% / SL 0,8%, giữ ≤ 8 giờ) | **0/158** cấu hình có ròng trung vị > 0; gross trung vị +0,011%/lệnh, ròng −0,093%/lệnh; tốt nhất SuperTrend+HTF: gross +0,081%, ròng −0,020% |
| Độ nhạy đơn lẻ | phí 0,02%/chiều: 6/158 cấu hình ròng trung vị > 0 (tốt nhất +0,040%); TP 1,8%, bỏ funding, trượt 3 tick: vẫn 0/158 |
| Tổ hợp kích hoạt + xác nhận (train) | 1.800 lần thử; 1.752 đạt precision ≥ 1,2× ngẫu nhiên, tất cả đủ ≥ 30 tín hiệu/symbol |
| Walk-forward | 97 tổ hợp, 252.687 lệnh ngoài mẫu (trung vị 1.501/tổ hợp); gộp gross +0,016%, ròng **−0,087%/lệnh**; 3/97 tổ hợp ròng > 0 |
| Tiêu chí §6 | (1) ≥ 100 lệnh: 97 · (2) ròng > 0 và CI95 dưới > 0: **0** · (3) DSR ≥ 0,95: **0** (lớn nhất 0,0008) · (4) ≥ 3/5 symbol dương: 3 · (5) không đổi dấu ±20%: 7 → **đạt cả 5: 0** |
| Chống "may mắn" | 29.394 lần thử track M15 (206.180 cộng M1); PBO 0,311 |
| Tổ hợp tốt nhất | Chande Kroll Stop (kích hoạt) + Average Price + Donchian (xác nhận): 628 lệnh, +0,048%/lệnh, CI95 [−0,047; +0,156], chỉ được chọn ở 1/13 fold, trên train −0,067%/lệnh, ×0,8 tham số → −0,006% (đổi dấu) |
| Cấu trúc lệnh (trung vị 97 tổ hợp) | thắng 38%; chạm TP 32%, SL 42%, tín hiệu ngược 18%, hết giờ 7%; giữ TB 156 phút; phí 0,100%/lệnh, trượt 0,003%, funding ≈ 0 |

File: `reports/ind15/` (`single_tableA/B*.csv`, `candidates.csv`, `combos_tableA*.csv`, `combos_tableB.csv`,
`top10.md`, `m1_vs_m15.md`, `wf/summary.json`, `trials.csv`).

## 2. Suy luận [I]

- Chỉ báo có thông tin thật về hướng sóng (lift ≈ 1,3–1,4, precision tổ hợp 0,53–0,56 so với ngẫu nhiên 0,42–0,43),
  nhưng chuyển thông tin đó thành lợi nhuận chỉ được ≈ +0,01–0,02%/lệnh trước phí. Với phí taker 0,05%/chiều,
  mỗi lệnh mất 0,10% → âm ở cả M1 và M15.
- Phí là yếu tố quyết định: chỉ khi phí giảm còn 0,02%/chiều mới có vài chỉ báo đơn lẻ dương trên train. Đổi phí là
  đổi phạm vi (CLAUDE.md), chưa làm.
- PBO 0,31 (tốt hơn M1 0,50) cho thấy ít lần thử giúp việc chọn ít ngẫu nhiên hơn, nhưng DSR ≈ 0: không tổ hợp nào
  có Sharpe vượt mức kỳ vọng do thử nhiều lần.
- 3 tổ hợp dương đều âm trên train và chỉ được chọn ở 1 tháng → nhiều khả năng là may mắn của tháng đó.

## 3. Chưa kiểm chứng

- Giai đoạn 2026-05-16 → 2026-10-08 (đã dùng ở track chính PR #2 nên chỉ còn "bán sạch" [L]): **không chạy**, vì không
  tổ hợp nào đạt (spec M15 §7). Không đăng ký forward holdout.
- Phí maker / lệnh limit, khung H1/H4 để vào lệnh, giữ > 8 giờ, ngưỡng sóng khác 1,5%, symbol khác: ngoài phạm vi.

## 4. Giả định [A]

- TP 1,2% / SL 0,8%, giữ ≤ 8 giờ, phí taker 0,05%/chiều, trượt 1 tick/chiều (cả TP), funding thật.
- "1 ngày" = 96 nến M15; Zig Zag 1,5%; Multi-Timeframe MA dùng H1; dạng trạng thái = hướng sự kiện gần nhất.
- Quy ước N4 (ứng viên, filter tốt nhất, ≥ 30 tín hiệu, xếp hạng, độ bền) chốt trong CHANGELOG trước khi chạy.

## 5. Giới hạn [L]

- Chỉ OHLCV: thứ tự chạm TP/SL trong 1 nến M1 không biết → TP và SL cùng nến M1 tính SL (thận trọng). M15 đã giảm
  vấn đề này nhiều so với M1 vì mô phỏng trên từng nến M1.
- Không có spread lịch sử: trượt giá là giả định.
- Multiple testing: lần thử được đếm (29.394 + M1); lựa chọn ngầm (tham số mặc định, cách định nghĩa trạng thái) không đếm được hết.
- Chỉ nghiên cứu: không giao dịch thật, không gửi lệnh, không dùng API key.

## 6. Câu hỏi cho chủ repo (hướng tiếp)

Tôi không tự đổi phạm vi. Các hướng có thể (chủ repo chọn):

1. **Dừng track chỉ báo** — kết luận: tổ hợp chỉ báo TradingView không lãi sau phí taker ở khung M1 và M15.
2. **Kiểm tra phí thấp hơn** (maker 0,02%/chiều, lệnh limit) — đổi phạm vi phí, cần mô phỏng khả năng khớp lệnh limit; là lần thử mới.
3. **Khung dài hơn** (vào lệnh H1/H4, giữ nhiều ngày, sóng ≥ 3–5%) — chi phí chỉ còn vài % mục tiêu; là track mới.
4. Hướng khác do chủ repo nêu.
