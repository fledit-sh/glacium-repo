from __future__ import annotations

from glacium.engines import FensapScriptJob


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
