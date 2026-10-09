# Phiếu chỉ báo (sinh tự động từ `src/kh/ind/indicators/registry.py`)

Tổng số: **101** chỉ báo = số tên ở Phụ lục A của `docs/ind/spec.md`.
Quy ước: (D) directional → sự kiện +1/−1 tại nến điều kiện vừa đúng; (F) filter → trạng thái bật/tắt, không cho hướng.
Quy tắc filter mặc định: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A].

| # | Chỉ báo | Nhóm | Loại | Trạng thái | Tham số | Quy tắc |
|---|---|---|---|---|---|---|
| 1 | SMA | A1 MA | D | chưa triển khai | `{'length': 9}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 2 | EMA | A1 MA | D | chưa triển khai | `{'length': 9}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 3 | DEMA | A1 MA | D | chưa triển khai | `{'length': 9}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 4 | TEMA | A1 MA | D | chưa triển khai | `{'length': 9}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 5 | Hull MA | A1 MA | D | chưa triển khai | `{'length': 9}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 6 | Hamming MA | A1 MA | D | chưa triển khai | `{'length': 10}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 7 | Arnaud Legoux MA | A1 MA | D | chưa triển khai | `{'length': 9, 'offset': 0.85, 'sigma': 6}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 8 | Least Squares MA | A1 MA | D | chưa triển khai | `{'length': 25}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 9 | Smoothed MA | A1 MA | D | chưa triển khai | `{'length': 7}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 10 | Adaptive MA | A1 MA | D | chưa triển khai | `{'length': 9, 'fast': 2, 'slow': 30}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 11 | Multi-Timeframe MA | A1 MA | D | chưa triển khai | `{'length': 20, 'tf': '15m'}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 12 | WMA | A1 MA | D | chưa triển khai | `{'length': 9}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 13 | McGinley Dynamic | A1 MA | D | chưa triển khai | `{'length': 14}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 14 | Guppy MMA | A1 MA | D | chưa triển khai | `{'short': [3, 5, 8, 10, 12, 15], 'long': [30, 35, 40, 45, 50, 60]}` | min(EMA ngắn) vừa vượt lên trên max(EMA dài) → +1; max(EMA ngắn) vừa xuống dưới min(EMA dài) → −1 |
| 15 | MA Cross | A1 MA | D | chưa triển khai | `{'fast': 9, 'slow': 21}` | SMA nhanh cắt lên SMA chậm → +1; cắt xuống → −1 |
| 16 | EMA Cross | A1 MA | D | chưa triển khai | `{'fast': 9, 'slow': 21}` | EMA nhanh cắt lên EMA chậm → +1; cắt xuống → −1 |
| 17 | MA-EMA Cross | A1 MA | D | chưa triển khai | `{'sma': 10, 'ema': 10}` | EMA cắt lên SMA → +1; cắt xuống → −1 |
| 18 | SuperTrend | A2 Xu hướng | D | chưa triển khai | `{'atr': 10, 'factor': 3.0}` | đổi sang xu hướng tăng → +1; đổi sang giảm → −1 |
| 19 | Ichimoku Cloud | A2 Xu hướng | D | chưa triển khai | `{'tenkan': 9, 'kijun': 26, 'senkou_b': 52, 'displacement': 26}` | close cắt lên đỉnh mây → +1; cắt xuống đáy mây → −1 |
| 20 | Parabolic SAR | A2 Xu hướng | D | chưa triển khai | `{'start': 0.02, 'inc': 0.02, 'max': 0.2}` | SAR đổi xuống dưới giá → +1; lên trên giá → −1 |
| 21 | Directional Movement | A2 Xu hướng | D | chưa triển khai | `{'length': 14}` | +DI cắt lên −DI → +1; cắt xuống → −1 |
| 22 | Vortex | A2 Xu hướng | D | chưa triển khai | `{'length': 14}` | VI+ cắt lên VI− → +1; cắt xuống → −1 |
| 23 | Williams Alligator | A2 Xu hướng | D | chưa triển khai | `{'jaw': [13, 8], 'teeth': [8, 5], 'lips': [5, 3]}` | môi > răng > hàm vừa thành đúng → +1; môi < răng < hàm vừa thành đúng → −1 |
| 24 | Williams Fractal | A2 Xu hướng | D | chưa triển khai | `{'periods': 2}` | close phá lên trên đỉnh fractal ĐÃ XÁC NHẬN gần nhất → +1; phá xuống đáy fractal gần nhất → −1 |
| 25 | Aroon | A2 Xu hướng | D | chưa triển khai | `{'length': 14}` | Aroon Up cắt lên Aroon Down → +1; cắt xuống → −1 |
| 26 | Trend Strength Index | A2 Xu hướng | D | chưa triển khai | `{'length': 14}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 27 | Zig Zag | A2 Xu hướng | D | chưa triển khai | `{'deviation': 0.005}` | đáy được xác nhận → +1; đỉnh được xác nhận → −1 |
| 28 | Linear Regression Curve | A2 Xu hướng | D | chưa triển khai | `{'length': 9}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 29 | Linear Regression Slope | A2 Xu hướng | D | chưa triển khai | `{'length': 14}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 30 | Keltner Channels | A2 Xu hướng | D | chưa triển khai | `{'length': 20, 'mult': 2.0, 'atr': 10}` | close cắt lên dải trên → +1; cắt xuống dải dưới → −1 |
| 31 | Donchian Channels | A2 Xu hướng | D | chưa triển khai | `{'length': 20}` | close vượt max high 20 nến trước → +1; thủng min low → −1 |
| 32 | Price Channel | A2 Xu hướng | D | chưa triển khai | `{'length': 20}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 33 | MA Channel | A2 Xu hướng | D | chưa triển khai | `{'length': 20}` | close cắt lên SMA(high) → +1; cắt xuống SMA(low) → −1 |
| 34 | Chande Kroll Stop | A2 Xu hướng | D | chưa triển khai | `{'p': 10, 'x': 1.0, 'q': 9}` | close cắt lên stop short → +1; cắt xuống stop long → −1 |
| 35 | 52-Week High/Low | A2 Xu hướng | D | chưa triển khai | `{'length': 1440}` | close vượt đỉnh 1 ngày → +1; thủng đáy 1 ngày → −1 |
| 36 | Majority Rule | A2 Xu hướng | D | chưa triển khai | `{'length': 14}` | tỷ lệ cắt lên 50% → +1; cắt xuống 50% → −1 |
| 37 | ADX | A2 Xu hướng | F | chưa triển khai | `{'length': 14}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 38 | MACD | A3 Dao động | D | chưa triển khai | `{'fast': 12, 'slow': 26, 'signal': 9}` | đường chính cắt lên đường tín hiệu → +1; cắt xuống → −1 |
| 39 | RSI | A3 Dao động | D | chưa triển khai | `{'length': 14}` | RSI cắt lên 50 → +1; cắt xuống 50 → −1 |
| 40 | Stochastic | A3 Dao động | D | chưa triển khai | `{'k': 14, 'smooth_k': 1, 'd': 3}` | %K cắt lên %D → +1; cắt xuống → −1 |
| 41 | Stochastic RSI | A3 Dao động | D | chưa triển khai | `{'rsi': 14, 'stoch': 14, 'k': 3, 'd': 3}` | K cắt lên D → +1; cắt xuống → −1 |
| 42 | Connors RSI | A3 Dao động | D | chưa triển khai | `{'rsi': 3, 'streak': 2, 'rank': 100}` | CRSI cắt lên 50 → +1; cắt xuống → −1 |
| 43 | Awesome Oscillator | A3 Dao động | D | chưa triển khai | `{'fast': 5, 'slow': 34}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 44 | Accelerator Oscillator | A3 Dao động | D | chưa triển khai | `{'fast': 5, 'slow': 34, 'smooth': 5}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 45 | Momentum | A3 Dao động | D | chưa triển khai | `{'length': 10}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 46 | Chande Momentum Oscillator | A3 Dao động | D | chưa triển khai | `{'length': 9}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 47 | Price Oscillator | A3 Dao động | D | chưa triển khai | `{'fast': 10, 'slow': 21}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 48 | Detrended Price Oscillator | A3 Dao động | D | chưa triển khai | `{'length': 21}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 49 | TRIX | A3 Dao động | D | chưa triển khai | `{'length': 18}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 50 | Fisher Transform | A3 Dao động | D | chưa triển khai | `{'length': 9}` | Fisher cắt lên trigger → +1; cắt xuống → −1 |
| 51 | Ultimate Oscillator | A3 Dao động | D | chưa triển khai | `{'fast': 7, 'mid': 14, 'slow': 28}` | UO cắt lên 50 → +1; cắt xuống → −1 |
| 52 | Williams %R | A3 Dao động | D | chưa triển khai | `{'length': 14}` | %R cắt lên −50 → +1; cắt xuống → −1 |
| 53 | SMI Ergodic | A3 Dao động | D | chưa triển khai | `{'short': 5, 'long': 20, 'signal': 5}` | đường chính cắt lên đường tín hiệu → +1; cắt xuống → −1 |
| 54 | Relative Vigor Index | A3 Dao động | D | chưa triển khai | `{'length': 10}` | đường chính cắt lên đường tín hiệu → +1; cắt xuống → −1 |
| 55 | True Strength Index | A3 Dao động | D | chưa triển khai | `{'long': 25, 'short': 13, 'signal': 13}` | đường chính cắt lên đường tín hiệu → +1; cắt xuống → −1 |
| 56 | Coppock Curve | A3 Dao động | D | chưa triển khai | `{'wma': 10, 'long': 14, 'short': 11}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 57 | Rate of Change | A3 Dao động | D | chưa triển khai | `{'length': 9}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 58 | Klinger Oscillator | A3 Dao động | D | chưa triển khai | `{'fast': 34, 'slow': 55, 'signal': 13}` | đường chính cắt lên đường tín hiệu → +1; cắt xuống → −1 |
| 59 | Bollinger Bands | A4 Biến động | D | chưa triển khai | `{'length': 20, 'mult': 2.0}` | close cắt lên dải trên → +1; cắt xuống dải dưới → −1 (breakout) |
| 60 | BB %B | A4 Biến động | D | chưa triển khai | `{'length': 20, 'mult': 2.0}` | %B cắt lên 0,5 → +1; cắt xuống → −1 |
| 61 | Standard Error Bands | A4 Biến động | D | chưa triển khai | `{'length': 21, 'mult': 2.0, 'smooth': 3}` | close cắt lên dải trên → +1; cắt xuống dải dưới → −1 |
| 62 | Envelopes | A4 Biến động | D | chưa triển khai | `{'length': 20, 'percent': 10.0}` | close cắt lên dải trên → +1; cắt xuống dải dưới → −1 |
| 63 | BB Width | A4 Biến động | F | chưa triển khai | `{'length': 20, 'mult': 2.0}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 64 | ATR | A4 Biến động | F | chưa triển khai | `{'length': 14}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 65 | Historical Volatility | A4 Biến động | F | chưa triển khai | `{'length': 10}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 66 | Chaikin Volatility | A4 Biến động | F | chưa triển khai | `{'length': 10, 'roc': 10}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 67 | Close-to-Close Volatility | A4 Biến động | F | chưa triển khai | `{'length': 10}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 68 | Non-Directional Close-to-Close Volatility | A4 Biến động | F | chưa triển khai | `{'length': 10}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 69 | O-H-L-C Volatility | A4 Biến động | F | chưa triển khai | `{'length': 10}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 70 | Relative Volatility Index | A4 Biến động | F | chưa triển khai | `{'stdev': 10, 'smooth': 14}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 71 | Standard Deviation | A4 Biến động | F | chưa triển khai | `{'length': 20}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 72 | Volatility Region | A4 Biến động | F | không triển khai | `{}` | — |
| 73 | Mass Index | A4 Biến động | F | chưa triển khai | `{'ema': 9, 'sum': 25}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 74 | Net Volume | A5 Khối lượng | D | chưa triển khai | `{'length': 14}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 75 | OBV | A5 Khối lượng | D | chưa triển khai | `{'signal': 20}` | OBV cắt lên EMA20(OBV) → +1; cắt xuống → −1 |
| 76 | Accumulation/Distribution | A5 Khối lượng | D | chưa triển khai | `{'signal': 20}` | AD cắt lên EMA20(AD) → +1; cắt xuống → −1 |
| 77 | MFI | A5 Khối lượng | D | chưa triển khai | `{'length': 14}` | MFI cắt lên 50 → +1; cắt xuống → −1 |
| 78 | Chaikin Money Flow | A5 Khối lượng | D | chưa triển khai | `{'length': 20}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 79 | Chaikin Oscillator | A5 Khối lượng | D | chưa triển khai | `{'fast': 3, 'slow': 10}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 80 | Ease of Movement | A5 Khối lượng | D | chưa triển khai | `{'length': 14, 'divisor': 10000}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 81 | Elder Force Index | A5 Khối lượng | D | chưa triển khai | `{'length': 13}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 82 | Price & Volume Trend | A5 Khối lượng | D | chưa triển khai | `{'signal': 20}` | PVT cắt lên EMA20(PVT) → +1; cắt xuống → −1 |
| 83 | Volume | A5 Khối lượng | F | chưa triển khai | `{}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 84 | Volume Oscillator | A5 Khối lượng | F | chưa triển khai | `{'fast': 5, 'slow': 10}` | bật khi > 0 |
| 85 | Volume Profile Fixed Range | A5 Khối lượng | F | chưa triển khai | `{'value_area': 0.7, 'bins': 100}` | bật khi close nằm ngoài vùng giá trị của ngày trước |
| 86 | VWAP | A6 Khác | D | chưa triển khai | `{'anchor': '1D'}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 87 | VWMA | A6 Khác | D | chưa triển khai | `{'length': 20}` | giá đóng cửa cắt lên đường → +1; cắt xuống → −1 |
| 88 | Pivot Points Standard | A6 Khác | D | chưa triển khai | `{'anchor': '1D'}` | close cắt lên P → +1; cắt xuống → −1 |
| 89 | Balance of Power | A6 Khác | D | chưa triển khai | `{'length': 14}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 90 | Accumulative Swing Index | A6 Khác | D | chưa triển khai | `{'limit': 10000.0, 'signal': 20}` | ASI cắt lên SMA20(ASI) → +1; cắt xuống → −1 |
| 91 | Up/Down | A6 Khác | D | chưa triển khai | `{'length': 14}` | giá trị cắt lên 0 → +1; cắt xuống 0 → −1 |
| 92 | Spread | A6 Khác | F | chưa triển khai | `{'length': 20}` | bật khi |z| > 1 |
| 93 | Correlation Coefficient | A6 Khác | F | chưa triển khai | `{'length': 20}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 94 | Correlation-Log | A6 Khác | F | chưa triển khai | `{'length': 20}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 95 | Rank Correlation | A6 Khác | F | chưa triển khai | `{'length': 20}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 96 | Ratio | A6 Khác | F | chưa triển khai | `{'length': 20}` | bật khi |z| > 1 |
| 97 | Standard Error | A6 Khác | F | chưa triển khai | `{'length': 20}` | bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A] |
| 98 | Sure Thing | A6 Khác | D | không triển khai | `{}` | — |
| 99 | Average Price | A6 Khác | D | chưa triển khai | `{'length': 20}` | ohlc4 cắt lên SMA20 của chính nó → +1; cắt xuống → −1 |
| 100 | Typical Price | A6 Khác | D | chưa triển khai | `{'length': 20}` | hlc3 cắt lên SMA20 của chính nó → +1; cắt xuống → −1 |
| 101 | Median Price | A6 Khác | D | chưa triển khai | `{'length': 20}` | hl2 cắt lên SMA20 của chính nó → +1; cắt xuống → −1 |

