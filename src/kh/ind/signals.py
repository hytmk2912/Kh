"""Tính mọi chỉ báo đã triển khai cho từng symbol → tín hiệu M1 (Parquet trong data/ind/signals/).

Directional: cột int8 (+1/−1/0, sự kiện). Filter: cột bool (trạng thái). Thêm htf_long_ok / htf_short_ok.
KHÔNG import module nhãn (có test kiểm tra).
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from kh.config import setup_logging, write_json
from kh.ind.htf import htf_permissions
from kh.ind.indicators.impl import IMPL, Ctx, compute
from kh.ind.indicators.registry import CARDS

log = setup_logging("ind.signals")


def col_key(name: str) -> str:
    i = [c.name for c in CARDS].index(name) + 1
    return f"i{i:03d}"


def ref_symbol(symbol: str) -> str:
    return "ETHUSDT" if symbol == "BTCUSDT" else "BTCUSDT"


def signals_path(P, symbol: str):
    return P.data / "ind" / "signals" / f"{symbol}.parquet"


def build_ctx(P, symbol: str) -> tuple[Ctx, pd.DataFrame]:
    from kh.ind.data import load_m1

    m1 = load_m1(P, symbol)
    ref = load_m1(P, ref_symbol(symbol)).set_index("open_time_ms").close.reindex(m1.open_time_ms).to_numpy()
    return Ctx.from_frame(m1, ref), m1


def run_indicators(cfg: dict, P) -> None:
    out_dir = P.data / "ind" / "signals"
    out_dir.mkdir(parents=True, exist_ok=True)
    timing, counts = {}, {}
    for s in cfg["symbols"]:
        X, m1 = build_ctx(P, s)
        cols = {"open_time_ms": X.t}
        cols["htf_long_ok"], cols["htf_short_ok"] = htf_permissions(X.t, X.c)
        counts[s] = {}
        for c in CARDS:
            if c.name not in IMPL:
                continue
            t0 = time.time()
            _, sig = compute(c.name, X)
            timing[c.name] = timing.get(c.name, 0.0) + time.time() - t0
            cols[col_key(c.name)] = sig
            counts[s][c.name] = int((sig != 0).sum()) if c.kind == "D" else float(np.mean(sig))
        pd.DataFrame(cols).to_parquet(signals_path(P, s), compression="zstd", index=False)
        log.info("%s: %d chỉ báo, HTF cho phép long %.1f%% / short %.1f%%", s, len(cols) - 3,
                 100 * cols["htf_long_ok"].mean(), 100 * cols["htf_short_ok"].mean())
    write_json({"signal_counts_or_filter_on_share": counts, "seconds_total": timing,
                "keys": {c.name: col_key(c.name) for c in CARDS if c.name in IMPL}},
               P.reports / "ind" / "signal_summary.json")
