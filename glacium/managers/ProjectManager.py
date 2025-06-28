"""glacium.managers.project_manager – load()/create() fixed for new RecipeManager API"""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List

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
    """Koordiniert Erstellen & Laden von Projekten im *runs*-Verzeichnis."""

    def __init__(self, runs_root: Path):
        self.runs_root = runs_root.resolve()
        self.runs_root.mkdir(exist_ok=True)
        self._cache: Dict[str, Project] = {}

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    def create(self, name: str, recipe_name: str, airfoil: Path) -> Project:
        uid  = self._uid(name)
        root = self.runs_root / uid

        # Pfade & Grundstruktur
        paths = PathBuilder(root).build(); paths.ensure()
        cfg   = GlobalConfig(project_uid=uid, base_dir=root)
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
        if uid in self._cache:
            return self._cache[uid]

        root = self.runs_root / uid
        if not root.exists():
            raise FileNotFoundError(f"Projekt '{uid}' existiert nicht.")

        paths = PathBuilder(root).build()
        cfg_mgr = ConfigManager(paths)
        cfg   = cfg_mgr.load_global()

        project = Project(uid, root, cfg, paths, jobs=[])
        recipe  = RecipeManager.create(cfg.recipe)
        project.jobs.extend(recipe.build(project))
        project.job_manager = JobManager(project)  # type: ignore[attr-defined]
        self._cache[uid] = project
        return project

    # ------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------
    def list_uids(self) -> List[str]:
        return [p.name for p in self.runs_root.iterdir() if p.is_dir()]

    def refresh_jobs(self, uid: str) -> None:
        """Synchronisiert vorhandene Projekte mit dem neuesten Rezept."""
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
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        h  = hashlib.sha1(name.encode()).hexdigest()[:4]
        return f"{ts}-{h.upper()}"