## 1. SMA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: trung bình cộng close n nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 9}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 9
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 2. EMA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: EMA(close, n), α = 2/(n+1), khởi tạo bằng SMA n nến đầu (như TradingView)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 9}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 45
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 3. DEMA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: 2·EMA − EMA(EMA)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 9}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 90
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 4. TEMA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: 3·EMA − 3·EMA(EMA) + EMA(EMA(EMA))
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 9}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 135
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 5. Hull MA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: WMA(2·WMA(n/2) − WMA(n), √n)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 9}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 12
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 6. Hamming MA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: trung bình có trọng số cửa sổ Hamming w_i = 0,54 − 0,46·cos(2πi/(n−1))
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 10}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 10
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] độ dài 10, theo 'Moving Average Hamming' của TradingView, chưa đối chiếu

## 7. Arnaud Legoux MA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: ALMA: trọng số Gauss, offset 0,85, sigma 6
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 9, 'offset': 0.85, 'sigma': 6}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 9
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 8. Least Squares MA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: giá trị hồi quy tuyến tính n nến tại nến cuối (linreg, offset 0)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 25}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 25
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 9. Smoothed MA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SMMA/RMA: α = 1/n, khởi tạo SMA
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 7}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 35
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 10. Adaptive MA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: Kaufman AMA: ER = |Δn| / Σ|Δ1|, sc = (ER·(2/3 − 2/31) + 2/31)²
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 9, 'fast': 2, 'slow': 30}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 60
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] dùng Kaufman Adaptive MA (fast 2, slow 30)

