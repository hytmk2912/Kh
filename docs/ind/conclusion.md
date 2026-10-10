# Kết luận — Lướt sóng M1 bằng tổ hợp chỉ báo

Ngày: 2026-10-10 · Nhánh `ind-scalp` · Quyết định của chủ repo: **phương án 2 — không mở tập test khoá** (2026-05-16 → 2026-10-08 chưa chạy chiến lược chỉ báo nào trên đó; lưu ý giai đoạn này đã được dùng một lần làm final test của track chính PR #2, nên không còn hoàn toàn "sạch" [L]).

Nhãn: [F] đã đo trên dữ liệu thật · [A] giả định · [I] suy luận · [L] giới hạn.

## Kết luận một câu

**Không tìm được tổ hợp 2–4 chỉ báo nào lãi sau phí một cách đáng tin** khi lướt sóng M1 (giữ ≤ 15 phút, TP 0,45% / SL 0,30%, phí taker 0,05%/chiều) trên 5 coin trong train + validation. Theo spec §7, đây là kết quả hợp lệ.

Đây **không phải** lời hứa hay dự báo lợi nhuận. Kết quả backtest không phải lợi nhuận thực tế.

## 1. Đã chạy trên dữ liệu thật [F]

Dữ liệu: Binance Vision, 5 symbol (BTC, ETH, BNB, SOL, XRP USDⓈ-M), 2024-10-09 → 2026-10-08, mỗi symbol 1.051.200 nến M1, 0 thiếu, 0 trùng, SHA256 khớp. Mọi số dưới đây chỉ dùng train (2024-10-09 → 2025-12-20) và validation (2025-12-21 → 2026-05-15).

| Bước | Kết quả chính |
|---|---|
| Sóng 0,5% (đáp án) | sóng nhanh ≤ 15 phút: BTC ≈ 8,3 nghìn · ETH ≈ 22,5 nghìn · BNB ≈ 11,6 nghìn · SOL ≈ 33,1 nghìn · XRP ≈ 36,6 nghìn; tỷ lệ nến đi ngang 49–85% |
| 99 chỉ báo đơn lẻ, Bảng A (bắt sóng) | lift (precision ÷ precision ngẫu nhiên) cao nhất khi đủ mẫu ≈ 1,33–1,34 (Zig Zag, Keltner, Donchian); precision ngẫu nhiên ≈ 0,40 |
| Đơn lẻ, Bảng B (backtest sau phí) | **0/158** cấu hình có expectancy ròng trung vị > 0; trung vị trước phí +0,0012%/lệnh, sau phí −0,10%/lệnh; phí 0,02%/chiều vẫn −0,04% |
| 12.328 tổ hợp (2–4 chỉ báo × có/không HTF) | chỉ 30 đạt precision ≥ 1,5× ngẫu nhiên, và đều có rất ít tín hiệu (0 tổ hợp có ≥ 100 tín hiệu mỗi chiều) |
| Walk-forward 13 tháng (2025-05 → 2026-05) | 242 tổ hợp đánh giá ngoài mẫu; 34 có expectancy > 0 nhưng chỉ 1–25 lệnh mỗi tổ hợp; 0 tổ hợp ≥ 30 lệnh mà lãi |
| Gộp mọi lệnh ngoài mẫu | trước phí +0,005%/lệnh, sau phí **−0,098%/lệnh** |
| Thống kê chống "may mắn" | tổng số lần thử 176.786; DSR lớn nhất ≈ 0,0003 (cần ≥ 0,95); PBO 0,504 (≈ tung đồng xu) |
| Chiến lược hạng 1 theo quy tắc (F1) | SuperTrend + 52-Week High/Low + TRIX + Connors RSI, có HTF: **1 lệnh** ngoài mẫu; trên train 23 lệnh, −0,041%/lệnh |
| Bộ lọc HTF (M15 + H1, EMA50) | trên 32 cặp tổ hợp: có HTF −0,071%/lệnh, không HTF −0,099%/lệnh — giảm lỗ, không làm thành lãi |

File chi tiết: `reports/ind/single_tableA.csv`, `single_tableB*.csv`, `combos_tableA.csv`, `combos_tableB.csv`, `top10.md`, `wf/summary.json`, `trials.csv`; chiến lược và bằng chứng: `docs/ind/strategy.md`.

## 2. Suy luận [I]

- Chỉ báo trên M1 có một chút thông tin về hướng sóng ngắn (lift ≈ 1,3), nhưng lợi thế trước phí gần bằng 0 (+0,005%/lệnh), nhỏ hơn rất nhiều so với chi phí một vòng ≈ 0,10% phí + trượt giá. Vì vậy sau phí gần như mọi cấu hình đều âm khoảng −0,1%/lệnh.
- Các tổ hợp "lãi" trong Bảng B là kết quả hiển nhiên của việc thử rất nhiều lần: với 176.786 lần thử, chắc chắn sẽ có vài tổ hợp thắng trên 1–5 lệnh dù không có lợi thế thật. DSR ≈ 0 và PBO ≈ 0,5 khẳng định điều này.
- Đòi hỏi đồng thuận nhiều chỉ báo làm precision tăng nhưng số tín hiệu giảm mạnh, nên không đủ lệnh để kiểm chứng.
- Mở tập test khoá cho chiến lược hạng 1 sẽ chỉ cho khoảng 5–10 lệnh (ước tính theo tần suất train) — không đủ để kết luận, nên giữ tập test cho nghiên cứu sau là hợp lý.

## 3. Chưa kiểm chứng

- Tập test khoá 2026-05-16 → 2026-10-08: **chưa mở trong track này** (không có `reports/ind/final_test.json`). [L] Cùng giai đoạn đã là final test của track chính (PR #2, chiến lược khác), nên dùng lại sau này phải ghi rõ là "test bán sạch".
- Phí maker / lệnh limit, khung khác M1, giữ lệnh > 15 phút, ngưỡng sóng khác 0,5%, coin khác: ngoài phạm vi đã chốt, chưa thử.
- Tác động thị trường khi khối lượng lớn: không mô phỏng.

## 4. Giả định [A]

- Phí taker 0,05%/chiều; trượt giá 1 tick/chiều kể cả lệnh TP; tick suy ra từ dữ liệu.
- TP 0,45% / SL 0,30%; tín hiệu ngược chỉ để thoát, không mở lệnh đảo chiều.
- Mỗi sự kiện chỉ báo còn hiệu lực 3 nến; filter = giá trị > trung vị 1.440 nến trước; 52-Week High/Low dùng cửa sổ 1 ngày.
- Mọi quy ước khác ghi trong `CHANGELOG.md`.

## 5. Giới hạn [L]

- **Chỉ có OHLCV M1:** không biết đường đi của giá trong nến. Khi TP và SL cùng nằm trong một nến, luôn tính SL trước (thận trọng) — kết quả thật có thể khác.
- **Không có spread bid/ask lịch sử:** trượt giá là giả định; thực tế lúc biến động mạnh có thể lớn hơn nhiều.
- **Multiple testing:** 176.786 lần thử được đếm và đưa vào DSR; vẫn có thể còn những lựa chọn ngầm (tham số mặc định, quy tắc tín hiệu) không được đếm.
- Funding 2026-10-01..08 chưa có trên Binance Vision (chỉ ảnh hưởng tập test khoá, chưa dùng).
- Nhãn sóng nhìn lại quá khứ, chỉ dùng để chấm; không phải tín hiệu giao dịch được.
- Chỉ nghiên cứu: không giao dịch thật, không gửi lệnh, không dùng API key.
