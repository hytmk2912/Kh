import numpy as np
import pandas as pd

from conftest import T0
from kh.ind.labels import bar_labels
from kh.ind.score import WaveBook


def _bars(path):
    c = np.asarray(path, float)
    o = np.concatenate([[c[0]], c[:-1]])
    n = len(c)
    return pd.DataFrame({"open_time_ms": T0 + np.arange(n) * 60_000, "open": o, "high": np.maximum(o, c),
                         "low": np.minimum(o, c), "close": c, "volume": np.ones(n), "is_filler": np.zeros(n, bool)})


def test_wavebook_precision_recall_known_case():
    # tăng 100 → 102 (40′), giảm 102 → 100 (40′), tăng 100 → 101 (20′), giảm nhẹ để xác nhận
    path = np.concatenate([np.linspace(100, 102, 41), np.linspace(102, 100, 41)[1:], np.linspace(100, 101, 21)[1:],
                           np.linspace(101, 100.4, 13)[1:]])
    m = _bars(path)
    lab, W = bar_labels(m, 0.005)
    book = WaveBook(m, lab, W, 0, len(m))
    sig = np.zeros(len(m), np.int8)
    sig[2] = 1      # đầu sóng tăng 1: đúng
    sig[38] = 1     # cuối sóng tăng 1: còn < 0,3% → sai ("muộn")
    sig[45] = 1     # trong sóng giảm: sai ("ngược sóng")
    sig[44] = -1    # đầu sóng giảm: đúng
    r = book.score(sig, np.random.default_rng(0), n_random=5)
    assert r["n_long"] == 3 and r["n_short"] == 1
    assert np.isclose(r["precision_long"], 1 / 3) and r["precision_short"] == 1.0
    assert np.isclose(r["false_late_share"] + r["false_counter_wave_share"], 1.0)
    assert (W.direction == 1).sum() == 2 and W.fast.all()
    assert r["recall_fast_up"] == 0.5 and r["recall_fast_down"] == 1.0  # bắt 1/2 sóng tăng, 1/1 sóng giảm
    assert np.isnan(r["recall_slow"])  # không có sóng chậm
    assert r["latency_min_median"] >= 0
