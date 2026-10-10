import numpy as np
import pandas as pd

from conftest import T0, synth_klines
from kh.labels.triple_barrier import _barrier, breakeven_prob
from kh.waves.dc import run_dc, waves_table


def _bars(closes):
    c = np.asarray(closes, float)
    o = np.concatenate([[c[0]], c[:-1]])
    return pd.DataFrame({"open_time_ms": T0 + np.arange(len(c)) * 60_000, "open": o,
                         "high": np.maximum(o, c), "low": np.minimum(o, c), "close": c,
                         "volume": np.ones(len(c))})


def test_dc_pivots_and_confirmation_are_causal():
    # 100 → 110 → 104 → 112 → 100, theta 5%
    path = list(np.linspace(100, 110, 11)) + list(np.linspace(110, 104, 7))[1:] + \
        list(np.linspace(104, 112, 9))[1:] + list(np.linspace(112, 100, 13))[1:]
    df = _bars(path)
    dc = run_dc(df, np.full(len(df), 0.05))
    # Đáy 100 xác nhận khi giá ≥ 105; đỉnh 110 xác nhận khi giá ≤ 104,5; đáy 104 xác nhận khi giá ≥ 109,2
    types = list(dc["piv_type"])
    assert types[0] == -1 and types[1] == 1
    assert np.all(dc["piv_conf"] > dc["piv_idx"]), "xác nhận phải xảy ra SAU cực trị"
    # Trạng thái tại nến i chỉ phụ thuộc dữ liệu đến i: chạy trên dữ liệu cắt cụt cho kết quả giống
    for t in (12, 20, 30):
        dct = run_dc(df.iloc[: t + 1], np.full(t + 1, 0.05))
        assert dct["st_mode"][t] == dc["st_mode"][t]
        assert np.isclose(dct["st_ext"][t], dc["st_ext"][t], equal_nan=True)


def test_waves_alternate_and_amplitude_at_least_theta():
    k = synth_klines(5000, seed=3)
    dc = run_dc(k, np.full(len(k), 0.01))
    w = waves_table(k, dc)
    assert (np.diff(w.direction) != 0).all()
    assert (w.amp_log_abs >= np.log(1 / 0.99) - 1e-9).sum() >= 0.95 * len(w)
    assert (w.start_confirm_ms > w.start_ms).all()


def test_barrier_labels_and_ambiguous_bar():
    # Nến 2 chạm cả rào trên và dưới → ambiguous (2)
    o = np.array([100, 100, 100, 100, 100.0])
    h = np.array([100, 100.5, 102, 100, 100.0])
    l = np.array([100, 99.5, 98, 100, 100.0])
    c = np.array([100, 100, 100, 100, 100.0])
    touch, t_hit, fwd, hf = _barrier(o, h, l, c, np.zeros(5, bool), np.full(5, 0.01), 3)
    assert touch[0] == 2 and t_hit[0] == 2
    h2 = h.copy(); h2[2] = 101.5; l2 = l.copy(); l2[2] = 99.5
    touch, t_hit, _, _ = _barrier(o, h2, l2, c, np.zeros(5, bool), np.full(5, 0.01), 3)
    assert touch[0] == 1 and t_hit[0] == 2
    assert touch[-1] == -9  # không đủ dữ liệu tương lai


def test_breakeven_probability():
    assert np.isclose(breakeven_prob(0.01, 0.0014), 0.57)
