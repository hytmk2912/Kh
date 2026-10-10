import numpy as np
import pandas as pd
import pytest

from conftest import T0
from kh.backtest.engine import Costs, run_symbol
from kh.evaluation.metrics import deflated_sharpe, pbo_cscv, perf


def _k(o, h, l, c, filler=None):
    n = len(c)
    return pd.DataFrame({"open_time_ms": T0 + np.arange(n) * 60_000, "open": o, "high": h, "low": l, "close": c,
                         "is_filler": np.zeros(n, bool) if filler is None else filler})


def _sig(i, side, tp=0.01, sl=0.01, hold=5, exit_at=-1):
    return pd.DataFrame({"bar_idx": [i], "side": [side], "tp": [tp], "sl": [sl], "max_hold": [hold],
                         "exit_at": [exit_at], "risk_frac": [sl if sl == sl else 0.01]})


@pytest.fixture
def cfg2(cfg):
    c = dict(cfg)
    c["backtest"] = dict(cfg["backtest"], initial_capital=10_000, risk_per_trade=0.01, max_leverage_per_position=100)
    c["symbols"] = ["X"]
    return c


def test_ambiguous_bar_counts_as_stop(cfg2):
    flat = np.full(6, 100.0)
    h, l = flat.copy(), flat.copy()
    h[2], l[2] = 102, 98  # nến 2 chạm cả TP 101 và SL 99
    T = run_symbol(_k(flat, h, l, flat), None, _sig(0, 1), Costs(0.0, 0.0), cfg2)
    assert T.reason.iloc[0] == -1 and np.isclose(T.exit_px.iloc[0], 99.0)


def test_gap_through_stop_fills_at_open(cfg2):
    o = np.array([100, 100, 100, 97, 97, 97.0])
    c = o.copy()
    T = run_symbol(_k(o, np.maximum(o, c), np.minimum(o, c), c), None, _sig(1, 1), Costs(0.0, 0.0), cfg2)
    assert T.reason.iloc[0] == -1 and np.isclose(T.exit_px.iloc[0], 97.0)  # xấu hơn SL 99


def test_entry_next_open_fees_and_slippage(cfg2):
    o = np.array([100, 101, 101, 101, 101, 101, 101.0])
    T = run_symbol(_k(o, o, o, o), None, _sig(0, 1, hold=3), Costs(0.0005, 0.0002), cfg2)
    t = T.iloc[0]
    assert t.entry_idx == 1 and np.isclose(t.entry_px, 101 * 1.0002)
    assert np.isclose(t.exit_px, 101 * (1 - 0.0002))
    assert np.isclose(t.fees, 0.0005 * t.notional * (1 + t.exit_px / t.entry_px))
    assert t.pnl < 0  # giá đứng yên → lỗ đúng bằng chi phí


def test_funding_sign_long_pays_positive(cfg2):
    n = 600
    o = np.full(n, 100.0)
    f = pd.DataFrame({"funding_time_ms": [T0 + 300 * 60_000], "funding_rate": [0.001]})
    for side, sign in ((1, -1), (-1, 1)):
        T = run_symbol(_k(o, o, o, o), f, _sig(0, side, tp=np.nan, sl=np.nan, hold=500), Costs(0, 0), cfg2)
        assert np.sign(T.funding.iloc[0]) == sign


def test_no_entry_near_filler_and_no_overlap(cfg2):
    n = 200
    o = np.full(n, 100.0)
    fil = np.zeros(n, bool)
    fil[100:105] = True
    sig = pd.concat([_sig(10, 1, hold=50), _sig(20, 1, hold=50), _sig(120, 1, hold=5), _sig(170, -1, hold=5)])
    T = run_symbol(_k(o, o, o, o, fil), None, sig, Costs(0, 0), cfg2)
    assert list(T.bar_idx) == [10, 170]  # 20 trùng vị thế đang mở, 120 gần nến filler


def test_metrics_and_dsr_pbo_shapes():
    rng = np.random.default_rng(0)
    M = pd.DataFrame(rng.normal(0, 0.01, (400, 6)))
    out = pbo_cscv(M, S=8)
    assert 0 <= out["pbo"] <= 1
    d = deflated_sharpe(M[0], (M.mean() / M.std()).to_numpy())
    assert 0 <= d["dsr"] <= 1
    assert perf(pd.DataFrame(), T0, T0 + 10 * 86_400_000, 1e4)["total_return"] == 0


# ---------------------------------------------------------------- track ind (S2): engine lướt sóng
from kh.backtest.scalp import ScalpParams, run as scalp_run  # noqa: E402


def _m(o, h, l, c, filler=None):
    n = len(c)
    return pd.DataFrame({"open_time_ms": T0 + np.arange(n) * 60_000, "open": o, "high": h, "low": l, "close": c,
                         "is_filler": np.zeros(n, bool) if filler is None else filler})


def _flat(n=40, px=100.0):
    a = np.full(n, px)
    return a.copy(), a.copy(), a.copy(), a.copy()


def test_scalp_entry_next_open_and_fees_both_sides():
    o, h, l, c = _flat()
    o[1:] = 101.0
    h[1:], l[1:], c[1:] = 101.0, 101.0, 101.0
    sig = np.zeros(40, np.int8)
    sig[0] = 1
    T = scalp_run(_m(o, h, l, c), sig, 0.1, ScalpParams(slip_ticks=0), 0, 40)
    t = T.iloc[0]
    assert t.entry_idx == 1 and t.entry_raw == 101.0          # vào ở open nến kế tiếp
    assert t.reason == 0 and t.hold_min == 15                  # hết 15 phút
    assert np.isclose(t.fees, 0.0005 * 2)                      # phí 2 chiều
    assert np.isclose(t.net, -0.001)


def test_scalp_tp_and_sl_same_bar_counts_as_sl():
    o, h, l, c = _flat()
    h[3], l[3] = 101.0, 99.0                                   # nến 3 chạm cả TP (+0,45%) và SL (−0,30%)
    sig = np.zeros(40, np.int8)
    sig[0] = 1
    T = scalp_run(_m(o, h, l, c), sig, 0.1, ScalpParams(slip_ticks=0, fee=0), 0, 40)
    assert T.iloc[0].reason == -1 and np.isclose(T.iloc[0].gross, -0.003)


def test_scalp_no_entry_during_or_30min_after_filler():
    o, h, l, c = _flat(120)
    fil = np.zeros(120, bool)
    fil[10:12] = True
    sig = np.zeros(120, np.int8)
    sig[[9, 30, 50]] = 1                                       # vào ở 10 (filler), 31 (≤ 30′ sau), 51 (được)
    T = scalp_run(_m(o, h, l, c, fil), sig, 0.1, ScalpParams(), 0, 120)
    assert list(T.entry_idx) == [51]


def test_scalp_opposite_signal_exit_and_slippage_ticks():
    o, h, l, c = _flat()
    sig = np.zeros(40, np.int8)
    sig[0], sig[5] = 1, -1                                     # tín hiệu ngược tại nến 5 → thoát ở open nến 6
    T = scalp_run(_m(o, h, l, c), sig, 0.5, ScalpParams(fee=0, slip_ticks=2), 0, 40)
    t = T.iloc[0]
    assert t.reason == 2 and t.exit_idx == 6
    assert np.isclose(t.slippage, 2 * 2 * 0.5 / 100)           # 2 tick × 2 chiều
    assert len(T) == 1                                         # tín hiệu ngược khi đang có lệnh không mở lệnh mới
