# Báo cáo Giai đoạn 0 — Khảo sát, kiểm tra khả thi và thiết kế

Ngày lập: 2026-10-09 (UTC). Trạng thái: **chờ phê duyệt** (chưa sang Giai đoạn 1).
Bằng chứng gốc: `reports/phase0/evidence.md`, `reports/phase0/*.json`. Script kiểm tra: `tools/phase0_probe.py`.

Ký hiệu: **[F]** Fact đã đo/xác minh · **[A]** Assumption · **[H]** Hypothesis · **[I]** Inference · **[L]** Limitation.

---

## A. Tóm tắt yêu cầu

- Mục tiêu: nghiên cứu (không giao dịch thật) quy luật giá trên Binance USDⓈ-M perpetual, nến 1 phút, 730 ngày; đi từ mô tả sóng → đặc trưng → kiểm định dự báo ngoài mẫu → chiến lược → backtest có chi phí → xếp hạng theo mức bằng chứng.
- Symbol: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Môi trường: Python, Google Colab, Parquet, GitHub (mã + tài liệu), UTC.
- Giới hạn: chỉ dữ liệu công khai, không API key có quyền giao dịch, không tự đổi symbol/phạm vi, không coi giả thuyết là kết luận, final test được khóa.

## B. Kiểm tra tính khả thi

### B1. Đã xác minh (đo trực tiếp ngày 2026-10-09)

| # | Nội dung | Kết quả |
|---|---|---|
| 1 | REST `fapi.binance.com` từ container cloud | **[F] HTTP 451** "restricted location" |
| 2 | Binance Vision (`data.binance.vision`) | **[F]** truy cập được, không cần key |
| 3 | Klines 1m, 5 symbol, 2024-10-09 → 2026-10-08 | **[F]** mỗi symbol 1.051.200/1.051.200 nến, 0 thiếu, 0 trùng, 0 sai thứ tự, 0 lỗi OHLC, 0 lỗi SHA256 |
| 4 | Nến volume = 0, O=H=L=C | **[F]** 126–128 nến/symbol, gom thành đợt (vd. 2024-10-28 20:00–21:13, 74 phút) |
| 5 | Cột klines | **[F]** open_time, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore; timestamp ms; close_time − open_time = 59.999 ms |
| 6 | Metrics 5 phút (OI, long/short ratio, taker ratio) | **[F]** 210.235/210.240 dòng mỗi symbol, thiếu 5 slot trùng các đợt nến volume 0 |
| 7 | Funding | **[F]** 2.190 bản ghi/symbol (đủ 3 lần/ngày), chu kỳ 8h toàn bộ; chỉ có file theo tháng (tháng 10/2026 chưa có) |
| 8 | Spread (bookTicker) | **[F]** file cuối là 2024-04 → **không có spread trong cửa sổ nghiên cứu** |
| 9 | bookDepth | **[F]** có theo ngày, snapshot ~30 s, độ sâu tích lũy ±0,2%, ±1…5% |
| 10 | aggTrades | **[F]** có; BTC 2026-09 = 437 MB zip (nặng) |
| 11 | Tải toàn bộ klines 5 symbol | **[F]** 214,9 MB zip, 62 giây (4 luồng) trong container này; có 1 lỗi SSL tạm thời → cần retry |

### B2. Chưa xác minh được

- **[A]** Colab có bị 451 không: Colab thường chạy trên IP Google tại Mỹ nên khả năng cao bị chặn tương tự. Cần anh/chị chạy lệnh ở mục J.
- **[A]** Giới hạn REST (limit tối đa 1500 nến/lần, weight 2400/phút/IP, `openInterestHist` chỉ ~30 ngày gần nhất): theo hiểu biết trước đây, **chưa xác minh** vì trang tài liệu chính thức chặn truy cập tự động từ container. Không ảnh hưởng nếu dùng Binance Vision.
- **[A]** Ý nghĩa chính xác các cột metrics (vd. `count_toptrader_long_short_ratio` = tỷ lệ theo tài khoản top trader, `sum_toptrader...` = theo vị thế, `sum_taker_long_short_vol_ratio` = taker buy/sell) và **độ trễ công bố** của giá trị gắn `create_time`.
- **[A]** Biểu phí của tài khoản anh/chị (giả định VIP0: taker 0,05%, maker 0,02%) — chưa xác minh.
- **[I]** Nến volume 0 là nến "lấp chỗ" trong thời gian sàn bảo trì/sự cố (cùng thời điểm ở cả 5 symbol, trùng với metrics bị thiếu). Chưa có xác nhận chính thức.
- **[I]** Cả 5 hợp đồng đang giao dịch (dữ liệu có đến 2026-10-08) — chưa xác minh qua exchangeInfo vì bị 451.

### B3. Kết luận khả thi

