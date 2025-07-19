from __future__ import annotations

from pathlib import Path
import shutil
from typing import Iterable, Dict, Any

import yaml

from glacium.managers.project_manager import ProjectManager
from glacium.managers.config_manager import ConfigManager
from glacium.managers.job_manager import JobManager
from glacium.utils.JobIndex import JobFactory
from glacium.utils.logging import log
from glacium.utils import generate_global_defaults, global_default_config
from .project import Project


class Run:
    """Fluent helper to configure and create a project."""

    def __init__(self, runs_root: str | Path) -> None:
        self.runs_root = Path(runs_root)
        self._name = "project"
        self._airfoil: Path = Path(__file__).resolve().parents[1] / "data" / "AH63K127.dat"
        self._params: Dict[str, Any] = {"RECIPE": "prep"}
        self._jobs: list[str] = []
        self.tags: list[str] = []

    # ------------------------------------------------------------------
    def name(self, value: str) -> "Run":
        self._name = value
        return self

    def select_airfoil(self, airfoil: str | Path) -> "Run":
        self._airfoil = Path(airfoil)
        return self

    def set(self, key: str, value: Any) -> "Run":
        self._params[key.upper()] = value
        return self

    def set_bulk(self, data: Dict[str, Any]) -> "Run":
        for k, v in data.items():
            self.set(k, v)
        return self

    def add_job(self, name: str) -> "Run":
        self._jobs.append(name)
        return self

    def jobs(self, names: Iterable[str]) -> "Run":
        for n in names:
            self.add_job(n)
        return self

    def tag(self, label: str) -> "Run":
        self.tags.append(label)
        return self

    def clone(self) -> "Run":
        other = Run(self.runs_root)
        other._name = self._name
        other._airfoil = self._airfoil
        other._params = dict(self._params)
        other._jobs = list(self._jobs)
        other.tags = list(self.tags)
        return other

    # ------------------------------------------------------------------
    def preview(self) -> "Run":
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

    # ------------------------------------------------------------------
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
    def load(self, uid: str) -> Project:
        """Load an existing project by ``uid`` from ``runs_root``."""

        pm = ProjectManager(self.runs_root)
        proj = pm.load(uid)
        return Project(proj)

    # ------------------------------------------------------------------
    def get_mesh(self, project) -> Path:
        """Return the path of ``mesh.grid`` inside ``project``."""

        return project.paths.mesh_dir() / "mesh.grid"

    def set_mesh(self, mesh: Path, project) -> None:
        """Copy ``mesh`` into the project and update config paths."""

        dest = self.get_mesh(project)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mesh, dest)

        rel = Path("..") / dest.relative_to(project.root)
        cfg_mgr = ConfigManager(project.paths)
        cfg = cfg_mgr.load_global()
        cfg["FSP_FILES_GRID"] = str(rel)
        if "ICE_GRID_FILE" in cfg:
            cfg["ICE_GRID_FILE"] = str(rel)
        cfg_mgr.dump_global()
