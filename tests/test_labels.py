import ast
import pathlib
import subprocess
import sys

import numpy as np
import pandas as pd

from conftest import T0
from kh.ind.labels import DOWN, FLAT, PULLBACK, UNKNOWN, UP, bar_labels, waves, zigzag

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "kh" / "ind"


def _bars(path, filler=None):
    c = np.asarray(path, float)
    o = np.concatenate([[c[0]], c[:-1]])
    n = len(c)
    return pd.DataFrame({"open_time_ms": T0 + np.arange(n) * 60_000, "open": o, "high": np.maximum(o, c),
                         "low": np.minimum(o, c), "close": c, "volume": np.ones(n),
                         "is_filler": np.zeros(n, bool) if filler is None else filler})


def _known_path():
    # 100 → 101 trong 5 phút (sóng tăng nhanh 1%) → 100,3 (giảm 0,69%, chậm: 40 phút) → 100,9 → 99 (giảm 1,9%)
    up1 = np.linspace(100, 101, 6)
    dn1 = np.linspace(101, 100.3, 41)[1:]
    up2 = np.linspace(100.3, 100.9, 31)[1:]
    dn2 = np.linspace(100.9, 99, 20)[1:]
    return np.concatenate([up1, dn1, up2, dn2])


def test_zigzag_known_answer():
    m = _bars(_known_path())
    ev, px, tp, cf = zigzag(m.high.values, m.low.values, m.is_filler.values, 0.005)
    assert list(tp[:3]) == [-1, 1, -1]
    assert np.allclose(px[:3], [100, 101, 100.3])
    assert list(ev[:3]) == [0, 5, 45]
    assert np.all(cf > ev), "xác nhận phải sau điểm xoay"
    # đỉnh 101 được xác nhận ở nến đầu tiên có low ≤ 101 × 0,995 = 100,495
    first = int(np.argmax(m.low.values[6:] <= 101 * 0.995)) + 6
    assert cf[1] == first


def test_wave_table_fast_flag_and_amplitude():
    W = waves(_bars(_known_path()), 0.005)
    up = W.iloc[0]
    assert up.direction == 1 and np.isclose(up.amp_pct, 1.0) and up.fast and up.minutes == 5
    dn = W.iloc[1]
    assert dn.direction == -1 and not dn.fast  # 0,5% đầu tiên mất > 15 phút
    assert (W.amp_pct >= 0.5 - 1e-9).all()


def test_filler_ignored_and_unknown_after_filler():
    path = _known_path()
    fil = np.zeros(len(path), bool)
    fil[10:13] = True
    m = _bars(path, fil)
    m.loc[11, "high"] = 200.0  # giá rác trong nến filler không được tạo đỉnh
    lab, W = bar_labels(m, 0.005)
    assert W.end_px.max() < 150
    assert (lab[10:43] == UNKNOWN).all()  # filler + 30 phút sau


def test_flat_and_pullback_labels():
    rng = np.random.default_rng(0)
    flat = 100 + rng.uniform(-0.05, 0.05, 60)          # 60 phút biên độ < 0,5%
    up = np.linspace(100, 102, 40)
    pull = np.linspace(102, 101.6, 8)[1:]               # hồi 0,4% (> 0,2%) trong sóng tăng
    up2 = np.linspace(101.6, 103, 20)[1:]
    dn = np.linspace(103, 101, 30)[1:]
    up3 = np.linspace(101, 102, 10)[1:]                 # xác nhận đáy để sóng giảm có điểm kết thúc
    lab, W = bar_labels(_bars(np.concatenate([flat, up, pull, up2, dn, up3])), 0.005)
    assert (lab[5:50] == FLAT).sum() > 30
    i0 = 60 + 40
    assert (lab[i0:i0 + 6] == PULLBACK).sum() >= 4
    assert (lab == UP).any() and (lab == DOWN).any()
    w = W[W.direction == 1].iloc[-1]
    assert w.deepest_pullback_pct_of_wave > 0


def _imports(path: pathlib.Path) -> set[str]:
    mods = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            mods |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
            mods |= {f"{node.module}.{a.name}" for a in node.names}
    return mods


