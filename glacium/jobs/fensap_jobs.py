"""Job classes implementing FENSAP solver runs."""

from __future__ import annotations

from pathlib import Path

from glacium.engines import FensapScriptJob, Fluent2FensapJob

__all__ = [
    "FensapRunJob",
    "Drop3dRunJob",
    "Ice3dRunJob",
    "MultiShotRunJob",
    "Fluent2FensapJob",
]


class FensapRunJob(FensapScriptJob):
    """Render FENSAP input files and launch the solver."""

    name = "FENSAP_RUN"
    deps = ("FLUENT2FENSAP",)
    solver_dir = "run_FENSAP"
    templates = {
        "FENSAP.FENSAP.files.j2": "files",
        "FENSAP.FENSAP.par.j2": "fensap.par",
        "FENSAP.FENSAP.solvercmd.j2": ".solvercmd",
    }


class Drop3dRunJob(FensapScriptJob):
    """Render DROP3D input files and launch the solver."""

    name = "DROP3D_RUN"
    deps = ("FENSAP_RUN",)
    solver_dir = "run_DROP3D"
    templates = {
        "FENSAP.DROP3D.files.j2": "files",
        "FENSAP.DROP3D.par.j2": "drop3d.par",
        "FENSAP.DROP3D.solvercmd.j2": ".solvercmd",
    }


class Ice3dRunJob(FensapScriptJob):
    """Render ICE3D input files and launch the solver."""

    name = "ICE3D_RUN"
    deps = ("DROP3D_RUN",)
    solver_dir = "run_ICE3D"
    templates = {
        "FENSAP.ICE3D.custom_remeshing.sh.j2": "custom_remeshing.sh",
        "FENSAP.ICE3D.remeshing.jou.j2": "remeshing.jou",
        "FENSAP.ICE3D.fluent_config.jou.j2": "fluent_config.jou",
        "FENSAP.ICE3D.meshingSizes.scm.j2": "meshingSizes.scm",
        "FENSAP.ICE3D.par.j2": "ice.par",
        "FENSAP.ICE3D.solvercmd.j2": ".solvercmd",
    }


class MultiShotRunJob(FensapScriptJob):
    """Render MULTISHOT input files and launch the solver."""

    name = "MULTISHOT_RUN"
    deps = ("FLUENT2FENSAP",)
    solver_dir = "run_MULTISHOT"
    batch_dir = Path("MULTISHOT10")
    templates = {
        "MULTISHOT.meshingSizes.scm.j2": "meshingSizes.scm",
        "MULTISHOT.custom_remeshing.sh.j2": "custom_remeshing.sh",
        "MULTISHOT.solvercmd.j2": ".solvercmd",
        "MULTISHOT.files.j2": "files",
        "MULTISHOT.config.par.j2": "config.par",
        "MULTISHOT.fensap.par.j2": "fensap.par",
        "MULTISHOT.drop.par.j2": "drop.par",
        "MULTISHOT.ice.par.j2": "ice.par",
        "MULTISHOT.create-2.5D-mesh.bin.j2": "create-2.5D-mesh.bin",
        "MULTISHOT.remeshing.jou.j2": "remeshing.jou",
        "MULTISHOT.fluent_config.jou.j2": "fluent_config.jou",
    }


