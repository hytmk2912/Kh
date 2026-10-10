"""Nhãn sóng — ĐÁP ÁN để chấm (spec §2). Được nhìn lại quá khứ; KHÔNG BAO GIỜ là đầu vào tín hiệu.

ZigZag p% trên high/low:
- đang tìm đỉnh: đỉnh = high cao nhất; khi low ≤ đỉnh × (1 − p) → chốt đỉnh (`event_idx` = nến tạo đỉnh,
  `confirm_idx` = nến làm giá đảo p%), chuyển sang tìm đáy; ngược lại tương tự.
- nến filler bị bỏ qua khi cập nhật đỉnh/đáy và khi xét điều kiện đảo chiều.
- Nếu đỉnh mới và cú đảo p% cùng nằm trong một nến thì không chốt ở nến đó (không biết thứ tự trong nến).

Nhãn từng nến (mã số, thứ tự ưu tiên khi trùng — [A] chốt trong CHANGELOG 2026-10-09):
UNKNOWN (0) > ĐI NGANG (3) > NHỊP HỒI (4) > SÓNG TĂNG (1) / SÓNG GIẢM (2).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from kh.config import setup_logging, split_ms, write_json

try:
    from numba import njit
except ImportError:
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]

log = setup_logging("ind.labels")

UNKNOWN, UP, DOWN, FLAT, PULLBACK = 0, 1, 2, 3, 4
LABEL_NAMES = {UNKNOWN: "UNKNOWN", UP: "SÓNG TĂNG", DOWN: "SÓNG GIẢM", FLAT: "ĐI NGANG", PULLBACK: "NHỊP HỒI"}


@njit(cache=True)
def zigzag(high, low, filler, pct):
    """Trả về (event_idx, price, type, confirm_idx) của các điểm xoay. type: +1 đỉnh, −1 đáy."""
    n = len(high)
    ev = np.empty(n, np.int64)
    px = np.empty(n, np.float64)
    tp = np.empty(n, np.int8)
    cf = np.empty(n, np.int64)
    k = 0
    mode = 0
    hi = -1.0
    lo = -1.0
    hi_i = -1
    lo_i = -1
    for i in range(n):
        if filler[i]:
            continue
        h = high[i]
        l = low[i]
        if mode == 0:
            if hi_i < 0 or h > hi:
                hi = h
                hi_i = i
            if lo_i < 0 or l < lo:
                lo = l
                lo_i = i
            if h >= lo * (1.0 + pct) and lo_i < i:
                ev[k] = lo_i; px[k] = lo; tp[k] = -1; cf[k] = i; k += 1
                mode = 1; hi = h; hi_i = i
            elif l <= hi * (1.0 - pct) and hi_i < i:
                ev[k] = hi_i; px[k] = hi; tp[k] = 1; cf[k] = i; k += 1
                mode = -1; lo = l; lo_i = i
        elif mode == 1:
            if h > hi:
                hi = h
                hi_i = i
            if l <= hi * (1.0 - pct) and hi_i < i:
                ev[k] = hi_i; px[k] = hi; tp[k] = 1; cf[k] = i; k += 1
                mode = -1; lo = l; lo_i = i
        else:
            if l < lo:
                lo = l
                lo_i = i
            if h >= lo * (1.0 + pct) and lo_i < i:
                ev[k] = lo_i; px[k] = lo; tp[k] = -1; cf[k] = i; k += 1
                mode = 1; hi = h; hi_i = i
    return ev[:k], px[:k], tp[:k], cf[:k]


@njit(cache=True)
def _fast_reach(high, low, start, direction, start_px, pct, horizon):
    """Số phút (nến) từ điểm xuất phát tới khi giá đi được pct theo hướng sóng; −1 nếu quá horizon."""
    m = len(start)
    out = np.full(m, -1, np.int64)
    n = len(high)
    for j in range(m):
        s = start[j]
        for i in range(s + 1, min(s + horizon, n - 1) + 1):
            if direction[j] == 1 and high[i] >= start_px[j] * (1.0 + pct):
                out[j] = i - s
                break
            if direction[j] == -1 and low[i] <= start_px[j] * (1.0 - pct):
                out[j] = i - s
                break
    return out


def waves(m1: pd.DataFrame, pct: float, fast_minutes: int = 15) -> pd.DataFrame:
    """Bảng sóng từ ZigZag pct."""
    h, l = m1.high.to_numpy(np.float64), m1.low.to_numpy(np.float64)
    fil = m1.is_filler.to_numpy()
    ev, px, tp, cf = zigzag(h, l, fil, pct)
    if len(ev) < 2:
        return pd.DataFrame()
    t = m1.open_time_ms.to_numpy()
    a, b = ev[:-1], ev[1:]
    d = np.where(tp[:-1] == -1, 1, -1)
    amp = px[1:] / px[:-1] - 1
    dur = b - a
    reach = _fast_reach(h, l, a, d, px[:-1], pct, fast_minutes)
    w = pd.DataFrame({"start_idx": a, "end_idx": b, "direction": d,
                      "start_event_ms": t[a], "end_event_ms": t[b],
                      "start_confirm_ms": t[cf[:-1]], "end_confirm_ms": t[cf[1:]],
                      "start_px": px[:-1], "end_px": px[1:], "amp_pct": np.abs(amp) * 100,
                      "minutes": dur, "speed_pct_per_min": np.abs(amp) * 100 / np.maximum(dur, 1),
                      "minutes_to_pct": np.where(reach >= 0, reach, np.nan), "fast": reach >= 0})
    return w[w.amp_pct >= pct * 100 - 1e-9].reset_index(drop=True)


def bar_labels(m1: pd.DataFrame, pct: float, pullback_pct: float = 0.002, flat_minutes: int = 30,
               unknown_after_filler: int = 30, fast_minutes: int = 15) -> tuple[np.ndarray, pd.DataFrame]:
    """Nhãn từng nến + bảng sóng (có độ sâu nhịp hồi sâu nhất). Độ dài tính theo số nến của `m1`
    (track M15 truyền nến M15: flat_minutes/fast_minutes/unknown_after_filler là số nến M15)."""
    n = len(m1)
    W = waves(m1, pct, fast_minutes)
    lab = np.zeros(n, np.int8)
    for d, code in ((1, UP), (-1, DOWN)):
        sel = W[W.direction == d]
        for a, b in zip(sel.start_idx.to_numpy(), sel.end_idx.to_numpy()):
            lab[a:b] = code
    # Nhịp hồi: sóng ZigZag 0,2% ngược chiều nằm trọn trong sóng chính
    sub = waves(m1, pullback_pct, fast_minutes=0)
    depth = np.zeros(len(W))
    if len(W) and len(sub):
        ss, se, sd, sa = (sub[c].to_numpy() for c in ("start_idx", "end_idx", "direction", "amp_pct"))
        for j, (a, b, d, amp) in enumerate(zip(W.start_idx, W.end_idx, W.direction, W.amp_pct)):
            lo_k, hi_k = np.searchsorted(ss, a, "left"), np.searchsorted(ss, b, "left")
            for k in range(lo_k, hi_k):
                if se[k] <= b and sd[k] == -d:
                    lab[ss[k]:se[k]] = PULLBACK
                    depth[j] = max(depth[j], sa[k] / amp * 100)
    if len(W):
        W["deepest_pullback_pct_of_wave"] = depth
    # Đi ngang: mọi nến thuộc một cửa sổ ≥ flat_minutes phút có (max high − min low)/close < pct
    hh = m1.high.rolling(flat_minutes).max()
    ll = m1.low.rolling(flat_minutes).min()
    flat_end = ((hh - ll) / m1.close < pct).to_numpy()
    flat = np.zeros(n, bool)
    idx = np.flatnonzero(flat_end)
    if len(idx):
        cov = np.zeros(n + 1, np.int64)
        np.add.at(cov, idx - flat_minutes + 1, 1)
        np.add.at(cov, idx + 1, -1)
        flat = np.cumsum(cov[:-1]) > 0
    lab[flat] = FLAT
    # UNKNOWN: nến filler + 30 phút sau; và đoạn ngoài sóng (trước điểm xoay đầu / sau điểm xoay cuối)
    fil = m1.is_filler.to_numpy().astype(np.int64)
    after = np.convolve(fil, np.ones(unknown_after_filler + 1, np.int64))[:n] > 0
    lab[after] = UNKNOWN
    if len(W):
        lab[: W.start_idx.iloc[0]] = UNKNOWN
        lab[W.end_idx.iloc[-1]:] = UNKNOWN
    return lab, W


def flat_segments(lab: np.ndarray) -> int:
    f = (lab == FLAT).astype(np.int8)
    return int(((np.diff(np.concatenate([[0], f])) == 1)).sum())


def wave_stats(W: pd.DataFrame, lab: np.ndarray) -> dict:
    out = {"n_bars": int(len(lab)),
           "label_share": {LABEL_NAMES[c]: float((lab == c).mean()) for c in LABEL_NAMES},
           "flat_segments": flat_segments(lab)}
    for name, d in (("up", 1), ("down", -1)):
        g = W[W.direction == d]
        for speed, gg in (("fast", g[g.fast]), ("slow", g[~g.fast])):
            out[f"{name}_{speed}"] = {"n": int(len(gg)), "minutes_mean": float(gg.minutes.mean()) if len(gg) else None,
                                      "minutes_median": float(gg.minutes.median()) if len(gg) else None,
                                      "amp_pct_mean": float(gg.amp_pct.mean()) if len(gg) else None,
                                      "deepest_pullback_pct_median": float(gg.deepest_pullback_pct_of_wave.median()) if len(gg) else None}
    return out


def labels_dir(P, tr=None):
    from kh.ind.track import M1

    return (tr or M1).data(P) / "labels"


def track_labels(m: pd.DataFrame, pct: float, tr) -> tuple[np.ndarray, pd.DataFrame]:
    return bar_labels(m, pct, tr.pullback_pct, tr.flat_bars, tr.unknown_after_filler, tr.fast_bars)


def run_labels(cfg: dict, P, tr=None) -> None:
    from kh.ind.data import load_bars
    from kh.ind.track import M1

    tr = tr or M1
    out_dir = labels_dir(P, tr)
    out_dir.mkdir(parents=True, exist_ok=True)
    _, val_end = split_ms(cfg, "val")
    stats, md = {}, []
    main_key = f"{tr.wave_pct * 100:.1f}%"
    for s in cfg["symbols"]:
        m1 = load_bars(P, s, tr.tf)
        stats[s] = {}
        for pct in tr.wave_sens:
            lab, W = track_labels(m1, pct, tr)
            if pct == tr.wave_pct:  # ngưỡng chính: lưu đáp án để chấm (cả giai đoạn test — chưa ai xem kết quả trên đó)
                pd.DataFrame({"open_time_ms": m1.open_time_ms, "label": lab}).to_parquet(out_dir / f"bars_{s}.parquet", index=False)
                W.assign(symbol=s).to_parquet(out_dir / f"waves_{s}.parquet", index=False)
            # Thống kê chỉ trên train + validation (không mô tả giai đoạn test khoá)
            keep = (m1.open_time_ms < val_end).to_numpy()
            Wr = W[W.end_event_ms < val_end]
            stats[s][f"{pct * 100:.1f}%"] = wave_stats(Wr, lab[keep])
        log.info("%s: sóng %s nhanh tăng %d / giảm %d", s, main_key, stats[s][main_key]["up_fast"]["n"], stats[s][main_key]["down_fast"]["n"])
    sens = [f"{p * 100:.1f}%".replace(".", ",") for p in tr.wave_sens if p != tr.wave_pct]
    stats["_note"] = {"period": "train + validation (2024-10-09 → 2026-05-15)",
                      "priority": "UNKNOWN > ĐI NGANG > NHỊP HỒI > SÓNG",
                      "sensitivity": f"{' và '.join(sens)} chỉ để báo cáo, không dùng để chọn",
                      "flat_threshold": f"cùng ngưỡng với sóng; nhịp hồi dùng ZigZag {tr.pullback_pct * 100:.1f}% cố định".replace(".", ",", 1)}
    if tr.tf != 1:
        stats["_note"] |= {"bars": f"nến M{tr.tf}", "fast": f"sóng nhanh: đi được ngưỡng trong ≤ {tr.fast_bars} nến ({tr.fast_bars * tr.tf // 60} giờ)",
                           "flat": f"đi ngang: cửa sổ ≥ {tr.flat_bars} nến ({tr.flat_bars * tr.tf // 60} giờ)",
                           "minutes_unit": f"cột minutes_* tính theo số nến M{tr.tf}"}
    write_json(stats, tr.reports(P) / "waves_stats.json")
    _markdown(stats, cfg, tr.reports(P) / "waves_stats.md", tr)


def _markdown(stats: dict, cfg: dict, path, tr=None) -> None:
    from kh.ind.track import M1

    tr = tr or M1
    f = lambda x, d=1: "" if x is None else f"{x:.{d}f}"
    fast_txt = "15 phút" if tr.tf == 1 else f"{tr.fast_bars} nến M{tr.tf} ({tr.fast_bars * tr.tf // 60} giờ)"
    unit = "Phút" if tr.tf == 1 else f"Số nến M{tr.tf}"
    L = ["# Thống kê sóng (đáp án ZigZag) — train + validation", "",
         f"Sóng nhanh = đi được ≥ ngưỡng trong ≤ {fast_txt} tính từ điểm xuất phát. Tỷ lệ nhãn tính trên số nến.",
         "Thứ tự ưu tiên nhãn: UNKNOWN > ĐI NGANG > NHỊP HỒI > SÓNG. Số liệu [F] đo trên dữ liệu thật.", ""]
    main = f"{tr.wave_pct * 100:.1f}%"
    order = [main] + [f"{p * 100:.1f}%" for p in tr.wave_sens if p != tr.wave_pct]
    for th in order:
        L += [f"## Ngưỡng {th}" + (" (chính)" if th == main else " (độ nhạy, chỉ báo cáo)"), "",
              f"| Symbol | Tăng nhanh | Tăng chậm | Giảm nhanh | Giảm chậm | Đoạn đi ngang | {unit} TB / trung vị (tăng nhanh) | Biên độ TB % (tăng nhanh) | Hồi sâu nhất TV % sóng | % SÓNG | % NHỊP HỒI | % ĐI NGANG | % UNKNOWN |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for s in cfg["symbols"]:
            v = stats[s][th]
            uf, us, df, ds, sh = v["up_fast"], v["up_slow"], v["down_fast"], v["down_slow"], v["label_share"]
            L.append(f"| {s} | {uf['n']} | {us['n']} | {df['n']} | {ds['n']} | {v['flat_segments']} | "
                     f"{f(uf['minutes_mean'])} / {f(uf['minutes_median'])} | {f(uf['amp_pct_mean'], 2)} | {f(uf['deepest_pullback_pct_median'])} | "
                     f"{(sh['SÓNG TĂNG'] + sh['SÓNG GIẢM']) * 100:.1f} | {sh['NHỊP HỒI'] * 100:.1f} | {sh['ĐI NGANG'] * 100:.1f} | {sh['UNKNOWN'] * 100:.2f} |")
        L.append("")
    path.write_text("\n".join(L) + "\n")
