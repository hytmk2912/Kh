"""Registry chỉ báo — một phiếu cho MỌI tên ở Phụ lục A của docs/ind/spec.md (kể cả không triển khai được).

Quy ước chung (chốt trước khi chấm, ghi trong CHANGELOG):
- Directional (D): tín hiệu là SỰ KIỆN tại nến điều kiện vừa chuyển sang đúng: +1 Long, −1 Short, 0.
- Filter (F): tín hiệu là TRẠNG THÁI đúng/sai. Quy tắc mặc định cho filter [A]: giá trị chỉ báo > trung vị của
  chính nó trong 1.440 nến (1 ngày) TRƯỚC đó (không gồm nến hiện tại). Không bao giờ suy ra hướng từ filter.
- Tham số mặc định theo TradingView khi biết; không chắc → [A].
- Cặp tham chiếu cho Spread/Ratio/Correlation: BTCUSDT (với BTCUSDT dùng ETHUSDT).
Module này KHÔNG import module nhãn.
"""
from __future__ import annotations

from dataclasses import dataclass, field

FILTER_RULE = "bật khi giá trị > trung vị của chính nó trong 1.440 nến trước (không gồm nến hiện tại) [A]"


@dataclass
class Card:
    name: str
    group: str
    kind: str                      # "D" hoặc "F"
    formula: str
    params: dict
    rule: str
    source: str = "TradingView built-in"
    warmup: int = 0                # số nến khởi động (giá trị trước đó là NaN)
    lag: str = "tín hiệu tại đóng cửa nến t, vào lệnh ở mở cửa nến t+1"
    repaint: str = "không"
    tv_note: str = "chưa đối chiếu"
    notes: list = field(default_factory=list)
    not_implementable: str = ""    # lý do nếu không triển khai được

    @property
    def key(self) -> str:
        return self.name


def _c(name, group, kind, formula, params, rule, warmup, **kw) -> Card:
    return Card(name=name, group=group, kind=kind, formula=formula, params=params, rule=rule, warmup=warmup, **kw)


CROSS = "giá đóng cửa cắt lên đường → +1; cắt xuống → −1"
ZERO = "giá trị cắt lên 0 → +1; cắt xuống 0 → −1"
SIG = "đường chính cắt lên đường tín hiệu → +1; cắt xuống → −1"

