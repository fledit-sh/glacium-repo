"""glacium.cli.new
===================
CLI-Befehl `glacium new` – legt ein frisches Projekt an.

Funktionen
----------
• UID-Ordner in *runs/* erstellen
• Default-GlobalConfig kopieren (oder Minimal-Fallback)
• Airfoil-Datei ins Projekt kopieren und Pfad in Config setzen
• Alle Templates einmalig rendern
• Recipe auswählen → Jobs erzeugen → jobs.yaml schreiben
"""
from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, UTC
from pathlib import Path

import click

from glacium.utils.logging import log, log_call
from glacium.utils.default_paths import global_default_config, default_case_file
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.managers.template_manager import TemplateManager
from glacium.managers.recipe_manager import RecipeManager
from glacium.models.project import Project
from glacium.managers.job_manager import JobManager

# Paket-Ressourcen ---------------------------------------------------------
PKG_ROOT      = Path(__file__).resolve().parents[2]       # repo‑Root
PKG_PKG       = Path(__file__).resolve().parents[1]       # .../glacium
TEMPLATE_ROOT = PKG_ROOT / "templates"
DEFAULT_CFG   = global_default_config()
DEFAULT_CASE  = default_case_file()
RUNS_ROOT     = PKG_ROOT / "runs"

DEFAULT_RECIPE  = "multishot"
DEFAULT_AIRFOIL = PKG_PKG / "data" / "AH63K127.dat"

# ------------------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------------------

def _uid(name: str) -> str:
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    h  = hashlib.sha1(name.encode()).hexdigest()[:4].upper()
    return f"{ts}-{h}"


def _copy_default_cfg(dest: Path, uid: str) -> GlobalConfig:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if DEFAULT_CFG.exists():
        shutil.copy2(DEFAULT_CFG, dest)
        cfg = GlobalConfig.load(dest)
    else:
        cfg = GlobalConfig(project_uid=uid, base_dir=dest.parent)
        log.warning("DEFAULT_CFG nicht gefunden – Minimal-Config erzeugt.")
    cfg.project_uid = uid
    cfg.dump(dest)
    return cfg

# ------------------------------------------------------------------------
# Click-Command
# ------------------------------------------------------------------------
@click.command("new")
@click.argument("name")
@click.option("-a", "--airfoil",
              type=click.Path(path_type=Path),
              default=DEFAULT_AIRFOIL,
              show_default=True,
              help="Pfad zur Profil-Datei")
@click.option("-r", "--recipe",
              default=DEFAULT_RECIPE,
              show_default=True,
              help="Name des Rezepts (Jobs)")
@click.option("-o", "--output", default=str(RUNS_ROOT), show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=Path),
              help="Root-Ordner für Projekte")
@click.option("-y", "--yes", is_flag=True,
              help="Existierenden Ordner ohne Rückfrage überschreiben")
@log_call
def cli_new(name: str, airfoil: Path, recipe: str, output: Path, yes: bool):
    """Erstellt ein neues Glacium-Projekt."""

    uid       = _uid(name)
    proj_root = output / uid

    if proj_root.exists():
        if not yes:
            click.confirm(f"{proj_root} existiert – überschreiben?", abort=True)
        shutil.rmtree(proj_root)

    # 1) Pfade anlegen
    paths = PathBuilder(proj_root).build()
    paths.ensure()

    # Kopiere Standard-"case.yaml" falls vorhanden
    if DEFAULT_CASE.exists():
        shutil.copy2(DEFAULT_CASE, proj_root / "case.yaml")

    # 2) Globale Config
    cfg_file = paths.global_cfg_file()
    cfg      = _copy_default_cfg(cfg_file, uid)
    cfg["PROJECT_NAME"] = name

    # 3) Airfoil kopieren
    data_dir = paths.data_dir(); data_dir.mkdir(exist_ok=True)
    dest_air = data_dir / airfoil.name
    shutil.copy2(airfoil, dest_air)
    cfg.PWS_AIRFOIL_FILE = str(dest_air.relative_to(proj_root))  # type: ignore[attr-defined]
    cfg.recipe = recipe
    cfg.dump(cfg_file)

    # 4) Templates rendern
    TemplateManager(TEMPLATE_ROOT).render_batch(
        TEMPLATE_ROOT.rglob("*.j2"), cfg.__dict__, paths.tmpl_dir()
    )

    # 5) Jobs aus Recipe & Status anlegen
    recipe_obj = RecipeManager.create(recipe)
    jobs       = recipe_obj.build(None)  # type: ignore[arg-type]
    project    = Project(uid, proj_root, cfg, paths, jobs)
    JobManager(project)  # erzeugt jobs.yaml

    log.success(f"Projekt angelegt: {proj_root}")
    click.echo(uid)


if __name__ == "__main__":
    cli_new()
