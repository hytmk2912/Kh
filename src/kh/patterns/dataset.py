"""Nạp bảng mẫu (đặc trưng + nhãn) và gán tập train/val/test có purge + embargo."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from kh.config import split_ms


def load_samples(cfg: dict, P) -> pd.DataFrame:
    D = pd.concat([pd.read_parquet(P.work / "features" / f"{s}.parquet") for s in cfg["symbols"]],
                  ignore_index=True)
    D["day"] = (D.open_time_ms // 86_400_000).astype("int64")
    emb = cfg["splits"]["embargo_minutes"] * 60_000
    hmax = max(cfg["labels"]["horizons_min"])
    end = D[f"label_end_ms_{hmax}"]
    t = D.open_time_ms
    split = np.full(len(D), "gap", dtype=object)
    for name in ("train", "val", "test"):
        lo, hi = split_ms(cfg, name)
        lo = lo if name == "train" else lo + emb
        m = (t >= lo) & (t < hi)
        if name != "test":
            m &= end <= hi  # purge: nhãn phải hoàn tất trong cùng tập
        split[m.to_numpy()] = name
    D["split"] = split
    D["trend_regime"] = np.where(D.ret_1440_z > 1, "up", np.where(D.ret_1440_z < -1, "down", "range"))
    D["vol_regime"] = np.where(D.vol_ratio_30d > 1.25, "high", np.where(D.vol_ratio_30d < 0.8, "low", "normal"))
    return D


def feature_list(P) -> list[str]:
    """Danh sách đặc trưng do stage `features` ghi ra (không gồm cột kiểm soát chất lượng)."""
    with open(P.work / "features" / "feature_list.json") as f:
        return json.load(f)["features"]


def valid_mask(D: pd.DataFrame, H: int) -> pd.Series:
    """Loại mẫu bị ảnh hưởng bởi nến filler (bảo trì) và mẫu không có nhãn."""
    return (D.filler_last_60 == 0) & (~D[f"filler_in_h_{H}"].astype(bool)) & D[f"label_{H}"].notna()