## 11. Multi-Timeframe MA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SMA 20 của close M15 ĐÃ ĐÓNG, gắn vào M1 từ thời điểm nến M15 đóng
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20, 'tf': '15m'}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 300
- Độ trễ: dùng nến M15 đã đóng (trễ tới 15 phút so với M15 đang chạy)
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] SMA 20 trên M15

## 12. WMA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: trung bình trọng số tuyến tính n..1
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 9}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 9
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 13. McGinley Dynamic

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: MD_t = MD_{t−1} + (close − MD_{t−1}) / (n·(close/MD_{t−1})⁴)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 70
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 14. Guppy MMA

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: 6 EMA ngắn (3,5,8,10,12,15) và 6 EMA dài (30,35,40,45,50,60)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'short': [3, 5, 8, 10, 12, 15], 'long': [30, 35, 40, 45, 50, 60]}`
- Quy tắc tín hiệu: min(EMA ngắn) vừa vượt lên trên max(EMA dài) → +1; max(EMA ngắn) vừa xuống dưới min(EMA dài) → −1
- Số nến khởi động: 300
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 15. MA Cross

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SMA nhanh và SMA chậm
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'fast': 9, 'slow': 21}`
- Quy tắc tín hiệu: SMA nhanh cắt lên SMA chậm → +1; cắt xuống → −1
- Số nến khởi động: 21
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 16. EMA Cross

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: EMA nhanh và EMA chậm
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'fast': 9, 'slow': 21}`
- Quy tắc tín hiệu: EMA nhanh cắt lên EMA chậm → +1; cắt xuống → −1
- Số nến khởi động: 105
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 17. MA-EMA Cross

- Nhóm: A1 MA · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SMA và EMA cùng độ dài
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'sma': 10, 'ema': 10}`
- Quy tắc tín hiệu: EMA cắt lên SMA → +1; cắt xuống → −1
- Số nến khởi động: 50
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] SMA 10 / EMA 10 theo 'MA with EMA Cross'

