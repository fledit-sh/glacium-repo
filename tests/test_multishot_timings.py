import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.jobs import fensap_jobs
from glacium.jobs.fensap_jobs import MultiShotRunJob
from glacium.managers.template_manager import TemplateManager
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project


def test_multishot_timings(monkeypatch, tmp_path):
    template_root = tmp_path / "templates"
    template_root.mkdir()
    monkeypatch.setattr(fensap_jobs, "__file__", str(tmp_path / "pkg" / "fensap_jobs.py"))

    # minimal required templates
    names = [
        "MULTISHOT.meshingSizes.scm.j2",
        "MULTISHOT.custom_remeshing.sh.j2",
        "MULTISHOT.solvercmd.j2",
        "MULTISHOT.files.j2",
        "MULTISHOT.config.par.j2",
        "MULTISHOT.fensap.par.j2",
        "MULTISHOT.drop.par.j2",
        "MULTISHOT.ice.par.j2",
        "MULTISHOT.create-2.5D-mesh.bin.j2",
        "MULTISHOT.remeshing.jou.j2",
        "MULTISHOT.fluent_config.jou.j2",
        "config.fensap.j2",
        "config.drop.j2",
        "files.drop.j2",
        "files.fensap.j2",
    ]
    for n in names:
        content = "exit 0" if n == "MULTISHOT.solvercmd.j2" else "x"
        (template_root / n).write_text(content)

    # template under test prints timing values
    (template_root / "config.ice.j2").write_text("{{ ICE_GUI_INITIAL_TIME }} {{ ICE_GUI_TOTAL_TIME }}")

    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    cfg["FENSAP_EXE"] = "sh"
    cfg["MULTISHOT_COUNT"] = 3
    cfg["CASE_MULTISHOT"] = [1, 2, 3]

    paths = PathBuilder(tmp_path).build()
    paths.ensure()
    TemplateManager(template_root)

    project = Project("uid", tmp_path, cfg, paths, [])
    job = MultiShotRunJob(project)
    job.execute()

    work = paths.solver_dir("run_MULTISHOT")
    expect = [
        (0, 1),
        (1, 2),
        (3, 3),
    ]
    for i, pair in enumerate(expect, 1):
        idx = f"{i:06d}"
        text = (work / f"config.ice.{idx}").read_text().strip()
        nums = [float(x) for x in text.split()]
        assert nums == [float(pair[0]), float(pair[1])]

