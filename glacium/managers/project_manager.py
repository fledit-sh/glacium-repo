"""Create and load projects located inside the ``runs`` directory.

The :class:`ProjectManager` coordinates configuration, recipes and job
management.  Projects are identified by their UID which is a timestamp-based
string.

Example
-------
>>> pm = ProjectManager(Path('runs'))
>>> project = pm.create('demo', 'default_aero', Path('wing.dat'))
>>> pm.load(project.uid)
"""

from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List
import yaml

from glacium.managers.path_manager import PathBuilder, PathManager
from glacium.managers.config_manager import ConfigManager
from glacium.managers.template_manager import TemplateManager
from glacium.managers.recipe_manager import RecipeManager
from glacium.managers.job_manager import JobManager, Job
from glacium.models.config import GlobalConfig
from glacium.models.project import Project
from glacium.utils.logging import log
from glacium.utils.default_paths import global_default_config, default_case_file
from glacium.utils import generate_global_defaults

__all__ = ["ProjectManager"]


class ProjectManager:
    """Coordinate creation and loading of projects stored in ``runs``."""

    def __init__(self, runs_root: Path):
        """Initialise the manager working inside ``runs_root`` directory."""

        self.runs_root = runs_root.resolve()
        self.runs_root.mkdir(exist_ok=True)
        self._cache: Dict[str, Project] = {}

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    def create(
        self,
        name: str,
        recipe_name: str,
        airfoil: Path,
        *,
        multishots: int | None = None,
    ) -> Project:
        """Create a new project folder."""

        uid = self._uid(name)
        root = self.runs_root / uid

        paths, cfg = self._init_paths(root, uid, name, recipe_name, airfoil, multishots)
        self._render_templates(paths, cfg, uid)

        project = Project(uid, root, cfg, paths, jobs=[])
        self._load_jobs(project, recipe_name=recipe_name)

        self._cache[uid] = project
        log.success(f"Projekt '{uid}' erstellt.")
        return project

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
    def load(self, uid: str) -> Project:
        """Load an existing project by ``uid``.

        Parameters
        ----------
        uid:
            Unique identifier of the project.
        """

        if uid in self._cache:
            return self._cache[uid]

        root = self.runs_root / uid
        if not root.exists():
            raise FileNotFoundError(f"Projekt '{uid}' existiert nicht.")

        paths = PathBuilder(root).build()
        cfg_mgr = ConfigManager(paths)
        cfg = cfg_mgr.load_global()

        project = Project(uid, root, cfg, paths, jobs=[])
        status_file = paths.cfg_dir() / "jobs.yaml"

        self._load_jobs(project, status_file=status_file, cfg_mgr=cfg_mgr)

        self._cache[uid] = project
        return project

    # ------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------
    def list_uids(self) -> List[str]:
        """Return all known project UIDs."""

        return [p.name for p in self.runs_root.iterdir() if p.is_dir()]

    def refresh_jobs(self, uid: str) -> None:
        """Synchronise an existing project with the latest recipe."""
        proj = self.load(uid)  # load config and previous jobs
        if proj.config.recipe == "CUSTOM":
            return

        recipe = RecipeManager.create(proj.config.recipe)

        # 1) new list of desired jobs
        desired = {j.name: j for j in recipe.build(proj)}

        # 2) reuse old job instances or append new ones
        merged: list[Job] = []
        for name, job in desired.items():
            merged.append(proj.job_manager._jobs.get(name, job))  # type: ignore[attr-defined]
        proj.jobs = merged
        proj.job_manager = JobManager(proj)  # rebuild completely
        proj.job_manager._save_status()

    @staticmethod
    def _uid(name: str) -> str:
        """Generate a deterministic UID from ``name`` and current time."""

        ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
        h = hashlib.sha1(name.encode()).hexdigest()[:4]
        return f"{ts}-{h.upper()}"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _init_paths(
        self,
        root: Path,
        uid: str,
        name: str,
        recipe_name: str,
        airfoil: Path,
        multishots: int | None,
    ) -> tuple[PathManager, GlobalConfig]:
        paths = PathBuilder(root).build()
        paths.ensure()

        case_src = default_case_file()
        if case_src.exists():
            shutil.copy2(case_src, root / "case.yaml")

        case_file = root / "case.yaml"
        defaults = generate_global_defaults(case_file, global_default_config())

        cfg = GlobalConfig(**defaults, project_uid=uid, base_dir=root)
        if multishots is not None:
            cfg["MULTISHOT_COUNT"] = multishots
        cfg["PROJECT_NAME"] = name
        cfg["PWS_AIRFOIL_FILE"] = f"../_data/{airfoil.name}"
        cfg.recipe = recipe_name
        cfg.dump(paths.global_cfg_file())

        data_dir = paths.data_dir()
        data_dir.mkdir(exist_ok=True)
        (data_dir / airfoil.name).write_bytes(airfoil.read_bytes())

        return paths, cfg

    def _render_templates(self, paths: PathManager, cfg: GlobalConfig, uid: str) -> None:
        tmpl_root = Path(__file__).resolve().parents[1] / "templates"
        if not tmpl_root.exists():
            return
        TemplateManager(tmpl_root).render_batch(
            tmpl_root.rglob("*.j2"),
            cfg.extras | {"PROJECT_UID": uid},
            paths.tmpl_dir(),
        )

    def _load_jobs(self, project: Project, *, status_file: Path | None = None, recipe_name: str | None = None, cfg_mgr: ConfigManager | None = None) -> None:
        cfg = project.config
        if recipe_name:
            cfg.recipe = recipe_name
        sf = status_file or project.paths.cfg_dir() / "jobs.yaml"
        exists = sf.exists()
        names = list(yaml.safe_load(sf.read_text()) or {}) if exists else []
        recipe = None if cfg.recipe == "CUSTOM" else RecipeManager.create(cfg.recipe)
        replaced = False
        from glacium.utils.JobIndex import JobFactory

        def build(name: str):
            nonlocal replaced
            try:
                return JobFactory.create(name, project)
            except (KeyError, RuntimeError):
                from glacium.models.job import UnavailableJob
                replaced = True
                return UnavailableJob(project, name)

        jobs = [j for j in recipe.build(project) if not exists or j.name in names] if recipe else [build(n) for n in names]
        if exists and recipe:
            existing = {j.name for j in jobs}
            jobs.extend(build(n) for n in names if n not in existing)
        project.jobs.extend(jobs)
        if replaced:
            cfg.recipe = "CUSTOM"
            if cfg_mgr:
                cfg_mgr.set("RECIPE", "CUSTOM")
        for job in project.jobs:
            try:
                job.prepare()
            except Exception:
                log.warning(f"Failed to prepare job {job.name}")
        project.job_manager = JobManager(project)
