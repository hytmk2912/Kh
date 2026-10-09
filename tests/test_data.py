import io
import zipfile

import numpy as np
import pandas as pd

from conftest import synth_klines
from kh.data import normalize as N
from kh.data.quality import check_klines, runs


def test_filler_flag_and_runs():
    k = synth_klines(500, filler_at=(100, 130))
    assert k.is_filler.sum() == 30
    r = runs(k.is_filler.to_numpy(), k.open_time_ms.to_numpy())
    assert len(r) == 1 and r[0]["minutes"] == 30


def test_quality_detects_problems(cfg):
    k = synth_klines(2000)
    lo = int(k.open_time_ms.iloc[0])
    c = dict(cfg)
    c["window"] = {"start": "2025-01-01", "end": "2025-01-01"}
    k = k.iloc[:1440].copy()
    k.loc[10, "high"] = k.loc[10, "low"] - 1          # OHLC sai
    k = k.drop(index=[20, 21])                          # thiếu 2 phút
    k = pd.concat([k, k.iloc[[5]]])
    q = check_klines(k.sort_values("open_time_ms"), c)
    assert q["ohlc_violations"] >= 1
    assert q["missing_minutes"] == 2
    assert q["duplicate_timestamps"] == 1
    assert lo == int(k.open_time_ms.min())


def test_read_zip_with_and_without_header(tmp_path):
    rows = "1735689600000,1,2,0.5,1.5,10,1735689659999,15,3,4,6,0\n"
    for name, content in [("h.zip", ",".join(N.KLINE_COLS) + "\n" + rows), ("n.zip", rows)]:
        p = tmp_path / name
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("x.csv", content)
        df = N._read_zip_csv(p, N.KLINE_COLS)
        assert list(df.columns) == N.KLINE_COLS
        assert df.open_time.iloc[0] == 1735689600000


def test_microsecond_timestamps_converted():
    import pandas as pd

    s = pd.Series([1735689600000000, 1735689600000])
    assert np.all(N._to_ms(s) == 1735689600000)
