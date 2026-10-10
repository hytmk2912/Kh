# Đặc tả — Lướt sóng M1 bằng tổ hợp chỉ báo

Ngày chốt: 2026-10-10. Nguồn: Google Doc "Tài liệu hướng dẫn" (Prompt 1 + Prompt 2) đã gộp thành Prompt 3, chỉnh theo kết quả Giai đoạn 0.

## 0. Mục tiêu (một câu)

Tìm tổ hợp 2–4 chỉ báo **bắt được nhiều sóng tăng/giảm ≥ 0,5% nhất** trên nến M1, rồi chỉ giữ tổ hợp **còn lãi sau phí** khi lướt sóng, giữ lệnh 1–15 phút, Long và Short.

| Mục | Đã chốt |
|---|---|
| Symbol | BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT (USDⓈ-M perpetual) |
| Cửa sổ | 2024-10-09 00:00 → 2026-10-08 23:59 UTC |
| Khung | M1 tìm điểm vào; M15 + H1 chỉ lọc hướng (dựng bằng resample từ M1) |
| Sóng hợp lệ | biên độ ≥ 0,5% |
| Giữ lệnh | tối đa 15 phút |
| Cách chọn | Bảng A (bắt sóng) lọc ứng viên → Bảng B (lãi sau phí, ngoài mẫu) chọn cuối |
| Chia tập | Train 2024-10-09 → 2025-12-20 · Validation 2025-12-21 → 2026-05-15 · **Test cuối (khoá)** 2026-05-16 → 2026-10-08 · embargo 1 ngày giữa các tập |

## 1. Dữ liệu (việc D)

- Tải klines 1m + funding theo đường dẫn trong `CLAUDE.md`. Funding chỉ có file tháng → 2026-10-01..08 không có funding: ghi [L], phần đó nằm trong test khoá nên báo cáo kết quả có/không funding. Xác minh SHA256 từng zip trước khi ghi manifest.
- `data/manifest.parquet`: key, url, sha256, bytes, trạng thái, thời điểm tải. File đã `verified` thì bỏ qua.
- Chuẩn hoá: Parquet zstd `data/norm/klines_1m/symbol=XXX/part.parquet`, bỏ cột `ignore`, `open_time` → UTC, thêm `is_filler`.
- Resample M15/H1 từ M1 (open = open đầu, high = max, low = min, close = close cuối, volume = tổng). Gắn `available_at` = thời điểm đóng nến khung lớn.
- Tick size: không gọi được exchangeInfo → **suy ra từ dữ liệu** (bước giá nhỏ nhất xuất hiện trong close, làm tròn) và ghi [I] vào `reports/ind/tick_size.json`.
- Báo cáo `reports/ind/data_quality.json` theo từng symbol: số dòng, thiếu, trùng, OHLC sai, âm/không hữu hạn, số filler, số nến M15/H1.

## 2. Nhãn sóng — đáp án để chấm (việc L)

Đáp án được phép nhìn lại quá khứ, vì nó là "sóng đã xảy ra thật". Nó chỉ dùng để chấm, **không bao giờ** làm đầu vào tín hiệu.

**ZigZag 0,5% trên high/low:**

- Đang tìm đỉnh: cập nhật đỉnh khi high mới cao hơn. Khi low ≤ đỉnh × (1 − 0,005) → chốt đỉnh, chuyển sang tìm đáy. Ngược lại tương tự.
- Mỗi điểm xoay lưu `event_time` (nến tạo đỉnh/đáy) và `confirm_time` (nến làm giá đảo 0,5%).
- Bỏ qua nến `is_filler` khi cập nhật đỉnh/đáy.

**Trạng thái:**

| Nhãn | Định nghĩa |
|---|---|
| SÓNG TĂNG | đoạn đáy → đỉnh liền kề, biên độ ≥ 0,5% |
| SÓNG GIẢM | đoạn đỉnh → đáy liền kề, biên độ ≥ 0,5% |
| NHỊP HỒI | nến trong sóng mà giá đi ngược chiều sóng (dùng ZigZag 0,2% bên trong sóng 0,5%); lưu độ sâu % so với sóng chính |
| ĐI NGANG | cửa sổ ≥ 30 phút liên tiếp mà (high max − low min) / close < 0,5% |
| UNKNOWN | nến filler và 30 phút sau filler; đoạn không thuộc nhãn nào |

**Sóng nhanh** = sóng mà giá đi được ≥ 0,5% trong ≤ 15 phút tính từ `event_time` điểm xuất phát. Đây là tập chấm chính. Sóng chậm vẫn lưu, báo cáo riêng.

**Mỗi sóng lưu:** symbol, hướng, start/end `event_time`, start/end `confirm_time`, biên độ %, số phút, tốc độ %/phút, nhịp hồi sâu nhất, cờ nhanh/chậm.

