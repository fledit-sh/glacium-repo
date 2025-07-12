import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import pytest

from glacium.utils import convergence
from glacium.jobs.analysis_jobs import ConvergenceStatsJob
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project
from glacium.managers.job_manager import JobManager
from glacium.models.job import JobStatus


def _setup_report(tmp_path):
    report = tmp_path / "run_FENSAP"
    report.mkdir()
    arr1 = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    arr2 = np.array([[2.0, 4.0], [4.0, 8.0], [6.0, 12.0]])
    for i, arr in enumerate((arr1, arr2), start=1):
        p = report / f"converg.fensap.{i:06d}"
        p.write_text("\n".join(" ".join(map(str, row)) for row in arr))
    means = np.vstack([arr1.mean(axis=0), arr2.mean(axis=0)])
    stds = np.vstack([arr1.std(axis=0), arr2.std(axis=0)])
    return report, tmp_path / "analysis", means, stds


def test_analysis_returns_expected_stats(tmp_path, monkeypatch):
    report, out_dir, exp_means, exp_stds = _setup_report(tmp_path)

    captured = {}

    def fake_plot(idx, means, stds, out, labels=None):
        captured["idx"] = list(idx)
        captured["means"] = means
        captured["stds"] = stds
        captured["labels"] = labels

    monkeypatch.setattr(convergence, "plot_stats", fake_plot)

    convergence.analysis(tmp_path, [report, out_dir])

    assert captured["idx"] == [1, 2]
    assert np.allclose(captured["means"], exp_means)
    assert np.allclose(captured["stds"], exp_stds)
    assert captured["labels"] == []


def test_convergence_stats_job_creates_plots(tmp_path):
    report, out_dir, _, _ = _setup_report(tmp_path)

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    project = Project("uid", tmp_path, cfg, paths, [])
    job = ConvergenceStatsJob(project)
    job.deps = ()
    project.jobs = [job]

    jm = JobManager(project)
    jm.run()

    assert job.status is JobStatus.DONE
    assert (out_dir / "column_00.png").exists()
    assert (out_dir / "column_01.png").exists()
