"""Job classes implementing FENSAP solver runs."""

from __future__ import annotations

from pathlib import Path

from glacium.managers.template_manager import TemplateManager

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
    batch_dir = None
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

    shot_templates = {
        "config.drop.j2": "config.drop.{idx}",
        "config.fensap.j2": "config.fensap.{idx}",
        "config.ice.j2": "config.ice.{idx}",
        "files.drop.j2": "files.drop.{idx}",
        "files.fensap.j2": "files.fensap.{idx}",
    }

    def __init__(self, project):
        super().__init__(project)

    def prepare(self):
        paths = self.project.paths
        work = paths.solver_dir(self.solver_dir)
        ctx = self._context()
        tm = TemplateManager()

        for tpl, dest in self.templates.items():
            tm.render_to_file(tpl, ctx, work / dest)

        count = self.project.config.get("MULTISHOT_COUNT", 10)
        timings = self.project.config.get("CASE_MULTISHOT")
        start = 0.0
        default_total = ctx.get("ICE_GUI_TOTAL_TIME")
        for i in range(1, count + 1):
            total = (
                timings[i - 1]
                if isinstance(timings, list) and i - 1 < len(timings)
                else default_total
            )
            shot_ctx = {
                **ctx,
                "shot_index": f"{i:06d}",
                "prev_shot_index": f"{i-1:06d}" if i > 1 else None,
                "next_shot_index": f"{i+1:06d}",
                "ICE_GUI_INITIAL_TIME": start,
                "ICE_GUI_TOTAL_TIME": total,
                "FSP_GUI_INITIAL_TYPE": 1 if i == 1 else 2,
                "DRP_GUI_INITIAL_TYPE": 1 if i == 1 else 2,
                "FSP_GUI_ROUGHNESS_TYPE": 1 if i == 1 else 4,
                "FSP_WALL_ROUGHNESS_SWITCH": 1 if i == 1 else 2,
            }
            if i == 1:
                shot_ctx.pop("FSP_MAX_LAPLACE_ITERATIONS", None)
                shot_ctx.pop("FSP_GUI_NO_TIMEBC", None)
            else:
                shot_ctx["FSP_MAX_LAPLACE_ITERATIONS"] = 3
                shot_ctx["FSP_GUI_NO_TIMEBC"] = 1
            start += total if total is not None else 0
            for tpl, name_fmt in self.shot_templates.items():
                dest_name = name_fmt.format(idx=f"{i:06d}")
                tm.render_to_file(tpl, shot_ctx, work / dest_name)

        return work / ".solvercmd"

    
