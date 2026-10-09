"""Bảng A — chấm khả năng BẮT SÓNG của tín hiệu (spec §4). Module chấm điểm được phép đọc nhãn (đáp án).

Định nghĩa:
- Tín hiệu tại nến t (đóng cửa), giá vào = open nến t+1.
- "Bắt được sóng": tín hiệu cùng chiều nằm trong [start event, end event) của sóng và phần còn lại từ giá vào tới
  đỉnh/đáy kết thúc ≥ 0,3%. Mỗi sóng đếm tối đa 1 lần.
- Precision Long/Short: tỷ lệ tín hiệu "đúng" như trên. Tín hiệu trên nến UNKNOWN (filler + 30′) bị loại khỏi chấm.
- Tín hiệu sai chia theo nơi rơi: đi ngang / nhịp hồi / ngược sóng / muộn (cùng chiều nhưng còn < 0,3%).
- Precision ngẫu nhiên: trung bình 20 lần đặt cùng số tín hiệu Long/Short vào nến hợp lệ ngẫu nhiên; lift = precision / ngẫu nhiên.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from kh.ind.labels import DOWN, FLAT, PULLBACK, UNKNOWN, UP

MIN_REMAINING = 0.003


class WaveBook:
    """Đáp án của một symbol trong một khoảng [lo, hi) chỉ số nến."""

    def __init__(self, m1: pd.DataFrame, labels: np.ndarray, waves: pd.DataFrame, lo: int, hi: int):
        self.lo, self.hi = lo, hi
        n = len(m1)
        self.label = labels
        W = waves[(waves.start_idx >= lo) & (waves.end_idx < hi)].reset_index(drop=True)
        self.W = W
        self.wave_of = np.full(n, -1, np.int64)
        for j, (a, b) in enumerate(zip(W.start_idx.to_numpy(), W.end_idx.to_numpy())):
            self.wave_of[a:b] = j
        o = m1.open.to_numpy(np.float64)
        self.entry = np.append(o[1:], np.nan)
        self.dir = W.direction.to_numpy()
        self.end_px = W.end_px.to_numpy()
        self.start_px = W.start_px.to_numpy()
        self.start_idx = W.start_idx.to_numpy()
        self.fast = W.fast.to_numpy()
        valid = np.zeros(n, bool)
        valid[lo:hi] = True
        valid &= labels != UNKNOWN
        valid &= np.isfinite(self.entry)
        self.valid = valid
        w = self.wave_of
        has = w >= 0
        rem = np.full(n, np.nan)
        rem[has] = np.where(self.dir[w[has]] == 1, self.end_px[w[has]] / self.entry[has] - 1,
                            1 - self.end_px[w[has]] / self.entry[has])
        self.rem = rem
        self.good_long = valid & has & (np.where(has, self.dir[np.maximum(w, 0)], 0) == 1) & (rem >= MIN_REMAINING)
        self.good_short = valid & has & (np.where(has, self.dir[np.maximum(w, 0)], 0) == -1) & (rem >= MIN_REMAINING)
        self.valid_idx = np.flatnonzero(valid)

    def score(self, sig: np.ndarray, rng: np.random.Generator, n_random: int = 20) -> dict:
        s = np.where(self.valid, sig, 0)
        L, S = np.flatnonzero(s == 1), np.flatnonzero(s == -1)
        out = {"n_long": len(L), "n_short": len(S)}
        gl, gs = self.good_long[L], self.good_short[S]
        out["precision_long"] = gl.mean() if len(L) else np.nan
        out["precision_short"] = gs.mean() if len(S) else np.nan
        # sóng bắt được: sóng có ít nhất một tín hiệu đúng
        good = np.concatenate([L[gl], S[gs]])
        caught = np.unique(self.wave_of[good])
        W = self.W
        up, dn = self.dir == 1, self.dir == -1
        is_c = np.zeros(len(W), bool)
        is_c[caught] = True
        f = self.fast
        out["n_fast_up_waves"], out["n_fast_down_waves"], out["n_slow_waves"] = int((f & up).sum()), int((f & dn).sum()), int((~f).sum())
        out["recall_fast_up"] = is_c[f & up].mean() if (f & up).any() else np.nan
        out["recall_fast_down"] = is_c[f & dn].mean() if (f & dn).any() else np.nan
        out["recall_slow"] = is_c[~f].mean() if (~f).any() else np.nan
        out["recall_fast"] = is_c[f].mean() if f.any() else np.nan
        # độ trễ: tín hiệu đúng đầu tiên trong mỗi sóng bắt được
        if len(good):
            g = np.sort(good)
            wv = self.wave_of[g]
            first = g[np.unique(wv, return_index=True)[1]]
            fw = self.wave_of[first]
            lat_min = first - self.start_idx[fw]
            travelled = (self.entry[first] - self.start_px[fw]) / (self.end_px[fw] - self.start_px[fw])
            out["latency_min_median"] = float(np.median(lat_min))
            out["travelled_pct_median"] = float(np.median(travelled) * 100)
        else:
            out["latency_min_median"] = out["travelled_pct_median"] = np.nan
        # tín hiệu lặp cùng chiều trong sóng đã bắt
        same = np.concatenate([L[(self.wave_of[L] >= 0) & (self.dir[np.maximum(self.wave_of[L], 0)] == 1)],
                               S[(self.wave_of[S] >= 0) & (self.dir[np.maximum(self.wave_of[S], 0)] == -1)]])
        cnt = np.bincount(self.wave_of[same], minlength=len(W)) if len(same) else np.zeros(len(W), int)
        out["repeat_signals_per_caught_wave"] = float(np.mean(cnt[is_c] - 1)) if is_c.any() else np.nan
        # phân loại tín hiệu sai
        bad = np.concatenate([L[~gl], S[~gs]])
        side = np.concatenate([np.ones((~gl).sum()), -np.ones((~gs).sum())])
        if len(bad):
            lab = self.label[bad]
            wv = self.wave_of[bad]
            wdir = np.where(wv >= 0, self.dir[np.maximum(wv, 0)], 0)
            cat_flat = lab == FLAT
            cat_pull = (lab == PULLBACK) & ~cat_flat
            cat_counter = ~cat_flat & ~cat_pull & (wdir == -side)
            cat_late = ~cat_flat & ~cat_pull & (wdir == side)
            out["false_in_flat_share"] = cat_flat.mean()
            out["false_in_pullback_share"] = cat_pull.mean()
            out["false_counter_wave_share"] = cat_counter.mean()
            out["false_late_share"] = cat_late.mean()
            out["false_other_share"] = 1 - cat_flat.mean() - cat_pull.mean() - cat_counter.mean() - cat_late.mean()
        else:
            for k in ("flat", "pullback", "counter_wave", "late", "other"):
                out[f"false_{k}_share" if k not in ("flat", "pullback") else f"false_in_{k}_share"] = np.nan
        # chỉ số cấp nến
        idx = np.arange(self.lo, self.hi)
        idx = idx[self.valid[idx]]
        truth = np.where(self.label[idx] == UP, 1, np.where(self.label[idx] == DOWN, 2, 0))
        pred = np.where(s[idx] == 1, 1, np.where(s[idx] == -1, 2, 0))
        cm = np.zeros((3, 3))
        np.add.at(cm, (truth, pred), 1)
        tp = np.diag(cm)
        with np.errstate(invalid="ignore", divide="ignore"):
            prec, rec = tp / cm.sum(0), tp / cm.sum(1)
            f1 = 2 * prec * rec / (prec + rec)
        out["bar_macro_f1"] = float(np.nanmean(np.nan_to_num(f1)))
        out["bar_balanced_accuracy"] = float(np.nanmean(rec))
        # precision ngẫu nhiên cùng tần suất
        rl, rs = [], []
        for _ in range(n_random):
            if len(L):
                rl.append(self.good_long[rng.choice(self.valid_idx, len(L), replace=False)].mean())
            if len(S):
                rs.append(self.good_short[rng.choice(self.valid_idx, len(S), replace=False)].mean())
        out["random_precision_long"] = float(np.mean(rl)) if rl else np.nan
        out["random_precision_short"] = float(np.mean(rs)) if rs else np.nan
        out["lift_long"] = out["precision_long"] / out["random_precision_long"] if rl and out["random_precision_long"] > 0 else np.nan
        out["lift_short"] = out["precision_short"] / out["random_precision_short"] if rs and out["random_precision_short"] > 0 else np.nan
        return out

    def filter_lift(self, on: np.ndarray) -> dict:
        """Lift của filter: tỷ lệ nến thuộc sóng nhanh khi filter bật / tỷ lệ chung (nến hợp lệ)."""
        idx = self.valid_idx
        in_fast = (self.wave_of[idx] >= 0) & self.fast[np.maximum(self.wave_of[idx], 0)]
        o = np.asarray(on, bool)[idx]
        base = in_fast.mean()
        return {"filter_on_share": float(o.mean()), "fast_wave_share_when_on": float(in_fast[o].mean()) if o.any() else np.nan,
                "fast_wave_share_all": float(base), "filter_lift": float(in_fast[o].mean() / base) if o.any() and base > 0 else np.nan}