## 18. SuperTrend

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: dải hl2 ± factor·ATR(RMA), đổi hướng khi close vượt dải
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'atr': 10, 'factor': 3.0}`
- Quy tắc tín hiệu: đổi sang xu hướng tăng → +1; đổi sang giảm → −1
- Số nến khởi động: 50
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 19. Ichimoku Cloud

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: Tenkan 9, Kijun 26, Senkou B 52, mây dịch tới 26 nến (mây tại t tính từ dữ liệu t−26)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'tenkan': 9, 'kijun': 26, 'senkou_b': 52, 'displacement': 26}`
- Quy tắc tín hiệu: close cắt lên đỉnh mây → +1; cắt xuống đáy mây → −1
- Số nến khởi động: 78
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] dùng tín hiệu giá phá mây (không dùng Chikou vì Chikou là giá dịch lùi)

## 20. Parabolic SAR

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SAR Wilder, AF 0,02 tăng 0,02 tối đa 0,2
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'start': 0.02, 'inc': 0.02, 'max': 0.2}`
- Quy tắc tín hiệu: SAR đổi xuống dưới giá → +1; lên trên giá → −1
- Số nến khởi động: 10
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 21. Directional Movement

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: +DI và −DI (RMA 14)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: +DI cắt lên −DI → +1; cắt xuống → −1
- Số nến khởi động: 70
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 22. Vortex

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: VI+ = Σ|H−L₋₁|/ΣTR, VI− = Σ|L−H₋₁|/ΣTR
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: VI+ cắt lên VI− → +1; cắt xuống → −1
- Số nến khởi động: 15
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 23. Williams Alligator

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SMMA hl2: hàm 13 dịch 8, răng 8 dịch 5, môi 5 dịch 3 (giá trị tại t tính từ dữ liệu quá khứ)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'jaw': [13, 8], 'teeth': [8, 5], 'lips': [5, 3]}`
- Quy tắc tín hiệu: môi > răng > hàm vừa thành đúng → +1; môi < răng < hàm vừa thành đúng → −1
- Số nến khởi động: 100
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 24. Williams Fractal

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: fractal 5 nến (2 trái, 2 phải); xác nhận sau 2 nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'periods': 2}`
- Quy tắc tín hiệu: close phá lên trên đỉnh fractal ĐÃ XÁC NHẬN gần nhất → +1; phá xuống đáy fractal gần nhất → −1
- Số nến khởi động: 5
- Độ trễ: fractal chỉ dùng sau khi 2 nến bên phải đã đóng
- Rủi ro repaint: không (chỉ dùng điểm đã xác nhận)
- Tương đương TradingView: chưa đối chiếu

## 25. Aroon

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: Aroon Up/Down = 100·(n − số nến từ đỉnh/đáy n+1 nến)/n
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: Aroon Up cắt lên Aroon Down → +1; cắt xuống → −1
- Số nến khởi động: 15
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 26. Trend Strength Index

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: tương quan Pearson giữa close và chỉ số nến trong n nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 14
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] định nghĩa theo 'Trend Strength Index' của TradingView (correlation với thời gian)

## 27. Zig Zag

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: ZigZag trực tuyến trên high/low với độ lệch 0,5%; sự kiện tại nến XÁC NHẬN điểm xoay
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'deviation': 0.005}`
- Quy tắc tín hiệu: đáy được xác nhận → +1; đỉnh được xác nhận → −1
- Số nến khởi động: 0
- Độ trễ: trễ tới khi giá đảo đủ 0,5% so với cực trị
- Rủi ro repaint: không (chỉ dùng điểm đã xác nhận)
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] độ lệch 0,5% thay cho mặc định 5% của TradingView (5% hầu như không xảy ra trên M1)
- Ghi chú: tính độc lập trong module chỉ báo, không dùng module nhãn