**Báo cáo** `reports/ind/waves_stats.json` + `.md`, từng symbol: số sóng tăng/giảm (nhanh/chậm), số đoạn đi ngang, độ dài trung bình/trung vị, biên độ trung bình, tỉ lệ UNKNOWN. Độ nhạy: chạy lại với 0,4% và 0,7% **chỉ để báo cáo**, không dùng để chọn.

## 3. Chỉ báo và tín hiệu (việc I)

**Registry** (`src/kh/ind/indicators/registry.py`): mỗi chỉ báo 1 phiếu gồm tên, nhóm, công thức, nguồn công thức, tham số mặc định, loại (`directional` hay `filter`), quy tắc Long/Short/Neutral hoặc quy tắc lọc, số nến khởi động, độ trễ, rủi ro repaint, ghi chú tương đương TradingView ("chưa đối chiếu" nếu chưa kiểm).

- Toàn bộ danh sách ở Phụ lục A. Chỉ báo không triển khai được (cần dữ liệu khác, định nghĩa mơ hồ) → vẫn có phiếu, `status = "không triển khai"` + lý do. Không âm thầm thay bằng chỉ báo khác.
- Tham số mặc định theo TradingView khi biết; không chắc thì ghi [A].
- **Directional** (cho hướng): tín hiệu là **sự kiện** tại nến điều kiện vừa chuyển sang đúng (ví dụ giá cắt lên EMA, MACD cắt signal, RSI cắt lên 50, SuperTrend đổi màu). Giá trị: +1 Long, −1 Short, 0.
- **Filter** (không cho hướng — ATR, BB Width, Historical Volatility, Volume, Mass Index…): tín hiệu là **trạng thái** đúng/sai (ví dụ ATR M1 > trung vị 1 ngày trước đó). Không bao giờ suy ra Long/Short từ nhóm này.
- Trường hợp đặc biệt: Zig Zag, Williams Fractal, Pivot, Volume Profile chỉ dùng điểm **đã xác nhận** (sự kiện tại nến xác nhận, có độ trễ). Multi-Timeframe MA dùng nến M15 đã đóng. Spread / Ratio / Correlation cần cặp thứ hai → dùng BTCUSDT làm cặp tham chiếu (với BTC thì dùng ETHUSDT), ghi rõ. 52-Week High/Low → đổi cửa sổ sang 1 ngày và ghi [A], hoặc đánh dấu không triển khai.
- **Test chống nhìn tương lai (bắt buộc cho mọi chỉ báo):** chọn 20 thời điểm t ngẫu nhiên; tính trên `data[:t+1]` và trên toàn bộ dữ liệu → giá trị và tín hiệu tại t phải bằng nhau (sai số float32).

**Bộ lọc khung lớn (HTF)**, chốt trước:

- Với M15 và H1: hướng = Tăng nếu close > EMA50 và EMA50 hiện tại > EMA50 cách 3 nến; Giảm nếu ngược lại cả hai; còn lại Trung tính. Chỉ dùng nến đã đóng.
- Long chỉ được phép khi không khung nào Giảm; Short chỉ được phép khi không khung nào Tăng.
- Mọi chỉ báo và tổ hợp được chấm 2 lần: **có HTF** và **không HTF**.

## 4. Chấm chỉ báo đơn lẻ (việc S)

Chỉ dùng Train + Validation. Tính từng symbol, rồi tổng hợp (trung vị 5 symbol) và độ ổn định (giá trị kém nhất trong 5 symbol).

**Định nghĩa "bắt được sóng":** tín hiệu cùng chiều xuất hiện trong khoảng [start `event_time`, end `event_time`), và phần sóng còn lại tính từ giá vào (open nến kế tiếp) đến đỉnh/đáy kết thúc ≥ 0,3%. Mỗi sóng đếm tối đa 1 lần.

**Bảng A — bắt sóng** (`reports/ind/single_tableA.csv`):

- Recall sóng nhanh tăng, recall sóng nhanh giảm, recall sóng chậm.
- Precision Long, precision Short (tín hiệu rơi vào sóng cùng chiều và còn ≥ 0,3%).
- Tín hiệu sai chia theo nơi rơi: đi ngang / nhịp hồi / ngược sóng.
- Độ trễ: số phút và % sóng đã đi khi có tín hiệu.
- Số tín hiệu lặp trong cùng sóng. Chỉ số cấp nến (macro-F1, balanced accuracy) báo kèm.
- **Precision ngẫu nhiên tham chiếu** = precision của tín hiệu ngẫu nhiên cùng tần suất (trung bình 20 lần chạy). Báo `lift = precision / precision ngẫu nhiên`.

**Backtest baseline** (`src/kh/backtest/`), giống nhau cho mọi chỉ báo:

| Tham số | Giá trị baseline | Kịch bản độ nhạy |
|---|---|---|
| Vào lệnh | open nến kế tiếp | trễ thêm 1 nến |
| Take profit | 0,45% [A] | 0,30% / 0,60% |
| Stop loss | 0,30% [A] | 0,20% / 0,40% |
| Thoát khác | tín hiệu ngược chiều; hết 15 phút → thoát ở close | — |
| TP và SL cùng chạm trong 1 nến | coi như SL chạm trước | — |
| Phí | taker 0,05%/chiều [A] | 0,02% / 0,07% |
| Trượt giá | 1 tick/chiều [A] | 3 tick |
| Funding | tính khi lệnh đi qua mốc funding (00/08/16 UTC) | — |
| Không vào lệnh | nến filler, 30 phút sau filler, đã có lệnh mở cùng symbol | — |

Kết quả `reports/ind/single_tableB.csv`: số lệnh (Long/Short), win rate, gross, phí, trượt giá, funding, net, profit factor, max drawdown, expectancy/lệnh (% net), lãi/lỗ trung bình, thời gian giữ trung bình — theo từng symbol, có/không HTF. **Không suy ra lợi nhuận từ recall/precision.**

## 5. Quét tổ hợp (việc C)

1. **Chọn 20 ứng viên** từ Bảng A + B đơn lẻ (Train): 16 directional + 4 filter.
   - Điểm directional = trung bình thứ hạng của: recall sóng nhanh, lift, tỉ lệ sai trong đi ngang/nhịp hồi (thấp tốt), độ trễ (thấp tốt), độ ổn định 5 symbol. Trọng số bằng nhau.
   - Điểm filter = lift khi lọc: (tỉ lệ nến thuộc sóng nhanh khi filter bật) / (tỉ lệ chung).
   - Hai directional có tương quan tín hiệu > 0,8 → giữ cái điểm cao hơn.
2. **Quy tắc đồng thuận:** mỗi sự kiện directional còn hiệu lực 2 nến (nến phát + 2 nến sau). Tổ hợp phát Long/Short tại nến t nếu tất cả directional trong tổ hợp có sự kiện cùng chiều còn hiệu lực ở t, ít nhất một sự kiện mới phát ở t, không directional nào có sự kiện ngược chiều còn hiệu lực, và mọi filter đang bật. Tổ hợp phải có ≥ 1 directional.
3. **Quét** mọi tổ hợp 2, 3, 4 phần tử từ 20 ứng viên (≤ 6.175 tổ hợp) × có/không HTF. Ghi số lần thử thật vào `trials.csv`.
4. **Bảng A tổ hợp:** điều kiện precision ≥ 1,5 × precision ngẫu nhiên (cả Long và Short, trung vị 5 symbol). Trong các tổ hợp đạt, xếp theo **recall sóng nhanh (tăng + giảm)**, hoà thì theo precision. Giữ top 50. (Điều kiện precision chặn lời giải vô nghĩa "bắn tín hiệu liên tục để bắt hết sóng".)
5. **Bảng B tổ hợp:** backtest top 50 trên walk-forward. Loại tổ hợp có expectancy net ≤ 0 ở kịch bản phí baseline. Xếp theo expectancy net → profit factor → max drawdown → độ ổn định 5 symbol.
6. **Top 10** = 10 dòng đầu Bảng B. Giải thích ngắn vì sao các chỉ báo bổ trợ nhau (xu hướng / động lượng / khối lượng / biến động).

Báo cả hai bảng; tổ hợp bắt sóng tốt nhất có thể không phải tổ hợp lãi nhất.

## 6. Walk-forward và chống overfitting (việc W)

- Walk-forward trong Train + Validation: cửa sổ train mở rộng, tối thiểu 6 tháng, kiểm tra 1 tháng kế tiếp, trượt 1 tháng; purge + embargo 1 ngày ở mỗi ranh giới.
- Chọn 20 ứng viên và Bảng A chỉ trên phần train của mỗi fold; Bảng B tính trên phần kiểm tra của fold. Gộp kết quả ngoài mẫu các fold.
- Tinh chỉnh tham số chỉ cho chỉ báo trong top 10, chỉ trong train của fold. Bảng độ nhạy ±20% tham số: kết quả đổi dấu → loại.
- Multiple testing: Deflated Sharpe Ratio dùng tổng số lần thử, PBO (CSCV, 16 khối), block bootstrap (khối 1 ngày, 1.000 lần) cho khoảng tin cậy 95% của expectancy.
- Leave-one-coin-out cho tổ hợp top 10: chọn trên 4 coin, kiểm tra coin thứ 5.
- Báo cáo riêng: train, walk-forward gộp, theo symbol, theo 3 chế độ biến động (tam phân vị ATR M1 tính từ train).