def test_signal_modules_never_import_labels():
    """Quy tắc cứng: chỉ báo/tín hiệu/tổ hợp không được import module nhãn (đáp án)."""
    files = list((SRC / "indicators").rglob("*.py")) + [SRC / f for f in ("signals.py", "htf.py") if (SRC / f).exists()]
    assert files, "phải có ít nhất package indicators"
    for f in files:
        bad = {m for m in _imports(f) if "labels" in m}
        assert not bad, f"{f} import module nhãn: {bad}"
    code = "import sys, kh.ind.indicators\n" + \
           ("import kh.ind.signals\n" if (SRC / "signals.py").exists() else "") + \
           "assert 'kh.ind.labels' not in sys.modules, 'module nhãn bị nạp gián tiếp'"
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------- track M15 (việc N1): ZigZag 1,5% trên nến M15
from kh.ind.labels import track_labels  # noqa: E402
from kh.ind.track import M15  # noqa: E402


def _bars15(path, filler=None):
    m = _bars(path, filler)
    m["open_time_ms"] = T0 + np.arange(len(m)) * 900_000
    return m


def _known_path15():
    # đi ngang 40 nến (10 giờ, biên độ 0,2%) → tăng 100 → 101,6 trong 10 nến (nhanh, 2,5 giờ)
    # → giảm 101,6 → 100,4 (8 nến) → hồi 100,4 → 101,1 (0,7%: nhịp hồi trong sóng giảm) → giảm tiếp tới 99
    # → tăng 101 (+2%) xác nhận đáy 99
    rng = np.random.default_rng(1)
    flat = 100 + rng.uniform(0.02, 0.2, 40)          # luôn > 100 → đáy duy nhất 100 ở nến 39
    flat[-1] = 100.0
    up = np.linspace(100, 101.6, 11)[1:]
    dn1 = np.linspace(101.6, 100.4, 9)[1:]           # giảm dốc để không có cửa sổ 32 nến < 1,5% quanh nhịp hồi
    pb = np.linspace(100.4, 101.1, 6)[1:]           # hồi 0,7% (> 0,6%) trong sóng giảm
    dn2 = np.linspace(101.1, 99.0, 9)[1:]
    up2 = np.linspace(99.0, 101.0, 12)[1:]           # +2,0% để xác nhận đáy 99
    return np.concatenate([flat, up, dn1, pb, dn2, up2])


def test_m15_waves_known_answer():
    path = _known_path15()
    lab, W = track_labels(_bars15(path), M15.wave_pct, M15)
    assert list(W.direction[:2]) == [1, -1]
    up, dn = W.iloc[0], W.iloc[1]
    assert np.isclose(up.start_px, 100.0) and np.isclose(up.end_px, 101.6) and up.minutes == 10
    assert up.fast, "1,6% trong 10 nến M15 (2,5 giờ) là sóng nhanh (≤ 32 nến)"
    assert np.isclose(dn.end_px, 99.0)
    reach = W.iloc[1].minutes_to_pct
    assert dn.fast == (reach <= 32)
    # đi ngang: 40 nến đầu (≥ 32 nến, biên độ < 1,5%) — trừ đoạn UNKNOWN trước điểm xoay đầu
    assert (lab[:40] == FLAT).sum() + (lab[:40] == UNKNOWN).sum() == 40
    # nhịp hồi 0,6% bên trong sóng giảm
    i_pb = 40 + 10 + 8
    assert (lab[i_pb - 2:i_pb + 6] == PULLBACK).sum() >= 3


def test_m15_slow_wave_and_unknown_after_filler():
    up = np.linspace(100, 101.6, 41)            # 1,6% trong 40 nến: chạm +1,5% ở nến 38 > 32 → sóng chậm
    dn = np.linspace(101.6, 99.5, 15)[1:]
    up2 = np.linspace(99.5, 101.5, 10)[1:]
    path = np.concatenate([up, dn, up2])
    fil = np.zeros(len(path), bool)
    fil[60] = True
    lab, W = track_labels(_bars15(path, fil), M15.wave_pct, M15)
    assert W.iloc[0].direction == 1 and not W.iloc[0].fast
    assert (lab[60:63] == UNKNOWN).all(), "nến filler + 2 nến M15 sau"