## 28. Linear Regression Curve

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: giá trị hồi quy tuyến tính n nến tại nến cuối
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 9}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 9
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] độ dài 9 để khác Least Squares MA (25)

## 29. Linear Regression Slope

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: hệ số góc hồi quy tuyến tính close theo thời gian, n nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 14
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 30. Keltner Channels

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: EMA 20 ± 2·ATR 10
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20, 'mult': 2.0, 'atr': 10}`
- Quy tắc tín hiệu: close cắt lên dải trên → +1; cắt xuống dải dưới → −1
- Số nến khởi động: 100
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 31. Donchian Channels

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: max high / min low của n nến TRƯỚC
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: close vượt max high 20 nến trước → +1; thủng min low → −1
- Số nến khởi động: 21
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 32. Price Channel

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: đường giữa = (max high + min low)/2 của n nến trước
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 21
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] dùng cắt đường giữa để không trùng Donchian

## 33. MA Channel

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SMA(high, n) và SMA(low, n)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: close cắt lên SMA(high) → +1; cắt xuống SMA(low) → −1
- Số nến khởi động: 20
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] định nghĩa kênh MA bằng SMA high/low

## 34. Chande Kroll Stop

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: stop long/short = max/min(high/low ∓ x·ATR p) rồi max/min q nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'p': 10, 'x': 1.0, 'q': 9}`
- Quy tắc tín hiệu: close cắt lên stop short → +1; cắt xuống stop long → −1
- Số nến khởi động: 50
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 35. 52-Week High/Low

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: max high / min low của 1.440 nến (1 ngày) TRƯỚC
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 1440}`
- Quy tắc tín hiệu: close vượt đỉnh 1 ngày → +1; thủng đáy 1 ngày → −1
- Số nến khởi động: 1441
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] đổi cửa sổ 52 tuần → 1 ngày theo spec §3

## 36. Majority Rule

- Nhóm: A2 Xu hướng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: % số nến tăng (close > close₋₁) trong n nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: tỷ lệ cắt lên 50% → +1; cắt xuống 50% → −1
- Số nến khởi động: 15
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] ngưỡng 50%

## 37. ADX

- Nhóm: A2 Xu hướng · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: ADX Wilder (RMA 14)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 140
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 38. MACD

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: EMA12 − EMA26, signal EMA9
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'fast': 12, 'slow': 26, 'signal': 9}`
- Quy tắc tín hiệu: đường chính cắt lên đường tín hiệu → +1; cắt xuống → −1
- Số nến khởi động: 175
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 39. RSI

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: RSI Wilder (RMA)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: RSI cắt lên 50 → +1; cắt xuống 50 → −1
- Số nến khởi động: 140
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 40. Stochastic

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: %K = SMA(100·(C−LL)/(HH−LL), 1), %D = SMA(%K, 3)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'k': 14, 'smooth_k': 1, 'd': 3}`
- Quy tắc tín hiệu: %K cắt lên %D → +1; cắt xuống → −1
- Số nến khởi động: 17
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 41. Stochastic RSI

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: Stoch của RSI 14 (14), K = SMA 3, D = SMA 3 của K
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'rsi': 14, 'stoch': 14, 'k': 3, 'd': 3}`
- Quy tắc tín hiệu: K cắt lên D → +1; cắt xuống → −1
- Số nến khởi động: 175
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 42. Connors RSI

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: (RSI(close,3) + RSI(streak,2) + PercentRank(ROC1,100))/3
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'rsi': 3, 'streak': 2, 'rank': 100}`
- Quy tắc tín hiệu: CRSI cắt lên 50 → +1; cắt xuống → −1
- Số nến khởi động: 110
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] ngưỡng 50

## 43. Awesome Oscillator

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SMA(hl2,5) − SMA(hl2,34)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'fast': 5, 'slow': 34}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 34
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 44. Accelerator Oscillator

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: AO − SMA(AO,5)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'fast': 5, 'slow': 34, 'smooth': 5}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 39
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 45. Momentum

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: close − close₋ₙ
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 10}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 10
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 46. Chande Momentum Oscillator

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: 100·(ΣΔ⁺ − ΣΔ⁻)/(ΣΔ⁺ + ΣΔ⁻)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 9}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 10
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 47. Price Oscillator

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: PPO = 100·(EMA nhanh − EMA chậm)/EMA chậm
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'fast': 10, 'slow': 21}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 105
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 48. Detrended Price Oscillator

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: DPO = close − SMA(close, n) của n/2+1 nến trước (không căn giữa)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 21}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 33
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: chế độ không căn giữa (centered = false) để không nhìn tương lai

## 49. TRIX

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: 10000·Δlog(EMA(EMA(EMA(close))))
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 18}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 270
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 50. Fisher Transform

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: Fisher của hl2 chuẩn hoá trong n nến, trigger = Fisher₋₁
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 9}`
- Quy tắc tín hiệu: Fisher cắt lên trigger → +1; cắt xuống → −1
- Số nến khởi động: 30
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 51. Ultimate Oscillator

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: 100·(4·A7 + 2·A14 + A28)/7 với A = ΣBP/ΣTR
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'fast': 7, 'mid': 14, 'slow': 28}`
- Quy tắc tín hiệu: UO cắt lên 50 → +1; cắt xuống → −1
- Số nến khởi động: 29
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] ngưỡng 50

## 52. Williams %R

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: −100·(HH − C)/(HH − LL)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: %R cắt lên −50 → +1; cắt xuống → −1
- Số nến khởi động: 14
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] ngưỡng −50

## 53. SMI Ergodic

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: TSI(5,20) và signal EMA 5
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'short': 5, 'long': 20, 'signal': 5}`
- Quy tắc tín hiệu: đường chính cắt lên đường tín hiệu → +1; cắt xuống → −1
- Số nến khởi động: 125
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 54. Relative Vigor Index

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SMA(Σ trọng số (C−O))/SMA(Σ trọng số (H−L)), signal trọng số 1-2-2-1
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 10}`
- Quy tắc tín hiệu: đường chính cắt lên đường tín hiệu → +1; cắt xuống → −1
- Số nến khởi động: 16
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 55. True Strength Index

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: 100·EMA(EMA(Δ,25),13)/EMA(EMA(|Δ|,25),13), signal EMA 13
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'long': 25, 'short': 13, 'signal': 13}`
- Quy tắc tín hiệu: đường chính cắt lên đường tín hiệu → +1; cắt xuống → −1
- Số nến khởi động: 255
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 56. Coppock Curve

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: WMA(ROC14 + ROC11, 10)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'wma': 10, 'long': 14, 'short': 11}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 24
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 57. Rate of Change

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: 100·(close/close₋ₙ − 1)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 9}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 9
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 58. Klinger Oscillator