- **Khả thi** với OHLCV 1m + taker buy volume 1m, funding 8h, OI/long-short/taker ratio 5 phút cho đủ 730 ngày, cả 5 symbol, không cần API key.
- **Không khả thi**: spread bid/ask lịch sử trong cửa sổ → slippage phải mô hình hóa (dùng bookDepth làm căn cứ).
- **Khả thi nhưng tốn kém**: aggTrades toàn bộ (ước tính hàng chục GB) → chỉ dùng chọn lọc.

## C. Kiến trúc đề xuất

```
kh/
├── configs/            # YAML: symbols, cửa sổ thời gian, chia tập, phí, tham số sóng
├── src/kh/
│   ├── data/           # tải Binance Vision, manifest/checksum, chuẩn hóa, kiểm tra chất lượng
│   ├── features/       # đặc trưng + "registry" (công thức, cửa sổ, thời điểm khả dụng)
│   ├── waves/          # ZigZag / Directional Change, nhãn hồi cứu + thời điểm xác nhận
│   ├── labels/         # nhãn dự báo (forward return, triple-barrier)
│   ├── patterns/       # kiểm định đơn biến/tổ hợp, bootstrap, FDR
│   ├── models/         # baseline, logistic, GBM
│   ├── backtest/       # mô phỏng lệnh, phí, slippage, funding
│   ├── evaluation/     # walk-forward, purge/embargo, DSR, PBO, độ nhạy
│   └── tracking/       # experiment registry (ID, git hash, config hash, kết quả)
├── notebooks/          # notebook Colab mỏng, chỉ gọi src/
├── tests/              # pytest, gồm test chống look-ahead
├── tools/              # script tiện ích (phase0_probe.py)
├── reports/            # báo cáo nhỏ (md/json/png); số liệu lớn để trên Drive
├── docs/               # báo cáo giai đoạn, định nghĩa, pre-registration giả thuyết
├── requirements.txt    # khóa phiên bản
└── data/               # .gitignore — dữ liệu thật nằm trên Google Drive
```

Lý do khác bản tham khảo: thêm `labels/` (tách nhãn khỏi đặc trưng để dễ kiểm tra rò rỉ), `tracking/` (đếm số giả thuyết đã thử), gói `src/kh` để `pip install -e .` trên Colab. Không dùng database/MLflow ở giai đoạn đầu; registry là file Parquet/CSV để tối giản.

## D. Kế hoạch dữ liệu

1. **Nguồn**: Binance Vision (file tháng cho tháng đã đủ, file ngày cho phần tháng hiện tại). REST chỉ là tùy chọn đối chiếu nếu truy cập được từ máy anh/chị.
2. **Raw**: lưu nguyên file zip + file `.CHECKSUM`, xác minh SHA256 trước khi ghi nhận.
3. **Manifest (checkpoint)**: một bảng gồm key, sha256, kích thước, trạng thái, thời điểm tải. Tiếp tục tải = bỏ qua file đã "verified". Chạy lại không ghi đè file đã hợp lệ.
4. **Retry**: exponential backoff (2, 4, 8, 16 s), tối đa 5 lần; đã gặp lỗi SSL tạm thời thực tế.
5. **Normalized**: Parquet zstd, phân vùng `symbol=/year=/month=`, kiểu dữ liệu cố định (timestamp UTC, float64 giá, float64 volume), bỏ cột `ignore`.
6. **Cờ chất lượng**: `is_filler` = volume 0 và O=H=L=C. **Giữ nguyên, không nội suy, không xóa**; đặc trưng/tín hiệu trong và ngay sau đợt filler được đánh dấu không hợp lệ.
7. **Kiểm tra**: OHLC logic, giá/volume không âm, trùng/thiếu/sai thứ tự, đếm nến theo ngày, **đối chiếu chéo file tháng với file ngày** của cùng khoảng (hai sản phẩm độc lập) thay cho REST.
8. **Lưu trữ & sao lưu**: Google Drive `MyDrive/kh_data/` là nơi bền vững; `/content` trên Colab chỉ là bộ nhớ tạm. Mỗi file ghi xong mới cập nhật manifest. Phiên bản dữ liệu = hash của manifest, ghi vào mọi thí nghiệm.
9. **Đóng băng cửa sổ**: 2024-10-09 00:00 → 2026-10-08 23:59 UTC. Dữ liệu sau ngày này để dành làm forward holdout (xem G).

## E. Phương pháp nghiên cứu sóng giá

### E1. So sánh phương pháp

