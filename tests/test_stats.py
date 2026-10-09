import numpy as np
import pandas as pd

from kh.patterns.stats import ecdf_transform, fdr_by, ic_daily_products, nw_tstat


def _random_walk(seed, days=300):
    rng = np.random.default_rng(seed)
    n = 1440 * days
    lp = pd.Series(np.cumsum(rng.normal(0, 1e-3, n)))
    df = pd.DataFrame({"ret1440": lp - lp.shift(1440), "ret15": lp - lp.shift(15),
                       "fwd60": lp.shift(-61) - lp.shift(-1), "day": np.arange(n) // 1440})
    return df.iloc[1440::15].dropna()


def test_pooled_ic_unbiased_on_random_walk():
    """Hồi quy cho lỗi đã gặp: IC trong ngày cho t ≈ −20 trên bước ngẫu nhiên."""
    for seed in (0, 1):
        d = ic_daily_products(_random_walk(seed), ["ret1440", "ret15"], "fwd60")
        for c in d:
            assert abs(nw_tstat(d[c], 10)[1]) < 3.5


def test_fdr_by_controls():
    p = np.concatenate([np.full(5, 1e-6), np.linspace(0.2, 1, 95)])
    rej = fdr_by(p, 0.1)
    assert rej[:5].all() and not rej[5:].any()


def test_ecdf_uses_train_only():
    tr = np.arange(100.0)
    assert np.isclose(ecdf_transform(tr, np.array([49.5]))[0], 0.0)
    assert np.isnan(ecdf_transform(tr, np.array([np.nan]))[0])
