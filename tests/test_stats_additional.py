import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

from glacium.utils.solver_time import parse_time
from glacium.utils.convergence.stats import (
    execution_time,
    stats_last_n,
    cl_cd_summary,
    aggregate_report,
    project_cl_cd_stats,
)


given_hours = st.integers(min_value=0, max_value=23)
given_minutes = st.integers(min_value=0, max_value=59)
given_seconds = st.floats(min_value=0, max_value=59, allow_nan=False, allow_infinity=False)


@st.composite
def array2d(draw):
    rows = draw(st.integers(min_value=1, max_value=5))
    cols = draw(st.integers(min_value=1, max_value=4))
    return draw(arrays(np.float64, (rows, cols), elements=st.floats(0, 10)))

@given(given_hours, given_minutes, given_seconds)
def test_parse_time_property(h, m, s):
    value = f"{h:02d}:{m:02d}:{s:05.2f}"
    expected = h * 3600 + m * 60 + float(f"{s:05.2f}")
    assert parse_time(value) == pytest.approx(expected)


def test_execution_time(tmp_path):
    text = "\n".join([
        "random line",
        "total simulation = 00:01:00",
        "other",
        "total simulation = 00:02:30",
    ])
    f = tmp_path / "log.txt"
    f.write_text(text)
    assert execution_time(f) == pytest.approx(60.0)


@given(array2d())
def test_stats_last_n_property(data):
    mean, std = stats_last_n(data, n=1)
    assert np.allclose(mean, data[-1])
    assert np.all(std >= 0)


def test_summary_and_aggregate(tmp_path):
    report = tmp_path
    a = np.array([[1.0, 2.0], [3.0, 4.0]])
    b = np.array([[2.0, 4.0], [6.0, 8.0]])
    lines = ["# 1 lift coefficient", "# 1 drag coefficient"]
    (report / "converg.fensap.001").write_text("\n".join(lines + [" ".join(map(str, r)) for r in a]))
    (report / "converg.fensap.002").write_text("\n".join(lines + [" ".join(map(str, r)) for r in b]))

    summary = cl_cd_summary(report, n=2)
    idx, means, stds = aggregate_report(report, n=2)
    assert idx.tolist() == [1, 2]
    assert means.shape == stds.shape == (2, 2)
    assert summary[0] == pytest.approx(means[:,0].mean())
    assert summary[2] == pytest.approx(means[:,1].mean())


def test_cl_cd_stats_handles_bad_files(tmp_path):
    report = tmp_path
    (report / "converg.fensap.bad").write_text("# comment\n1 2")
    stats = cl_cd_summary(report, n=1)
    assert all(np.isnan(v) for v in stats)


def test_aggregate_and_project_missing_headers(tmp_path):
    report = tmp_path
    (report / "converg.fensap.xxx").write_text("1 2\n3 4")
    idx, means, stds = aggregate_report(report, n=1)
    assert idx.size == 1
    assert means.size == 2
    assert stds.size == 2
    summary = cl_cd_summary(report, n=1)
    assert all(np.isnan(v) for v in summary)
    project_stats = project_cl_cd_stats(report, n=1)
    assert all(np.isnan(v) for v in project_stats)