| Phương pháp | Tham số | Ưu | Nhược | Online được? |
|---|---|---|---|---|
| ZigZag % cố định | θ (%) | Đơn giản, dễ hiểu | Không so sánh được giữa coin/giai đoạn có độ biến động khác nhau | Đỉnh/đáy: **không**; điểm xác nhận: có |
| ZigZag theo ATR/σ | k, cửa sổ σ | Chuẩn hóa theo biến động, so sánh được giữa coin | Thêm tham số; σ phải tính bằng quá khứ | Như trên |
| Directional Change (DC) | θ | Định nghĩa sự kiện rõ ràng: "giá đảo chiều θ từ cực trị" → thời điểm xác nhận chính xác | Giống ZigZag về bản chất | **Có** (sự kiện DC là online) |
| Change-point (PELT, BOCPD) | penalty / hazard | Tìm thay đổi chế độ thống kê | Chậm trên 1 triệu nến; PELT là offline | BOCPD: có, nhưng tốn tính toán |
| HMM chế độ | số trạng thái | Phân loại trend/range/biến động | Nhãn phụ thuộc toàn chuỗi khi fit (smoothing) | Chỉ filtering mới online |

**Đề xuất**: phương pháp chính là **DC/ZigZag theo σ, đa thang đo** (vd. θ = k·σ với k ∈ {2, 4, 8}), thêm ZigZag % cố định làm đối chứng. Change-point/HMM chỉ thêm khi có lý do rõ ràng.

### E2. Định nghĩa định lượng (đề xuất ban đầu)

- Sóng tăng/giảm: đoạn giữa hai cực trị liên tiếp ở thang θ.
- Nhịp điều chỉnh/hồi: sóng ngược chiều ở thang nhỏ nằm trong sóng thang lớn.
- Đi ngang: khoảng thời gian thang lớn không có sự kiện DC trong ≥ N phút và biên độ/σ thấp.
- Breakout/breakdown: giá đóng cửa vượt đỉnh/đáy N nến **trước đó** (không gồm nến hiện tại).
- Chuyển đổi trạng thái: thay đổi nhãn regime tính bằng cửa sổ quá khứ.

### E3. Nhãn hồi cứu và tín hiệu online

Mỗi sóng lưu: `extreme_time` (đỉnh/đáy, **hồi cứu**), `confirmation_time` (lúc giá đã đảo chiều θ — sớm nhất có thể biết), `signal_time` = đóng cửa nến xác nhận, `entry_time` = mở cửa nến kế tiếp (+ tùy chọn độ trễ). Chỉ `confirmation_time` trở đi mới được dùng cho tín hiệu.

### E4. Chống look-ahead

- **Test cắt cụt**: với t ngẫu nhiên, tính đặc trưng trên `data[:t]` và trên toàn bộ dữ liệu → giá trị tại t phải giống nhau. Test này tự động, bắt buộc với mọi đặc trưng.
- Metrics/funding gắn thời điểm khả dụng thận trọng (metrics tại T chỉ dùng từ T+5 phút; funding chỉ biết sau `calc_time`).
- Báo cáo độ nhạy: mọi thống kê sóng được tính trên lưới tham số, không chỉ một θ.

## F. Phương pháp khai phá quy luật

1. **Bài toán A (mô tả)**: phân phối biên độ, thời lượng, tốc độ, độ sâu hồi, xác suất chuyển tiếp theo coin/regime. Chỉ mô tả, không kết luận dự báo.
2. **Pre-registration**: trước khi kiểm định, ghi file `docs/hypotheses.md` (commit có thời gian) với giả thuyết, nhãn, ngưỡng, tiêu chí đạt. Giả thuyết phát sinh sau khi xem dữ liệu được gắn nhãn "exploratory".
3. **Bài toán B (dự báo)**: lấy mẫu theo sự kiện (tại thời điểm xác nhận DC, breakout…) thay vì mọi phút → giảm chồng lấn. Nhãn: forward return h phút và triple-barrier (TP/SL theo σ, thời gian tối đa).
4. **Trình tự**: đơn biến (chia decile → xác suất có điều kiện so với base rate, Spearman IC) → hai biến → nhiều biến/mô hình → baseline → ngoài mẫu → theo coin/regime.
5. **Bất định**: block bootstrap theo thời gian cho khoảng tin cậy; số quan sát hiệu dụng tính theo cụm sự kiện không chồng lấn và gộp theo thời gian giữa các coin (5 coin không độc lập).
6. **Bài toán C (chiến lược)**: chỉ quy luật vượt tiêu chí ngoài mẫu mới được chuyển sang backtest; báo cáo expectancy, không chỉ win rate.

## G. Kiểm định và chống overfitting

- **Chia tập theo thời gian (60/20/20)**:
  - Train: 2024-10-09 → 2025-12-20 (438 ngày)
  - Validation: 2025-12-21 → 2026-05-15 (146 ngày)
  - Final test: 2026-05-16 → 2026-10-08 (146 ngày) — **khóa**
  - Embargo giữa các tập ≥ horizon nhãn dài nhất (đề xuất 1 ngày).
