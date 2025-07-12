import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from glacium.utils.convergence import cl_cd_stats


def test_cl_cd_stats(tmp_path):
    report = tmp_path / "report"
    report.mkdir()
    # first file
    content1 = "\n".join([
        "# 1 lift coefficient",
        "# 1 drag coefficient",
        "1 2",
        "3 4",
        "5 6",
    ])
    (report / "converg.fensap.000001").write_text(content1)

    content2 = "\n".join([
        "# 1 lift coefficient",
        "# 1 drag coefficient",
        "0.5 1.5",
        "1.0 2.0",
    ])
    (report / "converg.fensap.000002").write_text(content2)

    stats = cl_cd_stats(report, n=2)
    assert isinstance(stats, np.ndarray)
    assert stats.shape == (2, 3)
    assert np.allclose(stats[0], [1, 4.0, 5.0])
    assert np.allclose(stats[1], [2, 0.75, 1.75])

