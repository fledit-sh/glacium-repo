"""Job classes implementing FENSAP solver runs."""

from __future__ import annotations

import yaml
from pathlib import Path

from glacium.engines import Fluent2FensapJob
from glacium.models.job import Job
from glacium.managers.template_manager import TemplateManager
from glacium.utils.logging import log
from glacium.engines.fensap import FensapEngine


class FensapRunJob(Job):
    """Render FENSAP input files and launch the solver."""

    name = "FENSAP_RUN"
    deps: tuple[str, ...] = ()

    _DEFAULT_EXE = (
        r"C:\\Program Files\\ANSYS Inc\\v251\\fensapice\\bin\\nti_sh.exe"
    )

    def execute(self) -> None:  # noqa: D401
        cfg = self.project.config
        paths = self.project.paths
        work = paths.solver_dir("run_FENSAP")

        defaults_file = (
            Path(__file__).resolve().parents[1]
            / "config"
            / "defaults"
            / "global_default.yaml"
        )
        defaults = yaml.safe_load(defaults_file.read_text()) if defaults_file.exists() else {}

        ctx = {**defaults, **cfg.extras}

        tm = TemplateManager()
        tm.render_to_file("FENSAP.FENSAP.files.j2", ctx, work / "files")
        tm.render_to_file("FENSAP.FENSAP.par.j2", ctx, work / "fensap.par")
        tm.render_to_file("FENSAP.FENSAP.solvercmd.j2", ctx, work / ".solvercmd")

        exe = cfg.get("FENSAP_EXE", self._DEFAULT_EXE)
        engine = FensapEngine()
        engine.run_script(exe, work / ".solvercmd", work)


class Drop3dRunJob(Job):
    """Render DROP3D input files and launch the solver."""

    name = "DROP3D_RUN"
    deps: tuple[str, ...] = ()

    _DEFAULT_EXE = (
        r"C:\\Program Files\\ANSYS Inc\\v251\\fensapice\\bin\\nti_sh.exe"
    )

    def execute(self) -> None:  # noqa: D401
        cfg = self.project.config
        paths = self.project.paths
        work = paths.solver_dir("run_DROP3D")

        defaults_file = (
            Path(__file__).resolve().parents[1]
            / "config"
            / "defaults"
            / "global_default.yaml"
        )
        defaults = (
            yaml.safe_load(defaults_file.read_text()) if defaults_file.exists() else {}
        )

        ctx = {**defaults, **cfg.extras}

        tm = TemplateManager()
        tm.render_to_file("FENSAP.DROP3D.files.j2", ctx, work / "files")
        tm.render_to_file("FENSAP.DROP3D.par.j2", ctx, work / "drop3d.par")
        tm.render_to_file("FENSAP.DROP3D.solvercmd.j2", ctx, work / ".solvercmd")

        exe = cfg.get("FENSAP_EXE", self._DEFAULT_EXE)
        engine = FensapEngine()
        engine.run_script(exe, work / ".solvercmd", work)


class Ice3dRunJob(Job):
    """Render ICE3D input files and launch the solver."""

    name = "ICE3D_RUN"
    deps: tuple[str, ...] = ()

    _DEFAULT_EXE = (
        r"C:\\Program Files\\ANSYS Inc\\v251\\fensapice\\bin\\nti_sh.exe"
    )

    def execute(self) -> None:  # noqa: D401
        cfg = self.project.config
        paths = self.project.paths
        work = paths.solver_dir("run_ICE3D")

        defaults_file = (
            Path(__file__).resolve().parents[1]
            / "config"
            / "defaults"
            / "global_default.yaml"
        )
        defaults = (
            yaml.safe_load(defaults_file.read_text()) if defaults_file.exists() else {}
        )

        ctx = {**defaults, **cfg.extras}

        tm = TemplateManager()
        tm.render_to_file("FENSAP.ICE3D.custom_remeshing.sh.j2", ctx, work / "custom_remeshing.sh")
        tm.render_to_file("FENSAP.ICE3D.remeshing.jou.j2", ctx, work / "remeshing.jou")
        tm.render_to_file("FENSAP.ICE3D.meshingSizes.scm.j2", ctx, work / "meshingSizes.scm")
        tm.render_to_file("FENSAP.ICE3D.files.j2", ctx, work / "files")
        tm.render_to_file("FENSAP.ICE3D.par.j2", ctx, work / "ice.par")
        tm.render_to_file("FENSAP.ICE3D.solvercmd.j2", ctx, work / ".solvercmd")

        exe = cfg.get("FENSAP_EXE", self._DEFAULT_EXE)
        engine = FensapEngine()
        engine.run_script(exe, work / ".solvercmd", work)


class MultiShotRunJob(Job):
    """Render MULTISHOT input files and launch the solver."""

    name = "MULTISHOT_RUN"
    deps: tuple[str, ...] = ()

    _DEFAULT_EXE = (
        r"C:\\Program Files\\ANSYS Inc\\v251\\fensapice\\bin\\nti_sh.exe"
    )

    def execute(self) -> None:  # noqa: D401
        cfg = self.project.config
        paths = self.project.paths
        work = paths.solver_dir("run_MULTISHOT")

        defaults_file = (
            Path(__file__).resolve().parents[1]
            / "config"
            / "defaults"
            / "global_default.yaml"
        )
        defaults = (
            yaml.safe_load(defaults_file.read_text()) if defaults_file.exists() else {}
        )

        ctx = {**defaults, **cfg.extras}

        tm = TemplateManager()
        template_root = Path(__file__).resolve().parents[1] / "templates"
        batch_root = template_root / "MULITSHOT10"
        rel_paths = [p.relative_to(template_root) for p in batch_root.glob("*.j2")]
        tm.render_batch(rel_paths, ctx, work)
        tm.render_to_file("MULTISHOT.meshingSizes.scm.j2", ctx, work / "meshingSizes.scm")
        tm.render_to_file("MULTISHOT.custom_remeshing.sh.j2", ctx, work / "custom_remeshing.sh")
        tm.render_to_file("MULTISHOT.solvercmd.j2", ctx, work / ".solvercmd")
        tm.render_to_file("MULTISHOT.files.j2", ctx, work / "files")
        tm.render_to_file("MULTISHOT.config.par.j2", ctx, work / "config.par")
        tm.render_to_file("MULTISHOT.fensap.par.j2", ctx, work / "fensap.par")
        tm.render_to_file("MULTISHOT.drop.par.j2", ctx, work / "drop.par")
        tm.render_to_file("MULTISHOT.ice.par.j2", ctx, work / "ice.par")
        tm.render_to_file("MULTISHOT.create-2.5D-mesh.bin.j2", ctx, work / "create-2.5D-mesh.bin")
        tm.render_to_file("MULTISHOT.remeshing.jou.j2", ctx, work / "remeshing.jou")
        tm.render_to_file("MULTISHOT.fluent_config.jou.j2", ctx, work / "fluent_config.jou")
        exe = cfg.get("FENSAP_EXE", self._DEFAULT_EXE)
        engine = FensapEngine()
        engine.run_script(exe, work / ".solvercmd", work)


__all__ = [
    "FensapRunJob",
    "Drop3dRunJob",
    "Ice3dRunJob",
    "MultiShotRunJob",
]