- **Walk-forward** trong train+validation: cửa sổ mở rộng, huấn luyện ≥ 6 tháng, kiểm tra 1 tháng, purge + embargo.
- **Final test**: chạy một lần sau khi khóa thiết kế; lưu hash kết quả. Nếu sửa sau khi xem → final test mất tính độc lập, phải ghi rõ.
- **Forward holdout miễn phí**: dữ liệu sau 2026-10-08 tự tích lũy; kiểm tra lại sau ≥ 3 tháng mà không chỉnh sửa.
- **Multiple testing**: registry đếm mọi thí nghiệm; FDR Benjamini–Yekutieli (chịu được phụ thuộc) trong từng nhóm giả thuyết; với chiến lược: Deflated Sharpe Ratio, PBO (CSCV), hoặc White Reality Check/Hansen SPA bằng block bootstrap.
- **Tổng quát hóa**: leave-one-coin-out (phát triển trên 4 coin, kiểm tra coin thứ 5).
- **Độ bền**: phí ×2, slippage ×3, trễ 1–2 nến, lân cận tham số, bỏ 5% giao dịch lãi lớn nhất, theo regime, theo coin.

## H. Tài nguyên và chi phí

| Hạng mục | Giá trị | Loại |
|---|---|---|
| Zip klines 1m, 5 symbol, 730 ngày | 214,9 MB | **Đo** |
| Thời gian tải klines | 62 s (container cloud) | **Đo** (Colab có thể khác) |
| Parquet normalized | ~310 MB (2,59 MB/tháng BTC × 120) | Ước tính |
| Metrics 5 phút | ~40 MB zip (11,5 KB/ngày × 3.650) | Ước tính |
| Funding | < 1 MB | Ước tính |
| Bảng đặc trưng (~150 cột float32 × 5,26 triệu dòng) | ~3 GB RAM, ~1–2 GB đĩa | Ước tính |
| aggTrades đầy đủ | hàng chục GB | Ước tính → không tải mặc định |
| Tổng dung lượng Drive giai đoạn đầu | ~2–5 GB | Ước tính |

- Colab miễn phí đủ cho tải dữ liệu, sóng, đặc trưng (xử lý theo từng symbol), logistic/LightGBM trên CPU.
- Có thể cần Colab Pro (trả phí) nếu phiên bị ngắt khi chạy walk-forward dài hoặc thiếu RAM — chỉ đề xuất khi đo được nhu cầu.
- Chi phí dự kiến: **0** (Colab free, Drive 15 GB free, GitHub free).

## I. Rủi ro và giới hạn

1. **Nến filler** khi sàn bảo trì: nếu không gắn cờ, chúng tạo ra giai đoạn "biến động thấp" giả và tín hiệu sai.
2. **Look-ahead** từ đỉnh/đáy ZigZag, metrics, funding.
3. **Thứ tự trong nến**: 1m OHLC không cho biết TP hay SL chạm trước → mặc định SL trước (thận trọng); aggTrades để kiểm tra mẫu.
4. **Không có spread lịch sử** → slippage là giả định.
5. **Last price vs mark price**: thanh lý dùng mark price → cần markPriceKlines nếu mô phỏng thanh lý.
6. **Mẫu nhỏ và tương quan cao**: 2 năm, 5 coin cùng chiều; final test 146 ngày có thể chỉ chứa 1 regime.
7. **Data snooping** do thử nhiều giả thuyết.
8. **Thiên lệch lựa chọn**: 5 coin vốn hóa lớn, còn tồn tại hôm nay → kết luận không suy rộng cho altcoin nhỏ.
9. **Phi dừng**: hành vi thị trường, phí, cấu trúc funding có thể thay đổi.
10. **Colab mất phiên**: phải ghi Drive liên tục, khóa phiên bản thư viện.
11. **Dữ liệu nguồn có thể bị sửa** → lưu checksum/manifest, đánh phiên bản.
12. **Pháp lý/điều khoản**: HTTP 451 cho thấy Binance hạn chế theo khu vực; dự án chỉ dùng dữ liệu công khai cho nghiên cứu.

## J. Quyết định cần xác nhận

Xem phần J trong phản hồi chat (danh sách câu hỏi + mặc định).

## Tiêu chí nghiệm thu Giai đoạn 0

- [x] Nguồn dữ liệu xác định và truy cập được (Binance Vision) — có bằng chứng.
- [x] Phạm vi 730 ngày × 5 symbol được xác nhận cho klines, metrics, funding — có bằng chứng.
- [x] Các bất thường dữ liệu đầu tiên được phát hiện (nến filler, metrics thiếu 5 slot, không có spread).
- [ ] Anh/chị chạy `tools/phase0_probe.py` trên Colab, kết quả khớp (đặc biệt mã HTTP REST).
- [ ] Các quyết định ở mục J được phê duyệt.
