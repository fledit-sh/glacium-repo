from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Dict, Any
import shutil
import yaml

from glacium.utils.JobIndex import JobFactory
from glacium.utils.logging import log
from glacium.utils import generate_global_defaults, global_default_config

from glacium.managers.config_manager import ConfigManager

from glacium.managers.project_manager import ProjectManager
from glacium.managers.job_manager import JobManager
from glacium.models.project import Project as ModelProject

__all__ = ["Project"]


class Project:
    """High level wrapper around :class:`~glacium.models.project.Project` as
    well as a builder for new projects."""

    _default_airfoil = Path(__file__).resolve().parents[1] / "data" / "AH63K127.dat"

    def __init__(self, source: ModelProject | str | Path) -> None:
        if isinstance(source, ModelProject):
            super().__setattr__("_project", source)
            super().__setattr__("_builder", False)
        else:
            super().__setattr__("runs_root", Path(source))
            super().__setattr__("_name", "project")
            super().__setattr__("_airfoil", self._default_airfoil)
            super().__setattr__("_params", {"RECIPE": "prep"})
            super().__setattr__("_jobs", [])
            super().__setattr__("tags", [])
            super().__setattr__("_project", None)
            super().__setattr__("_builder", True)

    # ------------------------------------------------------------------
    # Builder helpers
    # ------------------------------------------------------------------
    def name(self, value: str) -> "Project":
        self._name = value
        return self

    def select_airfoil(self, airfoil: str | Path) -> "Project":
        self._airfoil = Path(airfoil)
        return self

    def set(self, key: str, value: Any) -> "Project":
        self._params[key.upper()] = value
        return self

    def set_bulk(self, data: Dict[str, Any]) -> "Project":
        for k, v in data.items():
            self.set(k, v)
        return self

    def add_job(self, name: str):
        if self._builder:
            self._jobs.append(name)
            return self

        # operating on an existing project ------------------------------
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
            for dep in getattr(job, "deps", ()):
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

    def tag(self, label: str) -> "Project":
        self.tags.append(label)
        return self

    def clone(self) -> "Project":
        other = Project(self.runs_root)
        other._name = self._name
        other._airfoil = self._airfoil
        other._params = dict(self._params)
        other._jobs = list(self._jobs)
        other.tags = list(self.tags)
        return other

    def preview(self) -> "Project":
        log.info(f"Project name: {self._name}")
        log.info(f"Airfoil: {self._airfoil}")
        if self._params:
            log.info("Parameters:")
            for k, v in self._params.items():
                log.info(f"  {k} = {v}")
        if self._jobs:
            log.info("Jobs: " + ", ".join(self._jobs))
        if self.tags:
            log.info("Tags: " + ", ".join(self.tags))
        return self

    def create(self):
        recipe = str(self._params.get("RECIPE", "prep"))
        multishots = self._params.get("MULTISHOT_COUNT")
        pm = ProjectManager(self.runs_root)
        project = pm.create(self._name, recipe, self._airfoil, multishots=multishots)

        cfg_mgr = ConfigManager(project.paths)

        case_file = project.root / "case.yaml"
        case_data: Dict[str, Any] = {}
        if case_file.exists():
            case_data = yaml.safe_load(case_file.read_text()) or {}

        global_cfg = cfg_mgr.load_global()
        global_keys = {k.upper() for k in global_cfg.extras.keys()}
        global_keys.update({"PROJECT_UID", "BASE_DIR", "RECIPE"})
        case_keys = {k.upper() for k in case_data.keys()}

        global_updates: Dict[str, Any] = {}
        case_changed = False

        for k, v in self._params.items():
            if k in {"RECIPE", "PROJECT_NAME", "MULTISHOT_COUNT"}:
                continue

            key = k.upper()
            if key in case_keys:
                if case_data.get(key) != v:
                    case_changed = True
                case_data[key] = v
            elif key in global_keys:
                global_updates[key] = v
            else:
                raise KeyError(k)

        if case_file.exists():
            case_file.write_text(yaml.safe_dump(case_data, sort_keys=False))

        if case_changed:
            defaults = generate_global_defaults(case_file, global_default_config())
            global_cfg.extras.update(defaults)

        for k, v in global_updates.items():
            global_cfg[k] = v

        cfg_mgr.dump_global()
        project.config = global_cfg

        for name in self._jobs:
            try:
                job = JobFactory.create(name, project)
                project.jobs.append(job)
                try:
                    job.prepare()
                except Exception:
                    log.warning(f"Failed to prepare job {name}")
            except Exception as err:
                log.error(f"{name}: {err}")
        project.job_manager = JobManager(project)
        return Project(project)

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
    def __getattr__(self, name: str):
        if self._builder:
            raise AttributeError(name)
        return getattr(self._project, name)

    def __setattr__(self, name: str, value):
        if name in {"_project", "_builder", "runs_root", "_name", "_airfoil", "_params", "_jobs", "tags"}:
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

    def load_project(self, uid: str) -> "Project":
        """Instance helper using the builder's ``runs_root``."""

        return self.__class__.load(self.runs_root, uid)

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
