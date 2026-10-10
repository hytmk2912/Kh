# Chỉ báo trên M15 — tham số quy đổi (việc N2)

Phiếu gốc của 101 chỉ báo: `docs/ind/indicator_cards.md`. Track M15 dùng **cùng phiếu, cùng code**, tính trên nến M15
(resample từ M1). Chỉ những chỗ dưới đây khác M1; mọi tham số tính theo **số nến** (độ dài MA, RSI 14, ATR 10…)
giữ mặc định TradingView, nên trên M15 chúng bao phủ thời gian dài gấp 15 lần. Code: `kh.ind.track.M15` +
`kh.ind.indicators.impl.timeframe()`.

| Chỉ báo / quy tắc | M1 | M15 | Nhãn |
|---|---|---|---|
| 52-Week High/Low | 1.440 nến (1 ngày) | **96 nến (1 ngày)** | [A] spec M15 §3 |
| Quy tắc filter chung (trung vị của chính nó trong 1 ngày trước) | 1.440 nến | **96 nến** | [A] spec M15 §3 |
| Historical Volatility (hệ số năm hoá) | √(365·1.440) | √(365·96) | chỉ đổi thang đo, filter so với trung vị nên không đổi tín hiệu |
| Volume Profile Fixed Range, Pivot Points Standard (ngày UTC trước) | ngày đủ 1.440 nến | ngày đủ 96 nến | theo thời gian, không đổi ý nghĩa |
| VWAP | reset 00:00 UTC | reset 00:00 UTC | không đổi |
| Zig Zag (chỉ báo) | độ lệch 0,5% | **1,5%** | [A] spec M15 §3 |
| Multi-Timeframe MA | SMA 20 của M15 đã đóng | **SMA 20 của H1 đã đóng** | [A] khung gốc đã là M15, dùng khung lớn kế tiếp |
| Bộ lọc HTF | M15 + H1 | **H1 + H4** (EMA50, cách 3 nến, chỉ nến đã đóng) | spec M15 §3 |

## Hai dạng tín hiệu của mỗi chỉ báo directional

- **Sự kiện** (cột `iNNN`): như M1 — +1/−1 tại nến điều kiện vừa chuyển sang đúng.
- **Trạng thái** (cột `iNNN_st`) [A]: hướng của sự kiện gần nhất tại hoặc trước nến t, giữ tới khi có sự kiện ngược;
  0 trước sự kiện đầu tiên. Với quy tắc "cắt" (giá cắt EMA, MACD cắt đường tín hiệu, RSI cắt 50) đúng bằng
  "điều kiện đang đúng" (giá đang trên EMA → +1). Với quy tắc phá kênh (Donchian, Bollinger, Keltner…) nghĩa là
  "lần phá kênh gần nhất là lên/xuống". Dùng một định nghĩa chung cho mọi chỉ báo để không phải chọn tay từng cái.

Filter giữ dạng trạng thái đúng/sai như M1 (không có hướng).

## Kiểm tra

- `pytest -q tests/test_lookahead.py`: mọi chỉ báo trên M15, 20 thời điểm ngẫu nhiên, giá trị + sự kiện + trạng thái
  tính trên data[:t+1] khớp tính trên toàn bộ; HTF H1/H4 trên nến M15 (`tests/test_track.py`).
- Số sự kiện mỗi chỉ báo × symbol: `reports/ind15/signal_summary.json`.
