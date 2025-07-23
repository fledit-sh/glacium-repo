from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Dict, Any
import shutil
import yaml

from glacium.utils.JobIndex import JobFactory
from glacium.utils import generate_global_defaults, global_default_config

from glacium.managers.config_manager import ConfigManager
from glacium.managers.project_manager import ProjectManager
from glacium.managers.job_manager import JobManager
from glacium.models.project import Project as ModelProject

__all__ = ["Project"]


class Project:
    """Runtime helper around :class:`~glacium.models.project.Project`."""

    def __init__(self, source: ModelProject) -> None:
        super().__setattr__("_project", source)

    # ------------------------------------------------------------------
    # Config access
    # ------------------------------------------------------------------
    def set(self, key: str, value: Any) -> "Project":
        """Update a configuration parameter."""

        cfg_mgr = ConfigManager(self._project.paths)
        case_file = self._project.root / "case.yaml"
        case_data: Dict[str, Any] = {}
        if case_file.exists():
            case_data = yaml.safe_load(case_file.read_text()) or {}

        global_cfg = cfg_mgr.load_global()

        ukey = key.upper()
        if ukey in {k.upper() for k in case_data.keys()}:
            case_data[ukey] = value
            case_file.write_text(yaml.safe_dump(case_data, sort_keys=False))
            defaults = generate_global_defaults(case_file, global_default_config())
            global_cfg.extras.update(defaults)
        elif ukey not in global_cfg.extras and ukey not in {"PROJECT_UID", "BASE_DIR", "RECIPE"}:
            raise KeyError(key)

        global_cfg[ukey] = value
        cfg_mgr.dump_global()
        self._project.config = global_cfg
        return self

    def get(self, key: str) -> Any:
        """Return value for ``key`` from case data or the global configuration."""

        ukey = key.upper()
        cfg_mgr = ConfigManager(self._project.paths)
        case_file = self._project.root / "case.yaml"
        case_data: Dict[str, Any] = {}
        if case_file.exists():
            case_data = yaml.safe_load(case_file.read_text()) or {}

        case_map = {k.upper(): v for k, v in case_data.items()}
        if ukey in case_map:
            return case_map[ukey]

        cfg = cfg_mgr.load_global()

        if ukey == "PROJECT_UID":
            return cfg.project_uid
        if ukey == "BASE_DIR":
            return cfg.base_dir
        if ukey == "RECIPE":
            return cfg.recipe
        if ukey in cfg.extras:
            return cfg.extras[ukey]

        res_file = self._project.root / "results.yaml"
        res_data: Dict[str, Any] = {}
        if res_file.exists():
            res_data = yaml.safe_load(res_file.read_text()) or {}

        res_map = {k.upper(): v for k, v in res_data.items()}
        if ukey in res_map:
            return res_map[ukey]

        raise KeyError(key)

    def set_bulk(self, data: Dict[str, Any]) -> "Project":
        for k, v in data.items():
            self.set(k, v)
        return self

    # ------------------------------------------------------------------
    # Job management
    # ------------------------------------------------------------------
    def add_job(self, name: str):
        proj = self._project
        if proj.job_manager is None:
            proj.job_manager = JobManager(proj)  # type: ignore[attr-defined]

        from glacium.managers.recipe_manager import RecipeManager
        from glacium.utils import list_jobs

        if proj.config.recipe == "CUSTOM":
            recipe_jobs = {}
        else:
            recipe = RecipeManager.create(proj.config.recipe)
            recipe_jobs = {j.name: j for j in recipe.build(proj)}

        if name.isdigit():
            idx = int(name) - 1
            all_jobs = list_jobs()
            if idx < 0 or idx >= len(all_jobs):
                raise ValueError("invalid job number")
            target = all_jobs[idx]
        else:
            target = name.upper()

        added: list[str] = []

        def add_with_deps(jname: str) -> None:
            if jname in proj.job_manager._jobs or jname in added:
                return
            job = recipe_jobs.get(jname)
            if job is None:
                if JobFactory.get(jname) is None:
                    raise KeyError(f"Job '{jname}' not known")
                job = JobFactory.create(jname, proj)
            for dep in getattr(job, "deps", ()):  # type: ignore[attr-defined]
                add_with_deps(dep)
            proj.jobs.append(job)
            proj.job_manager._jobs[jname] = job
            try:
                job.prepare()
            except Exception:
                pass
            added.append(jname)

        add_with_deps(target)

        proj.job_manager._save_status()

        proj.config.recipe = "CUSTOM"
        cfg_mgr = ConfigManager(proj.paths)
        cfg = cfg_mgr.load_global()
        cfg.recipe = "CUSTOM"
        cfg_mgr.dump_global()
        cfg_mgr.set("RECIPE", "CUSTOM")

        return added

    def jobs(self, names: Iterable[str]) -> "Project":
        for n in names:
            self.add_job(n)
        return self

    # ------------------------------------------------------------------
    def run(self, *jobs: str) -> "Project":
        """Execute jobs via the project's :class:`JobManager`."""

        job_list: Optional[Iterable[str]]
        if jobs:
            job_list = list(jobs)
        else:
            job_list = None
        if self._project.job_manager is None:
            self._project.job_manager = JobManager(self._project)  # type: ignore[attr-defined]
        self._project.job_manager.run(job_list)  # type: ignore[arg-type]
        return self

    # ------------------------------------------------------------------
    @property
    def uid(self) -> str:
        return self._project.uid

    @property
    def root(self) -> Path:
        return self._project.root

    @property
    def config(self):
        return self._project.config

    @property
    def paths(self):
        return self._project.paths

    @property
    def jobs(self):
        return self._project.jobs

    @property
    def job_manager(self) -> JobManager:
        return self._project.job_manager  # type: ignore[return-value]

    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        return getattr(self._project, name)

    def __setattr__(self, name: str, value):
        if name == "_project":
            super().__setattr__(name, value)
        else:
            setattr(self._project, name, value)

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, runs_root: str | Path, uid: str) -> "Project":
        """Load an existing project from ``runs_root`` by ``uid``."""

        pm = ProjectManager(Path(runs_root))
        proj = pm.load(uid)
        return cls(proj)

    # ------------------------------------------------------------------
    @staticmethod
    def get_mesh(project: "Project") -> Path:
        """Return the path of ``mesh.grid`` inside ``project``."""

        return project.paths.mesh_dir() / "mesh.grid"

    @staticmethod
    def set_mesh(mesh: Path, project: "Project") -> None:
        """Copy ``mesh`` into the project and update config paths."""

        dest = Project.get_mesh(project)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mesh, dest)

        rel = Path("..") / dest.relative_to(project.root)
        cfg_mgr = ConfigManager(project.paths)
        cfg = cfg_mgr.load_global()
        cfg["FSP_FILES_GRID"] = str(rel)
        if "ICE_GRID_FILE" in cfg:
            cfg["ICE_GRID_FILE"] = str(rel)
        cfg_mgr.dump_global()

    # ------------------------------------------------------------------
    def get_grid(self) -> Path:
        """Return the path to ``mesh.grid`` inside the project."""

        return self.paths.mesh_dir() / "mesh.grid"

    def mesh_grid(self, grid: Path) -> None:
        """Copy ``grid`` into the project and update configuration keys."""

        dest = self.get_grid()
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(grid, dest)

        rel = Path("..") / dest.relative_to(self.root)
        cfg_mgr = ConfigManager(self.paths)
        cfg = cfg_mgr.load_global()
        cfg["FSP_FILES_GRID"] = str(rel)
        if "ICE_GRID_FILE" in cfg:
            cfg["ICE_GRID_FILE"] = str(rel)
        cfg_mgr.dump_global()

