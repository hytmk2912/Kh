"""Đối chiếu chỉ báo tự cài với thư viện độc lập (việc I2).

- TA-Lib (cài cùng môi trường): EMA, RSI, MACD, ATR, Bollinger, Stochastic, ADX/DI, OBV + nhiều chỉ báo khác.
- pandas-ta + talipp (chạy trong môi trường Python RIÊNG vì kéo numpy khác): SuperTrend, VWAP, Parabolic SAR.
  Lưu ý: SuperTrend của pandas-ta dùng thuật toán khác TradingView (so close với dải nến trước, không reset dải theo
  close nến trước); talipp chép đúng quy tắc dải cuối như TradingView → dùng talipp làm đối chiếu chính.

Dữ liệu: BTCUSDT M1 thật, 30.000 nến đầu; bỏ 2.000 nến khởi động. Sai số = max|a − b| / TB|b| (tương đối
theo độ lớn chuỗi tham chiếu). Kết quả: reports/ind/indicator_crosscheck.json (phiếu chỉ báo đọc file này).

Chạy:  python tools/ind_crosscheck.py --pandas-ta-python /đường/dẫn/python-có-pandas-ta
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from kh.config import get_paths, write_json
from kh.ind.data import load_m1
from kh.ind.indicators import core as K
from kh.ind.indicators import impl as I

N, SKIP = 30_000, 2_000

PANDAS_TA_SCRIPT = r"""
import sys, pandas as pd, pandas_ta as ta
df = pd.read_parquet(sys.argv[1])
idx = pd.to_datetime(df.open_time_ms, unit="ms", utc=True)
df.index = idx
st = ta.supertrend(df.high, df.low, df.close, length=10, multiplier=3.0)
vw = ta.vwap(df.high, df.low, df.close, df.volume, anchor="D")
out = pd.DataFrame({"st_line": st.iloc[:, 0].to_numpy(), "st_dir": st.iloc[:, 1].to_numpy(), "vwap": vw.to_numpy()})
from talipp.indicators import SuperTrend, ParabolicSAR
from talipp.indicators.SuperTrend import Trend
from talipp.ohlcv import OHLCV
bars = [OHLCV(o, h, l, c, v) for o, h, l, c, v in zip(df.open, df.high, df.low, df.close, df.volume)]
stt = SuperTrend(10, 3, input_values=bars)
out["tp_st_line"] = [x.value if x is not None else float("nan") for x in stt]
out["tp_st_dir"] = [(1 if x.trend == Trend.UP else -1) if x is not None else 0 for x in stt]
sar = ParabolicSAR(0.02, 0.02, 0.2, input_values=bars)
out["tp_sar"] = [x.value if x is not None else float("nan") for x in sar]
out.to_parquet(sys.argv[2], index=False)
"""


def err(a, b) -> float:
    a, b = np.asarray(a, np.float64)[SKIP:], np.asarray(b, np.float64)[SKIP:]
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 100:
        return float("nan")
    return float(np.max(np.abs(a[ok] - b[ok])) / (np.mean(np.abs(b[ok])) + 1e-12))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pandas-ta-python", default=None)
    a = ap.parse_args()
    import talib

    P = get_paths()
    m1 = load_m1(P, "BTCUSDT").iloc[:N].reset_index(drop=True)
    X = I.Ctx.from_frame(m1, m1.close.to_numpy())
    h, l, c, v = X.h, X.l, X.c, X.v
    res = {}

    def mine(name, key):
        return I.IMPL[name](X)[0][key]

    def add(name, lib, e, note=""):
        res.setdefault(name, []).append({"library": lib, "max_rel_error": e, "pass": bool(np.isfinite(e) and e < 1e-4), "note": note})

    T = f"TA-Lib {talib.__version__}"
    add("EMA", T, err(mine("EMA", "line"), talib.EMA(c, 9)), "EMA 9")
    add("SMA", T, err(mine("SMA", "line"), talib.SMA(c, 9)), "SMA 9")
    add("WMA", T, err(mine("WMA", "line"), talib.WMA(c, 9)), "WMA 9")
    add("DEMA", T, err(mine("DEMA", "line"), talib.DEMA(c, 9)), "DEMA 9")
    add("TEMA", T, err(mine("TEMA", "line"), talib.TEMA(c, 9)), "TEMA 9")
    add("RSI", T, err(mine("RSI", "rsi"), talib.RSI(c, 14)), "RSI 14")
    m, s, hi = talib.MACD(c, 12, 26, 9)
    add("MACD", T, max(err(mine("MACD", "macd"), m), err(mine("MACD", "signal"), s)), "MACD + signal 12/26/9")
    add("ATR", T, err(K.atr(h, l, c, 14), talib.ATR(h, l, c, 14)), "ATR 14 (trước khi chia close)")
    up, mid, lo = talib.BBANDS(c, 20, 2, 2, 0)
    o = I.IMPL["Bollinger Bands"](X)[0]
    add("Bollinger Bands", T, max(err(o["upper"], up), err(o["lower"], lo), err(o["basis"], mid)), "20, 2σ")
    sk, sd = talib.STOCH(h, l, c, fastk_period=14, slowk_period=1, slowk_matype=0, slowd_period=3, slowd_matype=0)
    o = I.IMPL["Stochastic"](X)[0]
    add("Stochastic", T, max(err(o["k"], sk), err(o["d"], sd)), "%K 14, smooth 1, %D 3")
    plus, minus, adx = I.dmi(X, 14)
    add("ADX", T, err(adx, talib.ADX(h, l, c, 14)), "ADX 14")
    add("Directional Movement", T, max(err(plus, talib.PLUS_DI(h, l, c, 14)), err(minus, talib.MINUS_DI(h, l, c, 14))), "+DI/−DI 14")
    obv_m, obv_t = mine("OBV", "obv"), talib.OBV(c, v)
    add("OBV", T, err(np.diff(obv_m), np.diff(obv_t)), "so sánh mức thay đổi từng nến (TA-Lib bắt đầu OBV bằng volume nến đầu → lệch hằng số)")
    add("Parabolic SAR", T, err(mine("Parabolic SAR", "sar"), talib.SAR(h, l, 0.02, 0.2)),
        "0,02 / 0,2 (định nghĩa Wilder)")
    ad_, au_ = talib.AROON(h, l, 14)
    o = I.IMPL["Aroon"](X)[0]
    add("Aroon", T, max(err(o["aroon_up"], au_), err(o["aroon_down"], ad_)), "14")
    add("MFI", T, err(mine("MFI", "mfi"), talib.MFI(h, l, c, v, 14)), "14")
    add("Rate of Change", T, err(I.IMPL["Rate of Change"](X)[0]["value"], talib.ROC(c, 9)), "9")
    add("Momentum", T, err(I.IMPL["Momentum"](X)[0]["value"], talib.MOM(c, 10)), "10")
    add("Williams %R", T, err(mine("Williams %R", "wr"), talib.WILLR(h, l, c, 14)), "14")
    add("Ultimate Oscillator", T, err(mine("Ultimate Oscillator", "uo"), talib.ULTOSC(h, l, c, 7, 14, 28)), "7/14/28")
    add("Accumulation/Distribution", T, err(mine("Accumulation/Distribution", "ad"), talib.AD(h, l, c, v)), "")
    add("Chaikin Oscillator", T, err(I.IMPL["Chaikin Oscillator"](X)[0]["value"], talib.ADOSC(h, l, c, v, 3, 10)), "3/10")
    add("Least Squares MA", T, err(mine("Least Squares MA", "line"), talib.LINEARREG(c, 25)), "linreg 25")
    add("Linear Regression Slope", T, err(I.IMPL["Linear Regression Slope"](X)[0]["value"], talib.LINEARREG_SLOPE(c, 14)), "14")
    add("Adaptive MA", T, err(mine("Adaptive MA", "line"), talib.KAMA(c, 9)), "KAMA 9 (fast 2, slow 30)")
    add("Chande Momentum Oscillator", T, err(I.IMPL["Chande Momentum Oscillator"](X)[0]["value"], talib.CMO(c, 9)),
        "TA-Lib CMO làm mượt kiểu Wilder, TradingView dùng tổng đơn giản → dự kiến KHÁC định nghĩa")

    if a.pandas_ta_python:
        with tempfile.TemporaryDirectory() as d:
            src, dst, scr = Path(d) / "in.parquet", Path(d) / "out.parquet", Path(d) / "pt.py"
            m1[["open_time_ms", "open", "high", "low", "close", "volume"]].to_parquet(src, index=False)
            scr.write_text(PANDAS_TA_SCRIPT)
            r = subprocess.run([a.pandas_ta_python, "-I", str(scr), str(src), str(dst)], capture_output=True, text=True)
            if r.returncode:
                print(r.stderr[-2000:], file=sys.stderr)
            else:
                ref = pd.read_parquet(dst)
                ver = subprocess.run([a.pandas_ta_python, "-I", "-c", "import pandas_ta;print(pandas_ta.version)"],
                                     capture_output=True, text=True).stdout.strip()
                tver = subprocess.run([a.pandas_ta_python, "-I", "-c",
                                       "import importlib.metadata as m;print(m.version('talipp'))"], capture_output=True, text=True).stdout.strip()
                o = I.IMPL["SuperTrend"](X)[0]
                agree = float(np.mean((o["direction"][SKIP:] == ref.tp_st_dir.to_numpy()[SKIP:])))
                add("SuperTrend", f"talipp {tver}", err(o["line"], ref.tp_st_line), f"ATR 10, factor 3; hướng trùng {agree:.6f} số nến")
                agree_pt = float(np.mean((o["direction"][SKIP:] == ref.st_dir.to_numpy()[SKIP:])))
                add("SuperTrend", f"pandas-ta {ver}", err(o["line"], ref.st_line),
                    f"thuật toán pandas-ta khác TradingView (xem docstring); hướng trùng {agree_pt:.6f} số nến — chỉ để tham khảo")
                add("Parabolic SAR", f"talipp {tver}", err(mine("Parabolic SAR", "sar"), ref.tp_sar),
                    "talipp khác TA-Lib ở nến đảo chiều; đối chiếu chính là TA-Lib — chỉ để tham khảo")
                add("VWAP", f"pandas-ta {ver}", err(mine("VWAP", "line"), ref.vwap), "neo theo ngày UTC, hlc3")
    out = {"data": f"BTCUSDT M1, {N} nến đầu cửa sổ, bỏ {SKIP} nến khởi động", "metric": "max|a−b| / TB|b|, đạt nếu < 1e-4",
           "results": res}
    write_json(out, P.reports / "ind" / "indicator_crosscheck.json")
    for k, v in res.items():
        for x in v:
            print(f"{k:<28} {x['library']:<18} {x['max_rel_error']:.2e} {'ĐẠT' if x['pass'] else 'KHÔNG'}  {x['note']}")


if __name__ == "__main__":
    main()