- Nhóm: A3 Dao động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: EMA34(VF) − EMA55(VF), VF = ±volume theo hướng hlc3, signal EMA 13
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'fast': 34, 'slow': 55, 'signal': 13}`
- Quy tắc tín hiệu: đường chính cắt lên đường tín hiệu → +1; cắt xuống → −1
- Số nến khởi động: 300
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 59. Bollinger Bands

- Nhóm: A4 Biến động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SMA 20 ± 2·stdev (stdev quần thể)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20, 'mult': 2.0}`
- Quy tắc tín hiệu: close cắt lên dải trên → +1; cắt xuống dải dưới → −1 (breakout)
- Số nến khởi động: 20
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 60. BB %B

- Nhóm: A4 Biến động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: %B = (close − dải dưới)/(dải trên − dải dưới)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20, 'mult': 2.0}`
- Quy tắc tín hiệu: %B cắt lên 0,5 → +1; cắt xuống → −1
- Số nến khởi động: 20
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] dùng ngưỡng 0,5 để không trùng Bollinger Bands

## 61. Standard Error Bands

- Nhóm: A4 Biến động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: linreg 21 ± 2·sai số chuẩn, làm mượt SMA 3
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 21, 'mult': 2.0, 'smooth': 3}`
- Quy tắc tín hiệu: close cắt lên dải trên → +1; cắt xuống dải dưới → −1
- Số nến khởi động: 24
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 62. Envelopes

