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

    _DEFAULT_PAR_TEMPLATE = "FENSAP.FENSAP.par.j2"
    _ICED_PAR_TEMPLATE = "FENSAP.ICEDSWEEP.par.j2"
    _DEFAULT_FILES_TEMPLATE = "FENSAP.FENSAP.files.j2"
    _ICED_FILES_TEMPLATE = "FENSAP.ICEDSWEEP.files.j2"

    def _template_mapping(self):
        mapping = dict(super()._template_mapping())
        selected_par_template = self._par_template_name()
        use_iced_templates = self._use_iced_templates(selected_par_template)

        par_dest = mapping.pop(
            self._DEFAULT_PAR_TEMPLATE,
            self.templates.get(self._DEFAULT_PAR_TEMPLATE, "fensap.par"),
        )
        if selected_par_template != self._DEFAULT_PAR_TEMPLATE:
            par_dest = mapping.pop(selected_par_template, par_dest)
        mapping[selected_par_template] = par_dest

        selected_files_template = (
            self._ICED_FILES_TEMPLATE if use_iced_templates else self._DEFAULT_FILES_TEMPLATE
        )
        files_dest = mapping.pop(
            self._DEFAULT_FILES_TEMPLATE,
            self.templates.get(self._DEFAULT_FILES_TEMPLATE, "files"),
        )
        if selected_files_template != self._DEFAULT_FILES_TEMPLATE:
            files_dest = mapping.pop(selected_files_template, files_dest)
        mapping[selected_files_template] = files_dest

        return mapping

    def _par_template_name(self) -> str:
        cfg = self.project.config
        override = cfg.get("FENSAP_PAR_TEMPLATE")
        if override:
            return override

        if cfg.get("FSP_FILE_VARIABLE_ROUGHNESS"):
            return self._ICED_PAR_TEMPLATE

        return self._DEFAULT_PAR_TEMPLATE

    def _use_iced_templates(self, par_template: str | None = None) -> bool:
        cfg = self.project.config
        if cfg.get("FSP_FILE_VARIABLE_ROUGHNESS"):
            return True

        if par_template is None:
            par_template = self._par_template_name()

        return par_template == self._ICED_PAR_TEMPLATE


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
        "FENSAP.ICE3D.create-2.5D-mesh.bin.j2": "create-2.5D-mesh.bin",
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

        timings = self.project.config.get("CASE_MULTISHOT")
        if not isinstance(timings, list) or not timings:
            timings = [ctx.get("ICE_GUI_TOTAL_TIME")]
        count = len(timings)
        start = 0.0
        for i in range(1, count + 1):
            total = timings[i - 1]
            shot_ctx = {
                **ctx,
                "shot_index": f"{i:06d}",
                "prev_shot_index": f"{i-1:06d}" if i > 1 else None,
                "next_shot_index": f"{i+1:06d}",
                "ICE_GUI_INITIAL_TIME": start,
                "ICE_GUI_TOTAL_TIME": total,
                "ICE_NUMBER_TIME_STEP": int(total * 1000),
                "ICE_GUI_TIME_BETWEEN_OUTPUT": total,
                "ICE_TIME_STEP_BETWEEN_OUTPUT": int(total * 1000),
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

    