## 7. Chiến lược cuối và test khoá (việc F)

- Chọn **1 chiến lược** theo thứ tự Bảng B walk-forward, ghi vào `CHANGELOG.md` kèm hash commit **trước** khi mở test cuối.
- `docs/ind/strategy.md`: điều kiện Long/Short, HTF, TP/SL, thoát thời gian, bộ lọc không giao dịch (mỗi bộ lọc phải có số chứng minh có ích ngoài mẫu), quản lý vốn.
- Quản lý vốn (giả định nghiên cứu): rủi ro 0,25–0,5% equity/lệnh; khối lượng = equity × % rủi ro ÷ (khoảng SL + phí + trượt giá); tách notional, ký quỹ, mức lỗ khi chạm SL; không dùng đòn bẩy cao để làm đẹp kết quả.
- Chạy test cuối **một lần**, lưu `reports/ind/final_test.json` + SHA256 của file kết quả.
- Không có chiến lược nào lãi sau phí → báo đúng như vậy, đó là kết quả hợp lệ.

## 8. Bàn giao

| File | Nội dung |
|---|---|
| `reports/ind/data_quality.json` | nguồn, URL mẫu, số dòng, thiếu, trùng, filler, trạng thái SHA256 |
| `reports/ind/waves_stats.{json,md}` | thống kê sóng + độ nhạy 0,4/0,5/0,7% |
| `docs/ind/indicator_cards.md` | phiếu mọi chỉ báo, kể cả chỉ báo không triển khai |
| `reports/ind/single_tableA.csv`, `single_tableB.csv` | chấm đơn lẻ, từng symbol, có/không HTF |
| `reports/ind/combos_tableA.csv`, `combos_tableB.csv`, `top10.md` | tổ hợp, số lần thử, ngoài mẫu, DSR, PBO, CI |
| `docs/ind/strategy.md`, `reports/ind/final_test.json` | chiến lược chọn + test cuối |
| `docs/ind/conclusion.md` | tách rõ: đã chạy trên dữ liệu thật / suy luận / chưa kiểm chứng; giới hạn OHLCV, không có spread, thứ tự chạm TP/SL, multiple testing; không hứa lợi nhuận |

## Phụ lục A — Danh sách chỉ báo bắt buộc

Gợi ý loại: (D) directional, (F) filter. Claude Code được đổi loại nếu có lý do, ghi vào phiếu.

- **A1. MA:** SMA, EMA, DEMA, TEMA, Hull MA, Hamming MA, Arnaud Legoux MA, Least Squares MA, Smoothed MA, Adaptive MA, Multi-Timeframe MA, WMA, McGinley Dynamic, Guppy MMA, MA Cross, EMA Cross, MA-EMA Cross — (D)
- **A2. Xu hướng:** SuperTrend, Ichimoku Cloud, Parabolic SAR, Directional Movement, Vortex, Williams Alligator, Williams Fractal, Aroon, Trend Strength Index, Zig Zag, Linear Regression Curve, Linear Regression Slope, Keltner Channels, Donchian Channels, Price Channel, MA Channel, Chande Kroll Stop, 52-Week High/Low, Majority Rule — (D); ADX — (F)
- **A3. Dao động:** MACD, RSI, Stochastic, Stochastic RSI, Connors RSI, Awesome Oscillator, Accelerator Oscillator, Momentum, Chande Momentum Oscillator, Price Oscillator, Detrended Price Oscillator, TRIX, Fisher Transform, Ultimate Oscillator, Williams %R, SMI Ergodic, Relative Vigor Index, True Strength Index, Coppock Curve, Rate of Change, Klinger Oscillator — (D)
- **A4. Biến động:** Bollinger Bands, BB %B, Standard Error Bands, Envelopes — (D, breakout); BB Width, ATR, Historical Volatility, Chaikin Volatility, Close-to-Close Volatility, Non-Directional Close-to-Close Volatility, O-H-L-C Volatility, Relative Volatility Index, Standard Deviation, Volatility Region, Mass Index — (F)
- **A5. Khối lượng:** Net Volume, OBV, Accumulation/Distribution, MFI, Chaikin Money Flow, Chaikin Oscillator, Ease of Movement, Elder Force Index, Price & Volume Trend — (D); Volume, Volume Oscillator, Volume Profile Fixed Range — (F)
- **A6. Khác:** VWAP (reset 00:00 UTC), VWMA, Pivot Points Standard (ngày trước), Balance of Power, Accumulative Swing Index, Up/Down — (D); Spread, Correlation Coefficient, Correlation-Log, Rank Correlation, Ratio, Standard Error — (F); Sure Thing, Average Price, Typical Price, Median Price — (D nếu dùng như giá so với MA của chính nó, ghi rõ)
