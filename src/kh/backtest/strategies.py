"""Giai đoạn 7 — chuyển quy luật thành chiến lược có đặc tả đầy đủ.

Mỗi hàm trả về DataFrame tín hiệu cho MỘT coin: bar_idx (nến tín hiệu, đóng cửa), side, tp, sl,
max_hold, exit_at, risk_frac. Không có tín hiệu = "No Trade" (hợp lệ).
Danh sách biến thể được cố định TRƯỚC khi chạy backtest trên validation (xem VARIANTS).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from kh.waves.dc import run_dc, theta_series

# Toàn bộ biến thể sẽ được thử (đếm vào DSR/PBO). Không thêm biến thể sau khi xem kết quả validation.
VARIANTS = (
    [{"family": "model", "name": f"lgbm_H{H}_tau{tau}", "H": H, "tau": tau}
     for H in (60, 240) for tau in (0.55, 0.60, 0.65)]
    + [{"family": "reversal", "name": f"rev_{f}_H{H}", "feature": f, "H": H}
       for f in ("ret_15_z", "taker_imb_15", "rsi_14") for H in (60, 240)]
    + [{"family": "dc_follow", "name": f"dc_sig{k}", "scale": k} for k in (4, 8)]
)


def _barrier_signals(idx: np.ndarray, side: np.ndarray, barrier: np.ndarray, H: int) -> pd.DataFrame:
    return pd.DataFrame({"bar_idx": idx.astype(np.int64), "side": side.astype(np.int64), "tp": barrier, "sl": barrier,
                         "max_hold": np.full(len(idx), H, np.int64), "exit_at": np.full(len(idx), -1, np.int64),
                         "risk_frac": barrier})


def model_signals(S: pd.DataFrame, bar_index: pd.Series, v: dict, prob_col: str = "p_lgbm") -> pd.DataFrame:
    """Long nếu p ≥ τ, short nếu p ≤ 1 − τ. Thoát: TP = SL = rào triple-barrier, giữ tối đa H phút."""
    H, tau = v["H"], v["tau"]
    p = S[prob_col].to_numpy()
    side = np.where(p >= tau, 1, np.where(p <= 1 - tau, -1, 0))
    m = side != 0
    idx = bar_index.reindex(S.open_time_ms[m]).to_numpy()
    return _barrier_signals(idx, side[m], S[f"barrier_{H}"].to_numpy()[m], H)


def reversal_signals(S: pd.DataFrame, bar_index: pd.Series, v: dict, edges: dict) -> pd.DataFrame:
    """Quy luật đảo chiều ngắn hạn (H4/H7): đặc trưng ở decile thấp nhất (theo train) → long,
    decile cao nhất → short. Thoát như triple-barrier H."""
    f, H = v["feature"], v["H"]
    lo, hi = edges[f]
    x = S[f].to_numpy()
    side = np.where(x <= lo, 1, np.where(x >= hi, -1, 0))
    m = side != 0
    idx = bar_index.reindex(S.open_time_ms[m]).to_numpy()
    return _barrier_signals(idx, side[m], S[f"barrier_{H}"].to_numpy()[m], H)


def dc_signals(k: pd.DataFrame, v: dict, hl: int) -> pd.DataFrame:
    """H1: vào theo hướng sóng mới tại nến xác nhận DC; thoát ở giá mở cửa nến sau xác nhận ngược.
    Kích thước vị thế theo θ (khoảng cách tới điểm đảo chiều tiếp theo)."""
    dc = run_dc(k, theta_series(k.close, {"kind": "sigma", "value": v["scale"]}, hl))
    conf, typ, th = dc["piv_conf"], dc["piv_type"], dc["piv_theta"]
    side = np.where(typ == -1, 1, -1)  # đáy xác nhận → sóng tăng
    exit_at = np.append(conf[1:] + 1, -1)
    return pd.DataFrame({"bar_idx": conf.astype(np.int64), "side": side.astype(np.int64), "tp": np.nan, "sl": np.nan,
                         "max_hold": np.zeros(len(conf), np.int64), "exit_at": exit_at.astype(np.int64),
                         "risk_frac": th})


def random_signals(template: pd.DataFrame, valid_bars: np.ndarray, rng: np.random.Generator) -> pd.DataFrame:
    """Baseline ngẫu nhiên: cùng số lệnh, cùng tỷ lệ long/short, cùng quy tắc thoát, thời điểm ngẫu nhiên."""
    if template.empty:
        return template
    T = template.copy()
    T["bar_idx"] = np.sort(rng.choice(valid_bars, size=len(T), replace=len(T) > len(valid_bars)))
    T["side"] = rng.permutation(T.side.to_numpy())
    return T