- Nhóm: A4 Biến động · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SMA 20 ± 10%
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20, 'percent': 10.0}`
- Quy tắc tín hiệu: close cắt lên dải trên → +1; cắt xuống dải dưới → −1
- Số nến khởi động: 20
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: tham số mặc định TradingView 10%: trên M1 gần như không có tín hiệu — giữ đúng spec, không tự đổi

## 63. BB Width

- Nhóm: A4 Biến động · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: (dải trên − dải dưới)/SMA 20
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20, 'mult': 2.0}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1460
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 64. ATR

- Nhóm: A4 Biến động · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: RMA(true range, 14) / close
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1510
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: chia cho close để so sánh giữa các mức giá (không đổi thứ tự trong 1 ngày)

## 65. Historical Volatility

- Nhóm: A4 Biến động · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: stdev(log return, 10)·√(365·1440)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 10}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1450
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 66. Chaikin Volatility

- Nhóm: A4 Biến động · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: 100·(EMA(H−L,10)/EMA(H−L,10)₋₁₀ − 1)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 10, 'roc': 10}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1500
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 67. Close-to-Close Volatility

- Nhóm: A4 Biến động · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: stdev(log return, 10) (có trừ trung bình)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 10}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1450
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 68. Non-Directional Close-to-Close Volatility

- Nhóm: A4 Biến động · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: √(mean(log return², 10)) (không trừ trung bình)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 10}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1450
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 69. O-H-L-C Volatility

- Nhóm: A4 Biến động · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: Garman–Klass: √mean(0,5·ln(H/L)² − (2ln2 − 1)·ln(C/O)², 10)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 10}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1450
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] dùng ước lượng Garman–Klass

## 70. Relative Volatility Index

- Nhóm: A4 Biến động · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: RSI dùng stdev 10 thay cho thay đổi giá, làm mượt 14
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'stdev': 10, 'smooth': 14}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1590
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 71. Standard Deviation

- Nhóm: A4 Biến động · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: stdev(close, 20)/close
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1460
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 72. Volatility Region

- Nhóm: A4 Biến động · Loại: filter · Trạng thái: **không triển khai** — lý do: không tìm được định nghĩa chuẩn (không phải chỉ báo built-in có công thức công bố); không tự thay bằng chỉ báo khác
- Công thức: —
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{}`
- Quy tắc tín hiệu: —
- Số nến khởi động: 0
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 73. Mass Index

- Nhóm: A4 Biến động · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: Σ₂₅ EMA9(H−L)/EMA9(EMA9(H−L))
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'ema': 9, 'sum': 25}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1530
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 74. Net Volume

- Nhóm: A5 Khối lượng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: volume·sign(Δclose), cộng dồn 14 nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 14
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] tổng 14 nến để thành tín hiệu

## 75. OBV

- Nhóm: A5 Khối lượng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: OBV cộng dồn volume·sign(Δclose)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'signal': 20}`
- Quy tắc tín hiệu: OBV cắt lên EMA20(OBV) → +1; cắt xuống → −1
- Số nến khởi động: 100
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] dùng EMA 20 của OBV làm đường tín hiệu

## 76. Accumulation/Distribution

- Nhóm: A5 Khối lượng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: Σ volume·((C−L)−(H−C))/(H−L)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'signal': 20}`
- Quy tắc tín hiệu: AD cắt lên EMA20(AD) → +1; cắt xuống → −1
- Số nến khởi động: 100
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] dùng EMA 20 làm đường tín hiệu

## 77. MFI

- Nhóm: A5 Khối lượng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: Money Flow Index 14 (hlc3·volume)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: MFI cắt lên 50 → +1; cắt xuống → −1
- Số nến khởi động: 15
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] ngưỡng 50

## 78. Chaikin Money Flow

- Nhóm: A5 Khối lượng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: Σ MFV / Σ volume, 20 nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 20
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 79. Chaikin Oscillator

- Nhóm: A5 Khối lượng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: EMA3(AD) − EMA10(AD)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'fast': 3, 'slow': 10}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 50
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 80. Ease of Movement

- Nhóm: A5 Khối lượng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SMA14(10000·Δhl2·(H−L)/volume)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14, 'divisor': 10000}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 15
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 81. Elder Force Index

- Nhóm: A5 Khối lượng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: EMA13(Δclose·volume)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 13}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 65
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 82. Price & Volume Trend

- Nhóm: A5 Khối lượng · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: Σ volume·Δclose/close₋₁
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'signal': 20}`
- Quy tắc tín hiệu: PVT cắt lên EMA20(PVT) → +1; cắt xuống → −1
- Số nến khởi động: 100
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] dùng EMA 20 làm đường tín hiệu

## 83. Volume

- Nhóm: A5 Khối lượng · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: volume nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1440
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 84. Volume Oscillator

- Nhóm: A5 Khối lượng · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: 100·(EMA5(vol) − EMA10(vol))/EMA10(vol)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'fast': 5, 'slow': 10}`
- Quy tắc tín hiệu: bật khi > 0
- Số nến khởi động: 50
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 85. Volume Profile Fixed Range

- Nhóm: A5 Khối lượng · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: vùng giá trị 70% (VAH/VAL) theo volume của NGÀY UTC TRƯỚC, 100 mức giá
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'value_area': 0.7, 'bins': 100}`
- Quy tắc tín hiệu: bật khi close nằm ngoài vùng giá trị của ngày trước
- Số nến khởi động: 1440
- Độ trễ: dùng hồ sơ volume của ngày đã kết thúc
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] 'Fixed Range' cần chọn vùng bằng tay; dùng ngày UTC trước làm vùng cố định

## 86. VWAP

- Nhóm: A6 Khác · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: Σ(hlc3·vol)/Σvol, reset 00:00 UTC
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'anchor': '1D'}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 1
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 87. VWMA

- Nhóm: A6 Khác · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: Σ(close·vol)/Σvol, 20 nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: giá đóng cửa cắt lên đường → +1; cắt xuống → −1
- Số nến khởi động: 20
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 88. Pivot Points Standard

- Nhóm: A6 Khác · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: P = (H+L+C)/3 của ngày UTC trước
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'anchor': '1D'}`
- Quy tắc tín hiệu: close cắt lên P → +1; cắt xuống → −1
- Số nến khởi động: 1440
- Độ trễ: dùng ngày đã kết thúc
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] chỉ dùng mức P (không dùng R/S)

