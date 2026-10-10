import pandas as pd

from kh.config import load_config
from kh.evaluation.wf import DAY, monthly_folds


def test_folds_no_overlap_and_exact_embargo():
    cfg = load_config()
    F = monthly_folds(cfg["splits"]["train"][0], cfg["splits"]["val"][1], 6, 1)
    assert len(F) >= 12
    val_end = int(pd.Timestamp(cfg["splits"]["val"][1], tz="UTC").value // 1_000_000) + DAY
    test_start = int(pd.Timestamp(cfg["splits"]["test"][0], tz="UTC").value // 1_000_000)
    for f in F:
        assert f.train_hi <= f.test_lo, "test chồng train"
        assert f.test_lo - f.train_hi == DAY, "embargo phải đúng 1 ngày"
        assert f.test_lo < f.test_hi <= val_end <= test_start, "fold không được chạm tập test khoá"
        assert (f.train_hi + DAY - f.train_lo) >= 180 * DAY, "train tối thiểu ~6 tháng"
    for a, b in zip(F, F[1:]):
        assert a.test_hi == b.test_lo, "các tháng kiểm tra nối tiếp, không chồng nhau"
        assert b.train_lo == a.train_lo and b.train_hi > a.train_hi, "train mở rộng"
        assert b.train_hi < b.test_lo and a.test_hi <= b.test_lo
    # mọi nến test của fold trước đều nằm trong train của fold sau (mở rộng) ngoại trừ ngày embargo
    for a, b in zip(F, F[1:]):
        assert a.test_lo >= b.train_lo and a.test_hi - DAY <= b.train_hi