CARDS: list[Card] = [
    # ---------------- A1. MA (D) — quy tắc: close cắt đường MA
    _c("SMA", "A1 MA", "D", "trung bình cộng close n nến", {"length": 9}, CROSS, 9),
    _c("EMA", "A1 MA", "D", "EMA(close, n), α = 2/(n+1), khởi tạo bằng SMA n nến đầu (như TradingView)", {"length": 9}, CROSS, 45),
    _c("DEMA", "A1 MA", "D", "2·EMA − EMA(EMA)", {"length": 9}, CROSS, 90),
    _c("TEMA", "A1 MA", "D", "3·EMA − 3·EMA(EMA) + EMA(EMA(EMA))", {"length": 9}, CROSS, 135),
    _c("Hull MA", "A1 MA", "D", "WMA(2·WMA(n/2) − WMA(n), √n)", {"length": 9}, CROSS, 12),
    _c("Hamming MA", "A1 MA", "D", "trung bình có trọng số cửa sổ Hamming w_i = 0,54 − 0,46·cos(2πi/(n−1))", {"length": 10}, CROSS, 10,
       notes=["[A] độ dài 10, theo 'Moving Average Hamming' của TradingView, chưa đối chiếu"]),
    _c("Arnaud Legoux MA", "A1 MA", "D", "ALMA: trọng số Gauss, offset 0,85, sigma 6", {"length": 9, "offset": 0.85, "sigma": 6}, CROSS, 9),
    _c("Least Squares MA", "A1 MA", "D", "giá trị hồi quy tuyến tính n nến tại nến cuối (linreg, offset 0)", {"length": 25}, CROSS, 25),
    _c("Smoothed MA", "A1 MA", "D", "SMMA/RMA: α = 1/n, khởi tạo SMA", {"length": 7}, CROSS, 35),
    _c("Adaptive MA", "A1 MA", "D", "Kaufman AMA: ER = |Δn| / Σ|Δ1|, sc = (ER·(2/3 − 2/31) + 2/31)²", {"length": 9, "fast": 2, "slow": 30}, CROSS, 60,
       notes=["[A] dùng Kaufman Adaptive MA (fast 2, slow 30)"]),
    _c("Multi-Timeframe MA", "A1 MA", "D", "SMA 20 của close M15 ĐÃ ĐÓNG, gắn vào M1 từ thời điểm nến M15 đóng", {"length": 20, "tf": "15m"}, CROSS, 20 * 15,
       lag="dùng nến M15 đã đóng (trễ tới 15 phút so với M15 đang chạy)", notes=["[A] SMA 20 trên M15"]),
    _c("WMA", "A1 MA", "D", "trung bình trọng số tuyến tính n..1", {"length": 9}, CROSS, 9),
    _c("McGinley Dynamic", "A1 MA", "D", "MD_t = MD_{t−1} + (close − MD_{t−1}) / (n·(close/MD_{t−1})⁴)", {"length": 14}, CROSS, 70),
    _c("Guppy MMA", "A1 MA", "D", "6 EMA ngắn (3,5,8,10,12,15) và 6 EMA dài (30,35,40,45,50,60)", {"short": [3, 5, 8, 10, 12, 15], "long": [30, 35, 40, 45, 50, 60]},
       "min(EMA ngắn) vừa vượt lên trên max(EMA dài) → +1; max(EMA ngắn) vừa xuống dưới min(EMA dài) → −1", 300),
    _c("MA Cross", "A1 MA", "D", "SMA nhanh và SMA chậm", {"fast": 9, "slow": 21}, "SMA nhanh cắt lên SMA chậm → +1; cắt xuống → −1", 21),
    _c("EMA Cross", "A1 MA", "D", "EMA nhanh và EMA chậm", {"fast": 9, "slow": 21}, "EMA nhanh cắt lên EMA chậm → +1; cắt xuống → −1", 105),
    _c("MA-EMA Cross", "A1 MA", "D", "SMA và EMA cùng độ dài", {"sma": 10, "ema": 10}, "EMA cắt lên SMA → +1; cắt xuống → −1", 50,
       notes=["[A] SMA 10 / EMA 10 theo 'MA with EMA Cross'"]),
    # ---------------- A2. Xu hướng
    _c("SuperTrend", "A2 Xu hướng", "D", "dải hl2 ± factor·ATR(RMA), chép theo mã tham chiếu Pine `ta.supertrend` của TradingView", {"atr": 10, "factor": 3.0},
       "đổi sang xu hướng tăng → +1; đổi sang giảm → −1", 50),
    _c("Ichimoku Cloud", "A2 Xu hướng", "D", "Tenkan 9, Kijun 26, Senkou B 52, mây dịch tới 26 nến (mây tại t tính từ dữ liệu t−26)",
       {"tenkan": 9, "kijun": 26, "senkou_b": 52, "displacement": 26}, "close cắt lên đỉnh mây → +1; cắt xuống đáy mây → −1", 78,
       notes=["[A] dùng tín hiệu giá phá mây (không dùng Chikou vì Chikou là giá dịch lùi)"]),
    _c("Parabolic SAR", "A2 Xu hướng", "D", "SAR Wilder, AF 0,02 tăng 0,02 tối đa 0,2; SAR nến sau được kẹp bởi high/low nến hiện tại và nến trước rồi mới xét đảo chiều (định nghĩa gốc Wilder, như TA-Lib)", {"start": 0.02, "inc": 0.02, "max": 0.2},
       "SAR đổi xuống dưới giá → +1; lên trên giá → −1", 10),
    _c("Directional Movement", "A2 Xu hướng", "D", "+DI và −DI (RMA 14)", {"length": 14}, "+DI cắt lên −DI → +1; cắt xuống → −1", 70),
    _c("Vortex", "A2 Xu hướng", "D", "VI+ = Σ|H−L₋₁|/ΣTR, VI− = Σ|L−H₋₁|/ΣTR", {"length": 14}, "VI+ cắt lên VI− → +1; cắt xuống → −1", 15),
    _c("Williams Alligator", "A2 Xu hướng", "D", "SMMA hl2: hàm 13 dịch 8, răng 8 dịch 5, môi 5 dịch 3 (giá trị tại t tính từ dữ liệu quá khứ)",
       {"jaw": [13, 8], "teeth": [8, 5], "lips": [5, 3]}, "môi > răng > hàm vừa thành đúng → +1; môi < răng < hàm vừa thành đúng → −1", 100),
    _c("Williams Fractal", "A2 Xu hướng", "D", "fractal 5 nến (2 trái, 2 phải); xác nhận sau 2 nến",
       {"periods": 2}, "close phá lên trên đỉnh fractal ĐÃ XÁC NHẬN gần nhất → +1; phá xuống đáy fractal gần nhất → −1", 5,
       lag="fractal chỉ dùng sau khi 2 nến bên phải đã đóng", repaint="không (chỉ dùng điểm đã xác nhận)"),
    _c("Aroon", "A2 Xu hướng", "D", "Aroon Up/Down = 100·(n − số nến từ đỉnh/đáy n+1 nến)/n", {"length": 14},
       "Aroon Up cắt lên Aroon Down → +1; cắt xuống → −1", 15),
    _c("Trend Strength Index", "A2 Xu hướng", "D", "tương quan Pearson giữa close và chỉ số nến trong n nến", {"length": 14}, ZERO, 14,
       notes=["[A] định nghĩa theo 'Trend Strength Index' của TradingView (correlation với thời gian)"]),
    _c("Zig Zag", "A2 Xu hướng", "D", "ZigZag trực tuyến trên high/low với độ lệch 0,5%; sự kiện tại nến XÁC NHẬN điểm xoay",
       {"deviation": 0.005}, "đáy được xác nhận → +1; đỉnh được xác nhận → −1", 0,
       lag="trễ tới khi giá đảo đủ 0,5% so với cực trị", repaint="không (chỉ dùng điểm đã xác nhận)",
       notes=["[A] độ lệch 0,5% thay cho mặc định 5% của TradingView (5% hầu như không xảy ra trên M1)",
              "tính độc lập trong module chỉ báo, không dùng module nhãn"]),
    _c("Linear Regression Curve", "A2 Xu hướng", "D", "giá trị hồi quy tuyến tính n nến tại nến cuối", {"length": 9}, CROSS, 9,
       notes=["[A] độ dài 9 để khác Least Squares MA (25)"]),
    _c("Linear Regression Slope", "A2 Xu hướng", "D", "hệ số góc hồi quy tuyến tính close theo thời gian, n nến", {"length": 14}, ZERO, 14),
    _c("Keltner Channels", "A2 Xu hướng", "D", "EMA 20 ± 2·ATR 10", {"length": 20, "mult": 2.0, "atr": 10},
       "close cắt lên dải trên → +1; cắt xuống dải dưới → −1", 100),
    _c("Donchian Channels", "A2 Xu hướng", "D", "max high / min low của n nến TRƯỚC", {"length": 20},
       "close vượt max high 20 nến trước → +1; thủng min low → −1", 21),
    _c("Price Channel", "A2 Xu hướng", "D", "đường giữa = (max high + min low)/2 của n nến trước", {"length": 20}, CROSS, 21,
       notes=["[A] dùng cắt đường giữa để không trùng Donchian"]),
    _c("MA Channel", "A2 Xu hướng", "D", "SMA(high, n) và SMA(low, n)", {"length": 20},
       "close cắt lên SMA(high) → +1; cắt xuống SMA(low) → −1", 20, notes=["[A] định nghĩa kênh MA bằng SMA high/low"]),
    _c("Chande Kroll Stop", "A2 Xu hướng", "D", "stop long/short = max/min(high/low ∓ x·ATR p) rồi max/min q nến", {"p": 10, "x": 1.0, "q": 9},
       "close cắt lên stop short → +1; cắt xuống stop long → −1", 50),
    _c("52-Week High/Low", "A2 Xu hướng", "D", "max high / min low của 1.440 nến (1 ngày) TRƯỚC", {"length": 1440},
       "close vượt đỉnh 1 ngày → +1; thủng đáy 1 ngày → −1", 1441, notes=["[A] đổi cửa sổ 52 tuần → 1 ngày theo spec §3"]),
    _c("Majority Rule", "A2 Xu hướng", "D", "% số nến tăng (close > close₋₁) trong n nến", {"length": 14},
       "tỷ lệ cắt lên 50% → +1; cắt xuống 50% → −1", 15, notes=["[A] ngưỡng 50%"]),
    _c("ADX", "A2 Xu hướng", "F", "ADX Wilder (RMA 14)", {"length": 14}, FILTER_RULE, 140),
    # ---------------- A3. Dao động (D)
    _c("MACD", "A3 Dao động", "D", "EMA12 − EMA26, signal EMA9", {"fast": 12, "slow": 26, "signal": 9}, SIG, 175),
    _c("RSI", "A3 Dao động", "D", "RSI Wilder (RMA)", {"length": 14}, "RSI cắt lên 50 → +1; cắt xuống 50 → −1", 140),
    _c("Stochastic", "A3 Dao động", "D", "%K = SMA(100·(C−LL)/(HH−LL), 1), %D = SMA(%K, 3)", {"k": 14, "smooth_k": 1, "d": 3},
       "%K cắt lên %D → +1; cắt xuống → −1", 17),
    _c("Stochastic RSI", "A3 Dao động", "D", "Stoch của RSI 14 (14), K = SMA 3, D = SMA 3 của K", {"rsi": 14, "stoch": 14, "k": 3, "d": 3},
       "K cắt lên D → +1; cắt xuống → −1", 175),
    _c("Connors RSI", "A3 Dao động", "D", "(RSI(close,3) + RSI(streak,2) + PercentRank(ROC1,100))/3", {"rsi": 3, "streak": 2, "rank": 100},
       "CRSI cắt lên 50 → +1; cắt xuống → −1", 110, notes=["[A] ngưỡng 50"]),
    _c("Awesome Oscillator", "A3 Dao động", "D", "SMA(hl2,5) − SMA(hl2,34)", {"fast": 5, "slow": 34}, ZERO, 34),
    _c("Accelerator Oscillator", "A3 Dao động", "D", "AO − SMA(AO,5)", {"fast": 5, "slow": 34, "smooth": 5}, ZERO, 39),
    _c("Momentum", "A3 Dao động", "D", "close − close₋ₙ", {"length": 10}, ZERO, 10),
    _c("Chande Momentum Oscillator", "A3 Dao động", "D", "100·(ΣΔ⁺ − ΣΔ⁻)/(ΣΔ⁺ + ΣΔ⁻)", {"length": 9}, ZERO, 10),
    _c("Price Oscillator", "A3 Dao động", "D", "PPO = 100·(EMA nhanh − EMA chậm)/EMA chậm", {"fast": 10, "slow": 21}, ZERO, 105),
    _c("Detrended Price Oscillator", "A3 Dao động", "D", "DPO = close − SMA(close, n) của n/2+1 nến trước (không căn giữa)",
       {"length": 21}, ZERO, 33, notes=["chế độ không căn giữa (centered = false) để không nhìn tương lai"]),
    _c("TRIX", "A3 Dao động", "D", "10000·Δlog(EMA(EMA(EMA(close))))", {"length": 18}, ZERO, 270),
    _c("Fisher Transform", "A3 Dao động", "D", "Fisher của hl2 chuẩn hoá trong n nến, trigger = Fisher₋₁", {"length": 9},
       "Fisher cắt lên trigger → +1; cắt xuống → −1", 30),
    _c("Ultimate Oscillator", "A3 Dao động", "D", "100·(4·A7 + 2·A14 + A28)/7 với A = ΣBP/ΣTR", {"fast": 7, "mid": 14, "slow": 28},
       "UO cắt lên 50 → +1; cắt xuống → −1", 29, notes=["[A] ngưỡng 50"]),
    _c("Williams %R", "A3 Dao động", "D", "−100·(HH − C)/(HH − LL)", {"length": 14}, "%R cắt lên −50 → +1; cắt xuống → −1", 14,
       notes=["[A] ngưỡng −50"]),
    _c("SMI Ergodic", "A3 Dao động", "D", "TSI(5,20) và signal EMA 5", {"short": 5, "long": 20, "signal": 5}, SIG, 125),
    _c("Relative Vigor Index", "A3 Dao động", "D", "SMA(Σ trọng số (C−O))/SMA(Σ trọng số (H−L)), signal trọng số 1-2-2-1", {"length": 10}, SIG, 16),
    _c("True Strength Index", "A3 Dao động", "D", "100·EMA(EMA(Δ,25),13)/EMA(EMA(|Δ|,25),13), signal EMA 13", {"long": 25, "short": 13, "signal": 13}, SIG, 255),
    _c("Coppock Curve", "A3 Dao động", "D", "WMA(ROC14 + ROC11, 10)", {"wma": 10, "long": 14, "short": 11}, ZERO, 24),
    _c("Rate of Change", "A3 Dao động", "D", "100·(close/close₋ₙ − 1)", {"length": 9}, ZERO, 9),
    _c("Klinger Oscillator", "A3 Dao động", "D", "EMA34(VF) − EMA55(VF), VF = ±volume theo hướng hlc3, signal EMA 13", {"fast": 34, "slow": 55, "signal": 13}, SIG, 300),
    # ---------------- A4. Biến động
    _c("Bollinger Bands", "A4 Biến động", "D", "SMA 20 ± 2·stdev (stdev quần thể)", {"length": 20, "mult": 2.0},
       "close cắt lên dải trên → +1; cắt xuống dải dưới → −1 (breakout)", 20),
    _c("BB %B", "A4 Biến động", "D", "%B = (close − dải dưới)/(dải trên − dải dưới)", {"length": 20, "mult": 2.0},
       "%B cắt lên 0,5 → +1; cắt xuống → −1", 20, notes=["[A] dùng ngưỡng 0,5 để không trùng Bollinger Bands"]),
    _c("Standard Error Bands", "A4 Biến động", "D", "linreg 21 ± 2·sai số chuẩn, làm mượt SMA 3", {"length": 21, "mult": 2.0, "smooth": 3},
       "close cắt lên dải trên → +1; cắt xuống dải dưới → −1", 24),
    _c("Envelopes", "A4 Biến động", "D", "SMA 20 ± 10%", {"length": 20, "percent": 10.0},
       "close cắt lên dải trên → +1; cắt xuống dải dưới → −1", 20,
       notes=["tham số mặc định TradingView 10%: trên M1 gần như không có tín hiệu — giữ đúng spec, không tự đổi"]),
    _c("BB Width", "A4 Biến động", "F", "(dải trên − dải dưới)/SMA 20", {"length": 20, "mult": 2.0}, FILTER_RULE, 1460),
    _c("ATR", "A4 Biến động", "F", "RMA(true range, 14) / close", {"length": 14}, FILTER_RULE, 1510,
       notes=["chia cho close để so sánh giữa các mức giá (không đổi thứ tự trong 1 ngày)"]),
    _c("Historical Volatility", "A4 Biến động", "F", "stdev(log return, 10)·√(365·1440)", {"length": 10}, FILTER_RULE, 1450),
    _c("Chaikin Volatility", "A4 Biến động", "F", "100·(EMA(H−L,10)/EMA(H−L,10)₋₁₀ − 1)", {"length": 10, "roc": 10}, FILTER_RULE, 1500),
    _c("Close-to-Close Volatility", "A4 Biến động", "F", "stdev(log return, 10) (có trừ trung bình)", {"length": 10}, FILTER_RULE, 1450),
    _c("Non-Directional Close-to-Close Volatility", "A4 Biến động", "F", "√(mean(log return², 10)) (không trừ trung bình)", {"length": 10}, FILTER_RULE, 1450),
    _c("O-H-L-C Volatility", "A4 Biến động", "F", "Garman–Klass: √mean(0,5·ln(H/L)² − (2ln2 − 1)·ln(C/O)², 10)", {"length": 10}, FILTER_RULE, 1450,
       notes=["[A] dùng ước lượng Garman–Klass"]),
    _c("Relative Volatility Index", "A4 Biến động", "F", "RSI dùng stdev 10 thay cho thay đổi giá, làm mượt 14", {"stdev": 10, "smooth": 14}, FILTER_RULE, 1590),
    _c("Standard Deviation", "A4 Biến động", "F", "stdev(close, 20)/close", {"length": 20}, FILTER_RULE, 1460),
    _c("Volatility Region", "A4 Biến động", "F", "—", {}, "—", 0,
       not_implementable="không tìm được định nghĩa chuẩn (không phải chỉ báo built-in có công thức công bố); không tự thay bằng chỉ báo khác"),
    _c("Mass Index", "A4 Biến động", "F", "Σ₂₅ EMA9(H−L)/EMA9(EMA9(H−L))", {"ema": 9, "sum": 25}, FILTER_RULE, 1530),
    # ---------------- A5. Khối lượng
    _c("Net Volume", "A5 Khối lượng", "D", "volume·sign(Δclose), cộng dồn 14 nến", {"length": 14}, ZERO, 14,
       notes=["[A] tổng 14 nến để thành tín hiệu"]),
    _c("OBV", "A5 Khối lượng", "D", "OBV cộng dồn volume·sign(Δclose)", {"signal": 20}, "OBV cắt lên EMA20(OBV) → +1; cắt xuống → −1", 100,
       notes=["[A] dùng EMA 20 của OBV làm đường tín hiệu"]),
    _c("Accumulation/Distribution", "A5 Khối lượng", "D", "Σ volume·((C−L)−(H−C))/(H−L)", {"signal": 20},
       "AD cắt lên EMA20(AD) → +1; cắt xuống → −1", 100, notes=["[A] dùng EMA 20 làm đường tín hiệu"]),
    _c("MFI", "A5 Khối lượng", "D", "Money Flow Index 14 (hlc3·volume)", {"length": 14}, "MFI cắt lên 50 → +1; cắt xuống → −1", 15,
       notes=["[A] ngưỡng 50"]),
    _c("Chaikin Money Flow", "A5 Khối lượng", "D", "Σ MFV / Σ volume, 20 nến", {"length": 20}, ZERO, 20),
    _c("Chaikin Oscillator", "A5 Khối lượng", "D", "EMA3(AD) − EMA10(AD)", {"fast": 3, "slow": 10}, ZERO, 50),
    _c("Ease of Movement", "A5 Khối lượng", "D", "SMA14(10000·Δhl2·(H−L)/volume)", {"length": 14, "divisor": 10000}, ZERO, 15),
    _c("Elder Force Index", "A5 Khối lượng", "D", "EMA13(Δclose·volume)", {"length": 13}, ZERO, 65),
    _c("Price & Volume Trend", "A5 Khối lượng", "D", "Σ volume·Δclose/close₋₁", {"signal": 20}, "PVT cắt lên EMA20(PVT) → +1; cắt xuống → −1", 100,
       notes=["[A] dùng EMA 20 làm đường tín hiệu"]),
    _c("Volume", "A5 Khối lượng", "F", "volume nến", {}, FILTER_RULE, 1440),
    _c("Volume Oscillator", "A5 Khối lượng", "F", "100·(EMA5(vol) − EMA10(vol))/EMA10(vol)", {"fast": 5, "slow": 10}, "bật khi > 0", 50),
    _c("Volume Profile Fixed Range", "A5 Khối lượng", "F", "vùng giá trị 70% (VAH/VAL) theo volume của NGÀY UTC TRƯỚC, 100 mức giá",
       {"value_area": 0.7, "bins": 100}, "bật khi close nằm ngoài vùng giá trị của ngày trước", 1440,
       lag="dùng hồ sơ volume của ngày đã kết thúc", repaint="không",
       notes=["[A] 'Fixed Range' cần chọn vùng bằng tay; dùng ngày UTC trước làm vùng cố định"]),
    # ---------------- A6. Khác
    _c("VWAP", "A6 Khác", "D", "Σ(hlc3·vol)/Σvol, reset 00:00 UTC", {"anchor": "1D"}, CROSS, 1),
    _c("VWMA", "A6 Khác", "D", "Σ(close·vol)/Σvol, 20 nến", {"length": 20}, CROSS, 20),
    _c("Pivot Points Standard", "A6 Khác", "D", "P = (H+L+C)/3 của ngày UTC trước", {"anchor": "1D"}, "close cắt lên P → +1; cắt xuống → −1", 1440,
       lag="dùng ngày đã kết thúc", notes=["[A] chỉ dùng mức P (không dùng R/S)"]),
    _c("Balance of Power", "A6 Khác", "D", "SMA14((C−O)/(H−L))", {"length": 14}, ZERO, 14, notes=["[A] làm mượt SMA 14"]),
    _c("Accumulative Swing Index", "A6 Khác", "D", "Σ Swing Index Wilder, limit move T = 10000", {"limit": 10000.0, "signal": 20},
       "ASI cắt lên SMA20(ASI) → +1; cắt xuống → −1", 25,
       notes=["[A] crypto không có giới hạn biên độ ngày; dùng T = 10000 như mặc định TradingView", "[A] SMA 20 làm đường tín hiệu"]),
    _c("Up/Down", "A6 Khác", "D", "chênh lệch volume mua chủ động − bán chủ động (taker buy − taker sell), cộng 14 nến", {"length": 14}, ZERO, 14,
       source="Binance taker_buy_volume (thay cho Up/Down Volume cần dữ liệu khung nhỏ hơn)",
       notes=["[A] Up/Down Volume của TradingView cần nến khung nhỏ hơn M1; thay bằng taker buy/sell của Binance — ghi rõ khác định nghĩa"]),
    _c("Spread", "A6 Khác", "F", "spread = log(close) − log(close cặp tham chiếu); z = (spread − SMA20)/stdev20", {"length": 20},
       "bật khi |z| > 1", 20, notes=["cặp tham chiếu BTCUSDT (với BTCUSDT dùng ETHUSDT)", "[A] dùng log để không phụ thuộc mức giá; ngưỡng |z| > 1"]),
    _c("Correlation Coefficient", "A6 Khác", "F", "tương quan Pearson close với close cặp tham chiếu, 20 nến", {"length": 20}, FILTER_RULE, 1460,
       notes=["cặp tham chiếu BTCUSDT (với BTCUSDT dùng ETHUSDT)"]),
    _c("Correlation-Log", "A6 Khác", "F", "tương quan Pearson của log return với cặp tham chiếu, 20 nến", {"length": 20}, FILTER_RULE, 1461,
       notes=["cặp tham chiếu BTCUSDT (với BTCUSDT dùng ETHUSDT)"]),
    _c("Rank Correlation", "A6 Khác", "F", "tương quan hạng Spearman close với cặp tham chiếu, 20 nến", {"length": 20}, FILTER_RULE, 1460,
       notes=["cặp tham chiếu BTCUSDT (với BTCUSDT dùng ETHUSDT)"]),
    _c("Ratio", "A6 Khác", "F", "ratio = close / close cặp tham chiếu; z = (ratio − SMA20)/stdev20", {"length": 20}, "bật khi |z| > 1", 20,
       notes=["cặp tham chiếu BTCUSDT (với BTCUSDT dùng ETHUSDT)", "[A] ngưỡng |z| > 1"]),
    _c("Standard Error", "A6 Khác", "F", "sai số chuẩn của hồi quy tuyến tính close 20 nến / close", {"length": 20}, FILTER_RULE, 1460),
    _c("Sure Thing", "A6 Khác", "D", "—", {}, "—", 0,
       not_implementable="không tìm được công thức chuẩn công bố cho 'Sure Thing'; không tự thay bằng chỉ báo khác"),
    _c("Average Price", "A6 Khác", "D", "ohlc4 so với SMA20(ohlc4)", {"length": 20}, "ohlc4 cắt lên SMA20 của chính nó → +1; cắt xuống → −1", 20,
       notes=["dùng như giá so với MA của chính nó (spec §A6)"]),
    _c("Typical Price", "A6 Khác", "D", "hlc3 so với SMA20(hlc3)", {"length": 20}, "hlc3 cắt lên SMA20 của chính nó → +1; cắt xuống → −1", 20,
       notes=["dùng như giá so với MA của chính nó (spec §A6)"]),
    _c("Median Price", "A6 Khác", "D", "hl2 so với SMA20(hl2)", {"length": 20}, "hl2 cắt lên SMA20 của chính nó → +1; cắt xuống → −1", 20,
       notes=["dùng như giá so với MA của chính nó (spec §A6)"]),
]

