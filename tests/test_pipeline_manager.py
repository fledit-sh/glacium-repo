import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fpdf import FPDF
from PyPDF2 import PdfReader

from glacium.managers.project_manager import ProjectManager
from glacium.managers.job_manager import JobManager
from glacium.pipelines import PipelineManager
from glacium.cli import update as cli_update


def _fake_run(self, jobs=None):
    level = int(self.project.config.get("PWS_REFINEMENT", 1))
    run_dir = self.project.root / "run_FENSAP"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "converg.fensap.000001").write_text(f"1 {level}\n1 {level}")
    out_dir = self.project.root / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, str(level))
    pdf.output(str(out_dir / "report.pdf"))


def test_pipeline_manager(tmp_path, monkeypatch):
    counter = 0

    def fake_uid(name: str) -> str:
        nonlocal counter
        counter += 1
        return f"20000101-000000-000000-{counter:04X}"

    monkeypatch.setattr(ProjectManager, "_uid", staticmethod(fake_uid))
    monkeypatch.setattr(JobManager, "run", _fake_run)

    pm = ProjectManager(tmp_path / "runs")
    monkeypatch.setattr(cli_update, "ROOT", pm.runs_root)
    monkeypatch.chdir(tmp_path)
    pipe = PipelineManager.create("grid-convergence")
    uids, stats = pipe.run(pm, levels=(1, 2))

    for idx, uid in enumerate(uids):
        assert (pm.runs_root / uid).exists()
        pdf = pm.runs_root / uid / "analysis" / "report.pdf"
        if idx < 2:  # grid projects were executed
            assert pdf.exists()
        else:
            assert not pdf.exists()

    out = pipe.merge_pdfs(pm, uids, stats)
    assert out.exists()

    expected_pages = 1
    for uid in uids[:2]:
        reader = PdfReader(str(pm.runs_root / uid / "analysis" / "report.pdf"))
        expected_pages += len(reader.pages)
    merged = PdfReader(str(out))
    assert len(merged.pages) == expected_pages
