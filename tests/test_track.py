"""Việc N0 (track M15): tham số hoá khung thời gian không đổi kết quả M1; H4; HTF trên nến M15."""
import numpy as np

from conftest import synth_klines
from kh.ind.data import resample
from kh.ind.htf import htf_permissions
from kh.ind.indicators import core as K
from kh.ind.indicators.impl import timeframe
from kh.ind.indicators.registry import BY_NAME
from kh.ind.track import M1, M15


def test_track_defaults_match_m1_spec():
    assert (M1.tf, M1.wave_pct, M1.fast_bars, M1.flat_bars, M1.unknown_after_filler) == (1, 0.005, 15, 30, 30)
    assert (M1.tp, M1.sl, M1.max_hold_bars, M1.min_remaining, M1.bars_per_day) == (0.0045, 0.0030, 15, 0.003, 1440)
    assert M1.param_overrides == {} and M1.htf == (15, 60)
    # spec M15 §1–§3
    assert (M15.tf, M15.htf, M15.wave_pct, M15.fast_bars, M15.flat_bars) == (15, (60, 240), 0.015, 32, 32)
    assert (M15.tp, M15.sl, M15.max_hold_bars, M15.min_remaining, M15.pullback_pct, M15.bars_per_day) == (0.012, 0.008, 32, 0.009, 0.006, 96)
    assert M15.unknown_after_filler == 2


def test_resample_h4_counts_and_filler():
    k = synth_klines(240 * 6, seed=3, filler_at=(500, 505))
    h4 = resample(k, 240)
    assert len(h4) == 6 and (h4.n_m1 == 240).all()
    assert h4.n_filler.tolist() == [0, 0, 5, 0, 0, 0]
    assert (h4.available_at_ms - h4.open_time_ms == 240 * 60_000).all()


def test_timeframe_context_overrides_and_restores():
    old_len, old_dev = BY_NAME["52-Week High/Low"].params["length"], BY_NAME["Zig Zag"].params["deviation"]
    with timeframe(M15):
        assert K.BARS_PER_DAY == 96
        assert BY_NAME["52-Week High/Low"].params["length"] == 96
        assert BY_NAME["Zig Zag"].params["deviation"] == 0.015
    assert K.BARS_PER_DAY == 1440
    assert BY_NAME["52-Week High/Low"].params["length"] == old_len == 1440
    assert BY_NAME["Zig Zag"].params["deviation"] == old_dev == 0.005
    with timeframe(M1):
        assert K.BARS_PER_DAY == 1440 and BY_NAME["52-Week High/Low"].params["length"] == 1440


def test_htf_on_m15_bars_equals_m1_version_at_bar_close():
    """Hướng H1/H4 tính trên nến M15 (base 15) phải bằng bản tính trên M1 tại phút cuối của mỗi nến M15."""
    k = synth_klines(240 * 80, seed=4)
    k["open_time_ms"] = k.open_time_ms - (k.open_time_ms.iloc[0] % (240 * 60_000))  # bắt đầu đúng mốc 4 giờ
    m15 = resample(k, 15)
    L1, S1 = htf_permissions(k.open_time_ms.to_numpy(), k.close.to_numpy(), (60, 240), 1)
    L15, S15 = htf_permissions(m15.open_time_ms.to_numpy(), m15.close.to_numpy(), (60, 240), 15)
    last_min = np.arange(14, len(k), 15)
    assert np.array_equal(L15, L1[last_min]) and np.array_equal(S15, S1[last_min])
    assert L15.mean() < 1 and S15.mean() < 1  # bộ lọc có tác dụng


def test_htf_m15_no_lookahead():
    k = synth_klines(240 * 60, seed=6)
    m15 = resample(k, 15)
    t, c = m15.open_time_ms.to_numpy(), m15.close.to_numpy()
    L, S = htf_permissions(t, c, (60, 240), 15)
    for i in np.random.default_rng(1).choice(np.arange(300, len(t)), 30, replace=False):
        l2, s2 = htf_permissions(t[: i + 1], c[: i + 1], (60, 240), 15)
        assert l2[i] == L[i] and s2[i] == S[i]
