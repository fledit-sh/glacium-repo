from __future__ import annotations

from glacium.engines import FensapScriptJob


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
