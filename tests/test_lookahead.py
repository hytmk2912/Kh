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


# ---------------------------------------------------------------- track ind (I2): mọi chỉ báo
from kh.ind.htf import htf_permissions  # noqa: E402
from kh.ind.indicators.impl import IMPL, Ctx, compute  # noqa: E402

N_IND = 3200


@pytest.fixture(scope="module")
def ind_data():
    k = synth_klines(N_IND, seed=11, filler_at=(1800, 1810))
    rng = np.random.default_rng(5)
    ref = k.close.to_numpy() * 0.5 + np.cumsum(rng.normal(0, 0.02, len(k)))
    k["open_time_ms"] = k.open_time_ms - (k.open_time_ms.iloc[0] % 86_400_000)  # bắt đầu đúng 00:00 UTC
    return k, ref


@pytest.mark.parametrize("name", sorted(IMPL))
def test_indicator_no_lookahead(name, ind_data):
    """20 thời điểm ngẫu nhiên: giá trị + tín hiệu tại t tính trên data[:t+1] phải bằng khi tính trên toàn bộ."""
    k, ref = ind_data
    full_out, full_sig = compute(name, Ctx.from_frame(k, ref))
    rng = np.random.default_rng(abs(hash(name)) % 2**32)
    for t in sorted(rng.choice(np.arange(1500, N_IND), 20, replace=False)):
        out, sig = compute(name, Ctx.from_frame(k.iloc[: t + 1], ref[: t + 1]))
        assert sig[t] == full_sig[t], f"{name}: tín hiệu khác tại t={t}"
        for key in full_out:
            a, b = out[key][t], full_out[key][t]
            assert np.isclose(a, b, rtol=1e-5, atol=1e-6, equal_nan=True), f"{name}.{key}: {a} ≠ {b} tại t={t}"


def test_htf_filter_no_lookahead(ind_data):
    k, _ = ind_data
    t, c = k.open_time_ms.to_numpy(), k.close.to_numpy()
    L, S = htf_permissions(t, c)
    for i in np.random.default_rng(0).choice(np.arange(200, N_IND), 30, replace=False):
        l2, s2 = htf_permissions(t[: i + 1], c[: i + 1])
        assert l2[i] == L[i] and s2[i] == S[i]
