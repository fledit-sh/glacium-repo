"""Utilities for computing ICEd characteristic values."""

from __future__ import annotations

import importlib.util
import math
import re
import sys
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

from glacium.api import Project as BuilderProject
from glacium.models.project import Project as ModelProject
from glacium.utils.multishot import load_multishot_project

__all__ = ["compute_iced_char_length"]

_SHOT_RE = re.compile(r"(\d{6})(?!.*\d)")
_READ_FIRST_ZONE_WITH_CONN: Callable | None = None

ProjectLike = BuilderProject | ModelProject


def _load_reader() -> Callable:
    global _READ_FIRST_ZONE_WITH_CONN
    if _READ_FIRST_ZONE_WITH_CONN is not None:
        return _READ_FIRST_ZONE_WITH_CONN

    try:
        from glacium.post.multishot.plot_s import _read_first_zone_with_conn as reader

        _READ_FIRST_ZONE_WITH_CONN = reader
        return reader
    except ModuleNotFoundError:
        plot_path = Path(__file__).resolve().parents[1] / "post" / "multishot" / "plot_s.py"
        spec = importlib.util.spec_from_file_location(
            "glacium.post.multishot.plot_s", plot_path
        )
        if spec is None or spec.loader is None:
            raise
        module = importlib.util.module_from_spec(spec)
        sys.modules.setdefault("glacium.post.multishot.plot_s", module)
        spec.loader.exec_module(module)
        reader = getattr(module, "_read_first_zone_with_conn")
        _READ_FIRST_ZONE_WITH_CONN = reader
        return reader


def _find_x_index(var_map: dict[str, int]) -> int | None:
    """Return the index of the X coordinate column based on ``var_map``."""

    candidates = ["x", "coordx", "xcoordinate", "coordinatex"]
    for key in candidates:
        idx = var_map.get(key)
        if idx is not None:
            return idx
    for key, idx in var_map.items():
        if key.endswith("x"):
            return idx
    return None


def _resolve_multishot_root(project: ProjectLike) -> Path:
    base_dir = project.root.parent.parent
    multishot_dir = base_dir / "05_multishot"
    if not multishot_dir.exists():
        raise FileNotFoundError(f"Multishot directory not found: {multishot_dir}")
    return multishot_dir


def _resolve_variable_roughness(project: ProjectLike) -> str | None:
    getter = getattr(project, "get", None)
    if callable(getter):
        try:
            roughness = getter("FSP_FILE_VARIABLE_ROUGHNESS")
        except KeyError as exc:
            raise ValueError("FSP_FILE_VARIABLE_ROUGHNESS is not defined on project") from exc
    else:
        roughness = project.config.get("FSP_FILE_VARIABLE_ROUGHNESS")
        if roughness is None:
            raise ValueError("FSP_FILE_VARIABLE_ROUGHNESS is not defined on project")
    if roughness is None:
        return None
    if isinstance(roughness, str):
        value = roughness.strip()
        if not value:
            return None
        if value.upper() == "NULL":
            return None
        return roughness
    return str(roughness)


def _infer_last_shot_index(multishot_project: ProjectLike) -> str | None:
    shots: Iterable[object] | None = None
    getter = getattr(multishot_project, "get", None)
    if callable(getter):
        try:
            shots = getter("CASE_MULTISHOT")
        except KeyError:
            shots = None
    if shots is None:
        cfg = getattr(multishot_project, "config", None)
        if cfg is not None:
            shots = cfg.get("CASE_MULTISHOT")

    last_candidate: str | None = None
    if shots is not None and isinstance(shots, Iterable) and not isinstance(shots, (str, bytes)):
        try:
            iterator = iter(shots)
        except TypeError:
            iterator = None
        if iterator is not None:
            for candidate in iterator:
                last_candidate = str(candidate)
            if last_candidate:
                match = _SHOT_RE.search(last_candidate)
                if match:
                    return match.group(1)

    analysis_root = multishot_project.root / "analysis" / "MULTISHOT"
    if not analysis_root.exists():
        return None

    shot_dirs: list[str] = []
    for child in analysis_root.iterdir():
        if child.is_dir() and len(child.name) == 6 and child.name.isdigit():
            if (child / "merged.dat").exists():
                shot_dirs.append(child.name)

    if not shot_dirs:
        return None

    return max(shot_dirs)


def _extract_shot_index(roughness: str) -> str:
    match = _SHOT_RE.search(str(roughness))
    if not match:
        raise ValueError(
            "Unable to infer shot index from FSP_FILE_VARIABLE_ROUGHNESS="
            f"{roughness!r}"
        )
    return match.group(1)


def compute_iced_char_length(project: ProjectLike) -> float:
    """Compute the iced characteristic length for ``project``.

    The method locates the associated multishot project, determines the active
    shot from the roughness displacement file and evaluates the X-span of the
    merged Tecplot data.  Missing or malformed data results in ``math.nan`` to
    allow callers to gracefully degrade their behaviour.
    """

    multishot_dir = _resolve_multishot_root(project)
    try:
        multishot_project = load_multishot_project(multishot_dir)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Unable to locate multishot project within {multishot_dir}"
        ) from exc

    roughness = _resolve_variable_roughness(project)
    shot: str | None = None
    if roughness is not None:
        try:
            shot = _extract_shot_index(roughness)
        except ValueError:
            shot = None
    if shot is None:
        shot = _infer_last_shot_index(multishot_project)
    if shot is None:
        return math.nan
    merged_path = (
        multishot_project.root
        / "analysis"
        / "MULTISHOT"
        / shot
        / "merged.dat"
    )
    if not merged_path.exists():
        return math.nan

    reader = _load_reader()

    try:
        nodes, _conn, _var_names, var_map = reader(merged_path)
    except Exception:
        return math.nan

    idx = _find_x_index(var_map)
    if idx is None:
        return math.nan

    if nodes.size == 0:
        return math.nan

    x = nodes[:, idx]
    if x.size == 0:
        return math.nan

    max_x = float(np.nanmax(x))
    min_x = float(np.nanmin(x))
    if not (math.isfinite(max_x) and math.isfinite(min_x)):
        return math.nan

    return max_x - min_x
