import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import pytest
from PyPDF2 import PdfReader

from glacium.utils import convergence
from glacium.jobs.analysis_jobs import ConvergenceStatsJob
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project
from glacium.managers.job_manager import JobManager
from glacium.models.job import JobStatus


@pytest.fixture
def report_dirs(tmp_path):
    report = tmp_path / "run_MULTISHOT"
    report.mkdir()
    arr1 = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    arr2 = np.array([[2.0, 4.0], [4.0, 8.0], [6.0, 12.0]])
    headers = ["# 1 lift coefficient   ", "# 1 drag coefficient   "]
    for i, arr in enumerate((arr1, arr2), start=1):
        p = report / f"converg.fensap.{i:06d}"
        lines = headers + [" ".join(map(str, row)) for row in arr]
        p.write_text("\n".join(lines))
    means = np.vstack([arr1.mean(axis=0), arr2.mean(axis=0)])
    stds = np.vstack([arr1.std(axis=0), arr2.std(axis=0)])
    return report, tmp_path / "analysis" / "MULTISHOT", means, stds


def test_analysis_returns_expected_stats(report_dirs, tmp_path, monkeypatch):
    report, out_dir, exp_means, exp_stds = report_dirs

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
    assert captured["labels"] == ["lift coefficient", "drag coefficient"]
    assert (out_dir / "cl_cd_stats.csv").exists()


def test_convergence_stats_job_creates_plots(report_dirs, tmp_path, monkeypatch):
    monkeypatch.setenv("FPDF_FONT_DIR", "/usr/share/fonts/truetype/dejavu")
    from fpdf import fpdf
    monkeypatch.setattr(fpdf, "FPDF_FONT_DIR", "/usr/share/fonts/truetype/dejavu", raising=False)
    report, out_dir, _, _ = report_dirs

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["CONVERGENCE_PDF"] = True
    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    project = Project("uid", tmp_path, cfg, paths, [])
    job = ConvergenceStatsJob(project)
    job.deps = ()
    project.jobs = [job]

    jm = JobManager(project)
    jm.run()

    assert job.status is JobStatus.DONE
    fig_dir = out_dir / "figures"
    assert (fig_dir / "column_00.png").exists()
    assert (fig_dir / "column_01.png").exists()
    assert (fig_dir / "cl_cd.png").exists()
    assert (fig_dir / "cl.png").exists()
    assert (fig_dir / "cd.png").exists()
    pdf_path = out_dir / "report.pdf"
    assert pdf_path.exists()
    reader = PdfReader(str(pdf_path))
    assert len(reader.pages) >= 1


def test_cl_cd_stats_returns_means(report_dirs):
    report, _, exp_means, _ = report_dirs

    stats = convergence.cl_cd_stats(report)
    expected = np.array([
        [1, exp_means[0, 0], exp_means[0, 1]],
        [2, exp_means[1, 0], exp_means[1, 1]],
    ])

    assert isinstance(stats, np.ndarray)
    assert stats.shape == (2, 3)
    assert np.allclose(stats, expected)
