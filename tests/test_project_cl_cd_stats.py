import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest

from glacium.utils.convergence import project_cl_cd_stats


def test_project_cl_cd_stats(tmp_path):
    report_dir = tmp_path / "report"
    report_dir.mkdir()

    data1 = np.array([
        [1.0, 2.0],
        [3.0, 4.0],
        [5.0, 6.0],
    ])
    data2 = np.array([
        [2.0, 4.0],
        [4.0, 8.0],
        [6.0, 12.0],
    ])

    lines = ["# 1 lift coefficient", "# 1 drag coefficient"]
    (report_dir / "converg.fensap.000001").write_text(
        "\n".join(lines + [" ".join(map(str, row)) for row in data1])
    )
    (report_dir / "converg.fensap.000002").write_text(
        "\n".join(lines + [" ".join(map(str, row)) for row in data2])
    )

    cl_mean, cl_std, cd_mean, cd_std = project_cl_cd_stats(report_dir, n=2)

    means1 = data1[-2:].mean(axis=0)
    stds1 = data1[-2:].std(axis=0)
    means2 = data2[-2:].mean(axis=0)
    stds2 = data2[-2:].std(axis=0)

    exp_cl_mean = np.mean([means1[0], means2[0]])
    exp_cl_std = np.mean([stds1[0], stds2[0]])
    exp_cd_mean = np.mean([means1[1], means2[1]])
    exp_cd_std = np.mean([stds1[1], stds2[1]])

    assert cl_mean == pytest.approx(exp_cl_mean)
    assert cl_std == pytest.approx(exp_cl_std)
    assert cd_mean == pytest.approx(exp_cd_mean)
    assert cd_std == pytest.approx(exp_cd_std)