BY_NAME = {c.name: c for c in CARDS}
assert len(BY_NAME) == len(CARDS), "trùng tên chỉ báo"


def status(card: Card) -> str:
    if card.not_implementable:
        return "không triển khai"
    from kh.ind.indicators import impl

    return "đã triển khai" if card.name in getattr(impl, "IMPL", {}) else "chưa triển khai"


def crosscheck_results() -> dict:
    import json

    from kh.config import REPO_ROOT

    p = REPO_ROOT / "reports" / "ind" / "indicator_crosscheck.json"
    return json.loads(p.read_text())["results"] if p.exists() else {}


def cards_markdown() -> str:
    xc = crosscheck_results()
    L = ["# Phiếu chỉ báo (sinh tự động từ `src/kh/ind/indicators/registry.py`)", "",
         f"Tổng số: **{len(CARDS)}** chỉ báo = số tên ở Phụ lục A của `docs/ind/spec.md`.",
         "Quy ước: (D) directional → sự kiện +1/−1 tại nến điều kiện vừa đúng; (F) filter → trạng thái bật/tắt, không cho hướng.",
         f"Quy tắc filter mặc định: {FILTER_RULE}.",
         "Đối chiếu thư viện độc lập: `tools/ind_crosscheck.py` → `reports/ind/indicator_crosscheck.json` (BTCUSDT M1 thật, ngưỡng 1e-4).", "",
         "| # | Chỉ báo | Nhóm | Loại | Trạng thái | Tham số | Quy tắc |", "|---|---|---|---|---|---|---|"]
    for i, c in enumerate(CARDS, 1):
        L.append(f"| {i} | {c.name} | {c.group} | {c.kind} | {status(c)} | `{c.params}` | {c.rule} |")
    L.append("")
    for i, c in enumerate(CARDS, 1):
        L += [f"## {i}. {c.name}", "",
              f"- Nhóm: {c.group} · Loại: {'directional' if c.kind == 'D' else 'filter'} · Trạng thái: **{status(c)}**"
              + (f" — lý do: {c.not_implementable}" if c.not_implementable else ""),
              f"- Công thức: {c.formula}", f"- Nguồn công thức: {c.source}", f"- Tham số mặc định: `{c.params}`",
              f"- Quy tắc tín hiệu: {c.rule}", f"- Số nến khởi động: {c.warmup}", f"- Độ trễ: {c.lag}",
              f"- Rủi ro repaint: {c.repaint}", f"- Tương đương TradingView: {c.tv_note}"]
        for r in xc.get(c.name, []):
            L.append(f"- Đối chiếu thư viện độc lập ({r['library']}): sai số tương đối tối đa {r['max_rel_error']:.2e} sau 2.000 nến khởi động"
                     f" → **{'khớp' if r['pass'] else 'không khớp'}**" + (f" — {r['note']}" if r["note"] else ""))
        L += [f"- Ghi chú: {n}" for n in c.notes]
        L.append("")
    return "\n".join(L)
