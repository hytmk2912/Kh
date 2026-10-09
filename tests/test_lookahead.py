"""Test cắt cụt: đặc trưng tại t tính trên dữ liệu đầy đủ phải bằng đặc trưng tính trên dữ liệu
chỉ gồm những gì đã có lúc nến t đóng cửa. Nếu một đặc trưng dùng tương lai, test sẽ thất bại."""
import numpy as np
import pandas as pd
import pytest

from conftest import synth_funding, synth_klines, synth_metrics
from kh.config import MS_PER_MIN
from kh.features.build import compute_features


@pytest.fixture(scope="module")
def data():
    k = synth_klines(4000, seed=7, filler_at=(2500, 2520))
    return k, synth_metrics(k), synth_funding(k), k.close * 0.9 + 1


def test_no_lookahead(cfg, data):
    k, m, f, btc = data
    full = compute_features(k, cfg, m, f, btc)
    for t in (1500, 2510, 3000, 3999):
        close_ms = k.open_time_ms.iloc[t] + MS_PER_MIN
        kt = k.iloc[: t + 1]
        mt = m[m.available_ms <= close_ms]
        ft = f[f.funding_time_ms <= close_ms]
        part = compute_features(kt, cfg, mt, ft, btc.iloc[: t + 1])
        a, b = full.iloc[t], part.iloc[t]
        bad = [c for c in full.columns if not np.isclose(a[c], b[c], equal_nan=True, rtol=1e-4, atol=1e-6)]
        assert not bad, f"Đặc trưng dùng dữ liệu tương lai tại t={t}: {bad}"


def test_future_shock_does_not_change_past(cfg, data):
    """Thay đổi mạnh dữ liệu sau t không được làm thay đổi đặc trưng tại t."""
    k, m, f, btc = data
    base = compute_features(k, cfg, m, f, btc)
    k2 = k.copy()
    k2.loc[3001:, ["open", "high", "low", "close"]] *= 1.5
    k2.loc[3001:, "volume"] *= 10
    shocked = compute_features(k2, cfg, m, f, btc)
    pd.testing.assert_frame_equal(base.iloc[:3001], shocked.iloc[:3001])


def test_features_finite_or_nan(cfg, data):
    k, m, f, btc = data
    F = compute_features(k, cfg, m, f, btc)
    assert not np.isinf(F.to_numpy()).any()