## 89. Balance of Power

- Nhóm: A6 Khác · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: SMA14((C−O)/(H−L))
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 14
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] làm mượt SMA 14

## 90. Accumulative Swing Index

- Nhóm: A6 Khác · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: Σ Swing Index Wilder, limit move T = 10000
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'limit': 10000.0, 'signal': 20}`
- Quy tắc tín hiệu: ASI cắt lên SMA20(ASI) → +1; cắt xuống → −1
- Số nến khởi động: 25
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] crypto không có giới hạn biên độ ngày; dùng T = 10000 như mặc định TradingView
- Ghi chú: [A] SMA 20 làm đường tín hiệu

## 91. Up/Down

- Nhóm: A6 Khác · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: chênh lệch volume mua chủ động − bán chủ động (taker buy − taker sell), cộng 14 nến
- Nguồn công thức: Binance taker_buy_volume (thay cho Up/Down Volume cần dữ liệu khung nhỏ hơn)
- Tham số mặc định: `{'length': 14}`
- Quy tắc tín hiệu: giá trị cắt lên 0 → +1; cắt xuống 0 → −1
- Số nến khởi động: 14
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: [A] Up/Down Volume của TradingView cần nến khung nhỏ hơn M1; thay bằng taker buy/sell của Binance — ghi rõ khác định nghĩa

## 92. Spread

- Nhóm: A6 Khác · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: spread = log(close) − log(close cặp tham chiếu); z = (spread − SMA20)/stdev20
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: bật khi |z| > 1
- Số nến khởi động: 20
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: cặp tham chiếu BTCUSDT (với BTCUSDT dùng ETHUSDT)
- Ghi chú: [A] dùng log để không phụ thuộc mức giá; ngưỡng |z| > 1

## 93. Correlation Coefficient

- Nhóm: A6 Khác · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: tương quan Pearson close với close cặp tham chiếu, 20 nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1460
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: cặp tham chiếu BTCUSDT (với BTCUSDT dùng ETHUSDT)

## 94. Correlation-Log

- Nhóm: A6 Khác · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: tương quan Pearson của log return với cặp tham chiếu, 20 nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1461
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: cặp tham chiếu BTCUSDT (với BTCUSDT dùng ETHUSDT)

## 95. Rank Correlation

- Nhóm: A6 Khác · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: tương quan hạng Spearman close với cặp tham chiếu, 20 nến
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1460
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: cặp tham chiếu BTCUSDT (với BTCUSDT dùng ETHUSDT)

## 96. Ratio

- Nhóm: A6 Khác · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: ratio = close / close cặp tham chiếu; z = (ratio − SMA20)/stdev20
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: bật khi |z| > 1
- Số nến khởi động: 20
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: cặp tham chiếu BTCUSDT (với BTCUSDT dùng ETHUSDT)
- Ghi chú: [A] ngưỡng |z| > 1

## 97. Standard Error

- Nhóm: A6 Khác · Loại: filter · Trạng thái: **chưa triển khai**
- Công thức: sai số chuẩn của hồi quy tuyến tính close 20 nến / close
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]
- Số nến khởi động: 1460
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 98. Sure Thing

- Nhóm: A6 Khác · Loại: directional · Trạng thái: **không triển khai** — lý do: không tìm được công thức chuẩn công bố cho 'Sure Thing'; không tự thay bằng chỉ báo khác
- Công thức: —
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{}`
- Quy tắc tín hiệu: —
- Số nến khởi động: 0
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu

## 99. Average Price

- Nhóm: A6 Khác · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: ohlc4 so với SMA20(ohlc4)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: ohlc4 cắt lên SMA20 của chính nó → +1; cắt xuống → −1
- Số nến khởi động: 20
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: dùng như giá so với MA của chính nó (spec §A6)

## 100. Typical Price

- Nhóm: A6 Khác · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: hlc3 so với SMA20(hlc3)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: hlc3 cắt lên SMA20 của chính nó → +1; cắt xuống → −1
- Số nến khởi động: 20
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: dùng như giá so với MA của chính nó (spec §A6)

## 101. Median Price

- Nhóm: A6 Khác · Loại: directional · Trạng thái: **chưa triển khai**
- Công thức: hl2 so với SMA20(hl2)
- Nguồn công thức: TradingView built-in
- Tham số mặc định: `{'length': 20}`
- Quy tắc tín hiệu: hl2 cắt lên SMA20 của chính nó → +1; cắt xuống → −1
- Số nến khởi động: 20
- Độ trễ: tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1
- Rủi ro repaint: không
- Tương đương TradingView: chưa đối chiếu
- Ghi chú: dùng như giá so với MA của chính nó (spec §A6)
