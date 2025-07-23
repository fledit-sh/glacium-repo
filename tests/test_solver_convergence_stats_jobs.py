import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import csv
import yaml
import pytest
from PyPDF2 import PdfReader

from glacium.jobs.analysis_jobs import (
    FensapConvergenceStatsJob,
    Drop3dConvergenceStatsJob,
    Ice3dConvergenceStatsJob,
)
from glacium.utils import normalise_key
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project
from glacium.managers.job_manager import JobManager
from glacium.models.job import JobStatus


@pytest.mark.parametrize(
    "job_cls, solver_dir, filename",
    [
        (FensapConvergenceStatsJob, "run_FENSAP", "converg"),
        (Drop3dConvergenceStatsJob, "run_DROP3D", "converg"),
        (Ice3dConvergenceStatsJob, "run_ICE3D", "iceconv.dat"),
    ],
)
def test_solver_convergence_stats_jobs(tmp_path, job_cls, solver_dir, filename, monkeypatch):
    monkeypatch.setenv("FPDF_FONT_DIR", "/usr/share/fonts/truetype/dejavu")
    from fpdf import fpdf
    monkeypatch.setattr(fpdf, "FPDF_FONT_DIR", "/usr/share/fonts/truetype/dejavu", raising=False)
    run_dir = tmp_path / solver_dir
    run_dir.mkdir()
    conv_file = run_dir / filename

    data = np.array([
        [1.0, 2.0],
        [3.0, 4.0],
        [5.0, 6.0],
        [7.0, 8.0],
        [9.0, 10.0],
    ])
    labels = ["lift coefficient", "drag coefficient"]
    lines = [f"# 1 {labels[0]}", f"# 2 {labels[1]}"]
    lines += [" ".join(map(str, row)) for row in data]
    conv_file.write_text("\n".join(lines))

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["CONVERGENCE_PDF"] = True
    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    project = Project("uid", tmp_path, cfg, paths, [])
    job = job_cls(project)
    job.deps = ()
    project.jobs = [job]

    jm = JobManager(project)
    jm.run()

    assert job.status is JobStatus.DONE
    suffix = {
        FensapConvergenceStatsJob: "FENSAP",
        Drop3dConvergenceStatsJob: "DROP3D",
        Ice3dConvergenceStatsJob: "ICE3D",
    }[job_cls]
    out_dir = tmp_path / "analysis" / suffix
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
    stats_file = out_dir / "stats.csv"
    assert stats_file.exists()

    with stats_file.open() as fh:
        rows = list(csv.DictReader(fh))

    expected_mean = data.mean(axis=0)
    expected_var = data.var(axis=0)

    assert len(rows) == 2
    assert rows[0]["label"] == labels[0]
    assert float(rows[0]["mean"]) == pytest.approx(expected_mean[0])
    assert float(rows[0]["variance"]) == pytest.approx(expected_var[0])
    assert rows[1]["label"] == labels[1]
    assert float(rows[1]["mean"]) == pytest.approx(expected_mean[1])
    assert float(rows[1]["variance"]) == pytest.approx(expected_var[1])
    assert (out_dir / "cl_cd_stats.csv").exists()

    results_file = tmp_path / "results.yaml"
    if job_cls is FensapConvergenceStatsJob:
        assert results_file.exists()
        data_yaml = yaml.safe_load(results_file.read_text()) or {}
        assert data_yaml[normalise_key(labels[0])] == pytest.approx(expected_mean[0])
        assert data_yaml[normalise_key(labels[1])] == pytest.approx(expected_mean[1])
    else:
        assert not results_file.exists()
