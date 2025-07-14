import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import re
import yaml
from click.testing import CliRunner

from glacium.cli import cli
from glacium.managers.project_manager import ProjectManager
from glacium.managers.job_manager import JobManager


def _fake_run(self, jobs=None):
    level = int(self.project.config.get("PWS_REFINEMENT", 1))
    run_dir = (
        self.project.root
        / ("run_MULTISHOT" if self.project.config.recipe == "multishot" else "run_FENSAP")
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 1 lift coefficient",
        "# 1 drag coefficient",
        f"1 {level}",
        f"1 {level}",
    ]
    (run_dir / "converg.fensap.000001").write_text("\n".join(lines))
    out_dir = self.project.root / "analysis" / ("MULTISHOT" if self.project.config.recipe == "multishot" else "FENSAP")
    out_dir.mkdir(parents=True, exist_ok=True)
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, str(level))
    pdf.output(str(out_dir / "report.pdf"))


def test_cli_pipeline(tmp_path, monkeypatch):
    counter = 0

    def fake_uid(name: str) -> str:
        nonlocal counter
        counter += 1
        return f"20000101-000000-000000-{counter:04X}"

    monkeypatch.setattr(ProjectManager, "_uid", staticmethod(fake_uid))
    monkeypatch.setattr(JobManager, "run", _fake_run)

    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli,
            [
                "pipeline",
                "--layout",
                "grid-convergence",
                "--level",
                "1",
                "--level",
                "2",
                "--multishot",
                "[10,20]",
                "--pdf",
            ],
            env=env,
        )
        assert result.exit_code == 0
        lines = [l.strip() for l in result.output.splitlines()]
        assert any("Best grid" in l for l in lines)

        uids = [l for l in lines if re.match(r"\d{8}-\d{6}-\d{6}-[0-9A-F]{4}", l)]
        assert len(uids) == 4

        single_uid = uids[2]
        ms_uid = uids[3]

        case_single = yaml.safe_load(
            (Path("runs") / single_uid / "case.yaml").read_text()
        )
        case_ms = yaml.safe_load((Path("runs") / ms_uid / "case.yaml").read_text())

        assert case_single["PWS_REFINEMENT"] == 1
        assert case_ms["PWS_REFINEMENT"] == 1
        assert case_ms["CASE_MULTISHOT"] == [10, 20]

        cfg_ms = yaml.safe_load(
            (Path("runs") / ms_uid / "_cfg" / "global_config.yaml").read_text()
        )
        assert cfg_ms["RECIPE"] == "multishot"
        assert (Path("runs") / single_uid / "run_FENSAP").exists()
        assert (Path("runs") / ms_uid / "run_MULTISHOT").exists()

        summary = Path("runs_summary.pdf")
        assert summary.exists()


def test_cli_pipeline_no_pdf(tmp_path, monkeypatch):
    counter = 0

    def fake_uid(name: str) -> str:
        nonlocal counter
        counter += 1
        return f"20000101-000000-000000-{counter:04X}"

    monkeypatch.setattr(ProjectManager, "_uid", staticmethod(fake_uid))
    monkeypatch.setattr(JobManager, "run", _fake_run)

    runner = CliRunner()
    env = {"HOME": str(tmp_path)}

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli,
            [
                "pipeline",
                "--layout",
                "grid-convergence",
                "--level",
                "1",
                "--level",
                "2",
                "--multishot",
                "[10,20]",
                "--no-pdf",
            ],
            env=env,
        )
        assert result.exit_code == 0
        summary = Path("runs_summary.pdf")
        assert not summary.exists()
