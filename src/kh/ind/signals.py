"""Tính mọi chỉ báo đã triển khai cho từng symbol → tín hiệu (Parquet trong data/<track>/signals/).

Directional: cột int8 (+1/−1/0, sự kiện). Filter: cột bool (trạng thái). Thêm htf_long_ok / htf_short_ok.
Track M15 thêm dạng TRẠNG THÁI của mỗi directional: cột `<key>_st` (spec M15 §3).
KHÔNG import module nhãn (có test kiểm tra).
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from kh.config import setup_logging, write_json
from kh.ind.htf import htf_permissions
from kh.ind.indicators.impl import IMPL, Ctx, compute, timeframe
from kh.ind.indicators.registry import CARDS
from kh.ind.track import M1

log = setup_logging("ind.signals")


def col_key(name: str) -> str:
    i = [c.name for c in CARDS].index(name) + 1
    return f"i{i:03d}"


def ref_symbol(symbol: str) -> str:
    return "ETHUSDT" if symbol == "BTCUSDT" else "BTCUSDT"


def signals_path(P, symbol: str, tr=M1):
    return tr.data(P) / "signals" / f"{symbol}.parquet"


def event_state(ev: np.ndarray) -> np.ndarray:
    """Dạng trạng thái của một directional [A]: hướng của sự kiện gần nhất tại hoặc trước nến t (giữ tới khi có
    sự kiện ngược), 0 trước sự kiện đầu tiên. Với quy tắc cắt (giá cắt EMA) đúng bằng "giá đang trên/dưới EMA"."""
    e = np.asarray(ev, np.int8)
    idx = np.where(e != 0, np.arange(len(e)), -1)
    last = np.maximum.accumulate(idx) if len(e) else idx
    return np.where(last >= 0, e[np.maximum(last, 0)], 0).astype(np.int8)


def build_ctx(P, symbol: str, tr=M1) -> tuple[Ctx, pd.DataFrame]:
    from kh.ind.data import load_bars

    m1 = load_bars(P, symbol, tr.tf)
    ref = load_bars(P, ref_symbol(symbol), tr.tf).set_index("open_time_ms").close.reindex(m1.open_time_ms).to_numpy()
    return Ctx.from_frame(m1, ref), m1


def run_indicators(cfg: dict, P, tr=M1) -> None:
    out_dir = tr.data(P) / "signals"
    out_dir.mkdir(parents=True, exist_ok=True)
    timing, counts, st_counts = {}, {}, {}
    for s in cfg["symbols"]:
        X, m1 = build_ctx(P, s, tr)
        cols = {"open_time_ms": X.t}
        cols["htf_long_ok"], cols["htf_short_ok"] = htf_permissions(X.t, X.c, tr.htf, tr.tf)
        counts[s], st_counts[s] = {}, {}
        with timeframe(tr):
            for c in CARDS:
                if c.name not in IMPL:
                    continue
                t0 = time.time()
                _, sig = compute(c.name, X)
                timing[c.name] = timing.get(c.name, 0.0) + time.time() - t0
                cols[col_key(c.name)] = sig
                counts[s][c.name] = int((sig != 0).sum()) if c.kind == "D" else float(np.mean(sig))
                if tr is not M1 and c.kind == "D":
                    st = event_state(sig)
                    cols[col_key(c.name) + "_st"] = st
                    st_counts[s][c.name] = {"long_share": float((st == 1).mean()), "short_share": float((st == -1).mean())}
        pd.DataFrame(cols).to_parquet(signals_path(P, s, tr), compression="zstd", index=False)
        log.info("%s: %d cột chỉ báo, HTF cho phép long %.1f%% / short %.1f%%", s, len(cols) - 3,
                 100 * cols["htf_long_ok"].mean(), 100 * cols["htf_short_ok"].mean())
    rep = {"signal_counts_or_filter_on_share": counts, "seconds_total": timing,
           "keys": {c.name: col_key(c.name) for c in CARDS if c.name in IMPL}}
    if tr is not M1:
        rep |= {"state_share": st_counts, "bars": f"M{tr.tf}", "htf_frames_min": list(tr.htf),
                "param_overrides": tr.param_overrides, "bars_per_day": tr.bars_per_day}
    write_json(rep, tr.reports(P) / "signal_summary.json")
