"""Phát hiện sóng bằng Directional Change (DC) / ZigZag.

Định nghĩa (xu hướng tăng): theo dõi đỉnh chạy `ext`. Khi giá thấp nhất của nến chạm
`ext * (1 - theta)` thì đỉnh được XÁC NHẬN tại nến đó (confirmation). Đỉnh (`extreme`) nằm ở quá
khứ; chỉ thời điểm xác nhận trở đi mới được dùng cho tín hiệu.

- `extreme_idx`  : vị trí đỉnh/đáy — nhãn HỒI CỨU (retrospective), cấm dùng làm tín hiệu.
- `confirm_idx`  : vị trí nến mà tại lúc đóng cửa ta biết đỉnh/đáy đã hình thành (online).
- Trạng thái theo từng nến (`state_*`) chỉ dùng dữ liệu đến hết nến đó → dùng được làm đặc trưng.

theta có thể thay đổi theo thời gian (ngưỡng theo độ biến động), giá trị tại nến i phải
được tính từ dữ liệu đến i-1.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from numba import njit
except ImportError:  # chạy được nhưng chậm hơn nếu thiếu numba
    def njit(*a, **k):
        def deco(f):
            return f
        return deco if not (a and callable(a[0])) else a[0]


@njit(cache=True)
def _dc_kernel(high, low, close, theta):
    n = len(close)
    piv_idx = np.empty(n, np.int64)
    piv_px = np.empty(n, np.float64)
    piv_type = np.empty(n, np.int8)       # +1 đỉnh, -1 đáy
    piv_conf = np.empty(n, np.int64)
    piv_theta = np.empty(n, np.float64)
    st_mode = np.zeros(n, np.int8)        # +1 đang tăng, -1 đang giảm, 0 chưa xác định
    st_ext = np.full(n, np.nan)           # cực trị chạy của xu hướng hiện tại
    st_conf_px = np.full(n, np.nan)       # giá đóng cửa tại nến xác nhận gần nhất
    st_conf_idx = np.full(n, -1, np.int64)
    st_theta = np.full(n, np.nan)         # theta tại lần xác nhận gần nhất
    k = 0
    mode = 0
    hi_ext = np.nan
    lo_ext = np.nan
    hi_i = -1
    lo_i = -1
    ext = np.nan
    ext_i = -1
    conf_px = np.nan
    conf_i = -1
    conf_th = np.nan
    for i in range(n):
        th = theta[i]
        if np.isnan(th):
            st_mode[i] = mode
            continue
        h = high[i]
        l = low[i]
        if mode == 0:
            if np.isnan(hi_ext) or h > hi_ext:
                hi_ext = h
                hi_i = i
            if np.isnan(lo_ext) or l < lo_ext:
                lo_ext = l
                lo_i = i
            if h >= lo_ext * (1.0 + th) and lo_i < i:
                piv_idx[k] = lo_i; piv_px[k] = lo_ext; piv_type[k] = -1; piv_conf[k] = i; piv_theta[k] = th
                k += 1
                mode = 1; ext = h; ext_i = i; conf_px = close[i]; conf_i = i; conf_th = th
            elif l <= hi_ext * (1.0 - th) and hi_i < i:
                piv_idx[k] = hi_i; piv_px[k] = hi_ext; piv_type[k] = 1; piv_conf[k] = i; piv_theta[k] = th
                k += 1
                mode = -1; ext = l; ext_i = i; conf_px = close[i]; conf_i = i; conf_th = th
        elif mode == 1:
            if h > ext:
                ext = h
                ext_i = i
            if l <= ext * (1.0 - th) and ext_i < i:
                piv_idx[k] = ext_i; piv_px[k] = ext; piv_type[k] = 1; piv_conf[k] = i; piv_theta[k] = th
                k += 1
                mode = -1; ext = l; ext_i = i; conf_px = close[i]; conf_i = i; conf_th = th
        else:
            if l < ext:
                ext = l
                ext_i = i
            if h >= ext * (1.0 + th) and ext_i < i:
                piv_idx[k] = ext_i; piv_px[k] = ext; piv_type[k] = -1; piv_conf[k] = i; piv_theta[k] = th
                k += 1
                mode = 1; ext = h; ext_i = i; conf_px = close[i]; conf_i = i; conf_th = th
        st_mode[i] = mode
        st_ext[i] = ext
        st_conf_px[i] = conf_px
        st_conf_idx[i] = conf_i
        st_theta[i] = conf_th
    return (piv_idx[:k], piv_px[:k], piv_type[:k], piv_conf[:k], piv_theta[:k],
            st_mode, st_ext, st_conf_px, st_conf_idx, st_theta)


def sigma_1m(close: pd.Series, halflife_min: int) -> pd.Series:
    """Độ lệch chuẩn EWMA của log return 1 phút, đã dịch 1 nến (chỉ dùng quá khứ)."""
    r = np.log(close).diff()
    return np.sqrt((r ** 2).ewm(halflife=halflife_min, min_periods=halflife_min).mean()).shift(1)


def theta_series(close: pd.Series, spec: dict, halflife_min: int) -> np.ndarray:
    if spec["kind"] == "sigma":
        return (spec["value"] * sigma_1m(close, halflife_min) * np.sqrt(60)).to_numpy()
    return np.full(len(close), float(spec["value"]))


def scale_specs(cfg: dict) -> list[dict]:
    w = cfg["waves"]
    specs = [{"name": f"sig{k}", "kind": "sigma", "value": k} for k in w["sigma_scales"]]
    specs += [{"name": f"pct{p * 100:g}", "kind": "pct", "value": p} for p in w["fixed_pcts"]]
    return specs


def run_dc(df: pd.DataFrame, theta: np.ndarray) -> dict:
    """Chạy DC trên khung nến 1 phút đã sắp xếp. Trả về pivot và trạng thái theo nến."""
    out = _dc_kernel(df.high.to_numpy(np.float64), df.low.to_numpy(np.float64),
                     df.close.to_numpy(np.float64), np.asarray(theta, np.float64))
    keys = ["piv_idx", "piv_px", "piv_type", "piv_conf", "piv_theta",
            "st_mode", "st_ext", "st_conf_px", "st_conf_idx", "st_theta"]
    return dict(zip(keys, out))


@njit(cache=True)
def _wave_paths(high, low, close, a, b, direction):
    """Độ sâu nhịp hồi lớn nhất (theo tỷ lệ biên độ đã đi) bên trong sóng [a, b]."""
    m = len(a)
    max_retr = np.full(m, np.nan)
    for j in range(m):
        s, e, d = a[j], b[j], direction[j]
        if e - s < 2:
            continue
        start = low[s] if d == 1 else high[s]
        run = start
        worst = 0.0
        for i in range(s + 1, e):
            if d == 1:
                if high[i] > run:
                    run = high[i]
                gain = run - start
                if gain > 0:
                    r = (run - low[i]) / gain
                    if r > worst:
                        worst = r
            else:
                if low[i] < run:
                    run = low[i]
                gain = start - run
                if gain > 0:
                    r = (high[i] - run) / gain
                    if r > worst:
                        worst = r
        max_retr[j] = worst
    return max_retr


def waves_table(df: pd.DataFrame, dc: dict, small_dc: dict | None = None) -> pd.DataFrame:
    """Bảng sóng: mỗi dòng là đoạn giữa hai pivot liên tiếp.

    Các cột *_confirm_* là thời điểm có thể biết trong thời gian thực; cột extreme là hồi cứu.
    """
    pi, pp, pt, pc, pth = dc["piv_idx"], dc["piv_px"], dc["piv_type"], dc["piv_conf"], dc["piv_theta"]
    if len(pi) < 2:
        return pd.DataFrame()
    t = df.open_time_ms.to_numpy()
    c = df.close.to_numpy()
    o = df.open.to_numpy()
    h = df.high.to_numpy()
    l = df.low.to_numpy()
    v = df.volume.to_numpy()
    a, b = pi[:-1], pi[1:]
    direction = np.where(pt[:-1] == -1, 1, -1)
    log_amp = np.log(pp[1:] / pp[:-1])
    dur = b - a
    w = pd.DataFrame({
        "start_ms": t[a], "end_ms": t[b], "direction": direction,
        "start_price": pp[:-1], "end_price": pp[1:],
        "amp_abs": pp[1:] - pp[:-1], "amp_pct": pp[1:] / pp[:-1] - 1, "amp_log_abs": np.abs(log_amp),
        "duration_min": dur, "speed_pct_per_hour": np.abs(log_amp) / np.maximum(dur, 1) * 60 * 100,
        # thời điểm online
        "start_confirm_ms": t[pc[:-1]], "end_confirm_ms": t[pc[1:]],
        "start_detect_lag_min": pc[:-1] - a, "end_detect_lag_min": pc[1:] - b,
        "theta_at_start_confirm": pth[:-1], "theta_at_end_confirm": pth[1:],
    })
    cs, ce = c[pc[:-1]], c[pc[1:]]
    # Phần "overshoot": quãng đường từ lúc xác nhận sóng đến cực trị cuối sóng (đơn vị theta)
    w["overshoot_over_theta"] = direction * np.log(pp[1:] / cs) / pth[:-1]
    # Lãi/lỗ (log, trước phí) của việc vào lệnh theo hướng sóng tại giá MỞ CỬA nến sau nến xác nhận
    # đầu sóng và thoát tại giá mở cửa nến sau nến xác nhận cuối sóng — kiểm định H1.
    last = len(o) - 1
    ein, eout = o[np.minimum(pc[:-1] + 1, last)], o[np.minimum(pc[1:] + 1, last)]
    w["dc_follow_logret"] = direction * np.log(eout / ein)
    w["dc_follow_hold_min"] = np.minimum(pc[1:] + 1, last) - np.minimum(pc[:-1] + 1, last)
    del ce
    w["max_retracement_frac"] = _wave_paths(h, l, c, a, b, direction)
    cv = np.concatenate([[0.0], np.cumsum(v)])
    w["volume_sum"] = cv[b + 1] - cv[a]
    pre = np.maximum(a - 1440, 0)
    pre_rate = (cv[a] - cv[pre]) / np.maximum(a - pre, 1)
    w["rel_volume"] = (w.volume_sum / (dur + 1)) / np.where(pre_rate > 0, pre_rate, np.nan)
    r = np.concatenate([[0.0], np.diff(np.log(c))])
    cr, cr2 = np.concatenate([[0.0], np.cumsum(r)]), np.concatenate([[0.0], np.cumsum(r ** 2)])
    n = (b - a).astype(float)
    mean = (cr[b + 1] - cr[a + 1]) / np.maximum(n, 1)
    w["vol_1m_inside"] = np.sqrt(np.maximum((cr2[b + 1] - cr2[a + 1]) / np.maximum(n, 1) - mean ** 2, 0))
    rng = np.where(h - l > 0, h - l, np.nan)
    body = np.nan_to_num(np.abs(c - o) / rng, nan=0.0)
    cb = np.concatenate([[0.0], np.cumsum(body)])
    w["body_ratio_mean"] = (cb[b + 1] - cb[a]) / (dur + 1)
    tr = np.maximum(h, np.roll(c, 1)) - np.minimum(l, np.roll(c, 1))
    tr[0] = h[0] - l[0]
    ctr = np.concatenate([[0.0], np.cumsum(tr / c)])
    p60 = np.maximum(a - 60, 0)
    w["atr60_pct_before"] = (ctr[a] - ctr[p60]) / np.maximum(a - p60, 1)
    w["ret60_before"] = np.log(c[a] / c[np.maximum(a - 60, 0)])
    if small_dc is not None:
        sp = small_dc["piv_idx"]
        cnt = np.searchsorted(sp, b, side="left") - np.searchsorted(sp, a, side="right")
        w["n_small_pivots_inside"] = cnt
        w["n_counter_moves"] = cnt // 2
    return w
