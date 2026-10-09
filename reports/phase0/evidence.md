# Bằng chứng Giai đoạn 0 (đo ngày 2026-10-09 UTC, từ container cloud của Claude Code)

Cửa sổ: 2024-10-09 00:00 UTC → 2026-10-08 23:59 UTC (730 ngày đủ, kết thúc hôm qua).

## 1. REST API
`fapi.binance.com/fapi/v1/ping`, `/fapi/v1/exchangeInfo` → **HTTP 451** "Service unavailable from a restricted location".
Chi tiết: `probe_result.json` → `rest`.

## 2. Klines 1m (Binance Vision, 24 file tháng 2024-10..2026-09 + 8 file ngày 2026-10-01..08), quét toàn bộ
| Symbol | Số nến | Kỳ vọng | Thiếu | Trùng | OHLC sai | SHA256 lỗi | volume = 0 |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 1,051,200 | 1,051,200 | 0 | 0 | 0 | 0 | 126 |
| ETHUSDT | 1,051,200 | 1,051,200 | 0 | 0 | 0 | 0 | 127 |
| BNBUSDT | 1,051,200 | 1,051,200 | 0 | 0 | 0 | 0 | 128 |
| SOLUSDT | 1,051,200 | 1,051,200 | 0 | 0 | 0 | 0 | 128 |
| XRPUSDT | 1,051,200 | 1,051,200 | 0 | 0 | 0 | 0 | 127 |

Tổng zip tải về: 214.9 MB, thời gian 62 s (4 luồng). Chi tiết: `klines_1m_full_scan.json`.

Nến volume = 0 của BTCUSDT (tất cả đều phẳng O=H=L=C), gom thành các đợt liên tiếp:
```
2024-10-28 16:21 → 16:34 (14)   2024-10-28 16:36 (1)   2024-10-28 20:00 → 21:13 (74)
2025-01-14 13:32 → 13:33 (2)    2025-01-29 01:23 → 01:35 (13)   2025-01-29 02:41 → 02:44 (4)
2025-08-29 06:19 → 06:36 (18)
```

## 3. Metrics (OI, long/short ratio, taker ratio — chu kỳ 5 phút), quét 730 file ngày × 5 symbol
Mỗi symbol: 210,235 / 210,240 dòng; thiếu 5 slot (2024-10-28 16:25, 16:30; 2025-08-29 06:20, 06:25, 06:30), 0 trùng, 0 lệch lưới 5 phút.
NaN: `count_toptrader_long_short_ratio` ~54–56, `sum_toptrader_long_short_ratio` 18, `count_long_short_ratio` ~19–21; OI và taker ratio: 0 NaN.
Có xảy ra lỗi mạng tạm thời (SSL EOF) khi tải; chạy lại có retry thì thành công.

## 4. Funding rate (file tháng 2024-10..2026-09)
Mỗi symbol 2,190 bản ghi, `funding_interval_hours` = 8 cho toàn bộ. Không có file funding theo ngày → tháng hiện tại chỉ có sau khi tháng kết thúc.

## 5. Dữ liệu khác
- bookTicker (bid/ask): file tháng cuối cùng là 2024-04 → **không có spread lịch sử trong cửa sổ nghiên cứu**.
- bookDepth (ngày): snapshot ~30 s, độ sâu tích lũy ở ±0.2%, ±1..5% (từ 2023-01-01).
- aggTrades tháng 2026-09: BTC 437 MB zip, SOL 132 MB, XRP 144 MB.
- Mẫu Parquet (zstd) klines BTC 2026-09: 2.59 MB / 43,200 dòng; zip 1.80 MB; CSV 4.86 MB.
