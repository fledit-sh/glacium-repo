"""Create and load projects located inside the ``runs`` directory.

The :class:`ProjectManager` coordinates configuration, recipes and job
management.  Projects are identified by their UID which is a timestamp-based
string.

Example
-------
>>> pm = ProjectManager(Path('runs'))
>>> project = pm.create('demo', 'preprocessing', Path('wing.dat'))
>>> pm.load(project.uid)
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import yaml

from glacium.managers.PathManager import PathBuilder, PathManager
from glacium.managers.ConfigManager import ConfigManager
from glacium.managers.TemplateManager import TemplateManager
from glacium.managers.RecipeManager import RecipeManager
from glacium.managers.JobManager import JobManager, Job
from glacium.models.config import GlobalConfig
from glacium.models.project import Project
from glacium.utils.logging import log

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
    def create(self, name: str, recipe_name: str, airfoil: Path) -> Project:
        """Create a new project folder.

        Parameters
        ----------
        name:
            Human readable project name.
        recipe_name:
            Name of the recipe used to generate jobs.
        airfoil:
            Path to the airfoil file copied into the project.
        """

        uid  = self._uid(name)
        root = self.runs_root / uid

        # Pfade & Grundstruktur
        paths = PathBuilder(root).build(); paths.ensure()

        from glacium.config import compose_config

        defaults = compose_config()

        cfg = GlobalConfig(**defaults, project_uid=uid, base_dir=root)
        cfg["PROJECT_NAME"] = name
        cfg["PWS_AIRFOIL_FILE"] = f"_data/{airfoil.name}"
        cfg["RECIPE"] = recipe_name
        cfg.dump(paths.global_cfg_file())

        # Airfoil kopieren
        data_dir = paths.data_dir(); data_dir.mkdir(exist_ok=True)
        (data_dir / airfoil.name).write_bytes(airfoil.read_bytes())

        # Templates rendern (nur falls vorhanden)
        tmpl_root = Path(__file__).parents[2] / "templates"
        if tmpl_root.exists():
            TemplateManager(tmpl_root).render_batch(tmpl_root.rglob("*.j2"), cfg.extras | {
                "PROJECT_UID": uid,
            }, paths.tmpl_dir())

        # Project-Objekt (Jobs erst gleich)
        project = Project(uid, root, cfg, paths, jobs=[])

        # Recipe -> Jobs
        recipe = RecipeManager.create(recipe_name)
        project.jobs.extend(recipe.build(project))

        # JobManager anhängen
        project.job_manager = JobManager(project)  # type: ignore[attr-defined]
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
        cfg   = cfg_mgr.load_global()

        project = Project(uid, root, cfg, paths, jobs=[])
        recipe = RecipeManager.create(cfg.recipe)
        project.jobs.extend(recipe.build(project))

        # Persisted jobs that are not part of the recipe -----------------
        status_file = paths.cfg_dir() / "jobs.yaml"
        if status_file.exists():
            data = yaml.safe_load(status_file.read_text()) or {}
            from glacium.utils.JobIndex import create_job, get_job_class
            existing = {j.name for j in project.jobs}
            for name in data.keys():
                if name not in existing:
                    cls = get_job_class(name)
                    if cls:
                        project.jobs.append(create_job(name, project))

        project.job_manager = JobManager(project)  # type: ignore[attr-defined]
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
        proj   = self.load(uid)                    # lädt Config + alte Jobs
        recipe = RecipeManager.create(proj.config.recipe)

        # 1) Neue Liste der Soll-Jobs
        desired = {j.name: j for j in recipe.build(proj)}

        # 2) Alte Job-Instanzen übernehmen, sonst neue anhängen
        merged: list[Job] = []
        for name, job in desired.items():
            merged.append(proj.job_manager._jobs.get(name, job))  # type: ignore[attr-defined]
        proj.jobs = merged
        proj.job_manager = JobManager(proj)  # komplett neu aufbauen
        proj.job_manager._save_status()

    @staticmethod
    def _uid(name: str) -> str:
        """Generate a deterministic UID from ``name`` and current time."""

        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        h = hashlib.sha1(name.encode()).hexdigest()[:4]
        return f"{ts}-{h.upper()}"

