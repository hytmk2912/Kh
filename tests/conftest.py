import numpy as np
import pandas as pd
import pytest

from kh.config import load_config

T0 = 1_735_689_600_000  # 2025-01-01 00:00 UTC (ms)


def synth_klines(n: int = 6000, seed: int = 0, filler_at: tuple[int, int] | None = None) -> pd.DataFrame:
    """Nến 1m tổng hợp: bước ngẫu nhiên + biến động thay đổi, đúng logic OHLC."""
    rng = np.random.default_rng(seed)
    vol = 0.001 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    r = rng.normal(0, 1, n) * vol
    close = 100 * np.exp(np.cumsum(r))
    open_ = np.concatenate([[100.0], close[:-1]])
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.0005, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.0005, n)))
    volume = rng.gamma(2, 50, n)
    df = pd.DataFrame({
        "symbol": "TEST", "open_time_ms": T0 + np.arange(n, dtype=np.int64) * 60_000,
        "open": open_, "high": high, "low": low, "close": close, "volume": volume,
        "close_time_ms": T0 + np.arange(n, dtype=np.int64) * 60_000 + 59_999,
        "quote_volume": volume * close, "trade_count": rng.integers(1, 100, n),
        "taker_buy_base_volume": volume * rng.uniform(0.2, 0.8, n),
        "taker_buy_quote_volume": volume * close * 0.5,
    })
    if filler_at:
        a, b = filler_at
        p = df.close.iloc[a - 1]
        df.loc[a:b - 1, ["open", "high", "low", "close"]] = p
        df.loc[a:b - 1, ["volume", "quote_volume", "taker_buy_base_volume", "taker_buy_quote_volume"]] = 0.0
        df.loc[a:b - 1, "trade_count"] = 0
    df["is_filler"] = (df.volume == 0) & (df.open == df.high) & (df.high == df.low) & (df.low == df.close)
    return df


def synth_metrics(k: pd.DataFrame, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = np.arange(k.open_time_ms.iloc[0], k.open_time_ms.iloc[-1], 300_000)
    m = pd.DataFrame({"create_time_ms": t, "available_ms": t + 300_000,
                      "sum_open_interest": 1e4 * np.exp(np.cumsum(rng.normal(0, 0.002, len(t)))),
                      "sum_open_interest_value": 1e6, "count_toptrader_long_short_ratio": rng.uniform(0.8, 1.5, len(t)),
                      "sum_toptrader_long_short_ratio": rng.uniform(0.8, 1.5, len(t)),
                      "count_long_short_ratio": rng.uniform(0.8, 1.5, len(t)),
                      "sum_taker_long_short_vol_ratio": rng.uniform(0.5, 2, len(t))})
    m["symbol"] = "TEST"
    return m


def synth_funding(k: pd.DataFrame, seed: int = 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = np.arange(k.open_time_ms.iloc[0], k.open_time_ms.iloc[-1], 8 * 3_600_000)
    return pd.DataFrame({"symbol": "TEST", "funding_time_ms": t, "calc_time_ms": t + 5,
                         "funding_interval_hours": 8, "funding_rate": rng.normal(1e-4, 1e-4, len(t))})


@pytest.fixture(scope="session")
def cfg():
    c = load_config()
    c["waves"]["sigma_halflife_min"] = 240  # khởi động nhanh hơn cho dữ liệu tổng hợp
    return c
