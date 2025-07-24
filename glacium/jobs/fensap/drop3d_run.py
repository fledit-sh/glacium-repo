from __future__ import annotations

from glacium.engines import FensapScriptJob


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
