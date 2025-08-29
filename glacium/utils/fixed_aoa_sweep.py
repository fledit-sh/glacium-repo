"""Utilities to execute a simple fixed-step angle-of-attack sweep."""

from __future__ import annotations

from typing import Callable, List, Set, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - used for type checkers only
    from glacium.api import Project

from glacium.utils.logging import log
from .aoa_sweep import _cl_from_project

__all__ = ["run_fixed_step_aoa_sweep"]


def run_fixed_step_aoa_sweep(
    base: Project,
    aoa_start: float,
    aoa_end: float,
    step: float,
    jobs: list[str],
    postprocess_aoas: Set[float],
    mesh_hook: Callable[[Project], None] | None = None,
) -> List[Tuple[float, float, Project]]:
    """Run a fixed-step AoA sweep and return ``(aoa, cl, project)`` tuples."""

    results: List[Tuple[float, float, Project]] = []
    postprocess_aoas = set(postprocess_aoas)

    aoa = float(aoa_start)
    while aoa <= aoa_end:
        builder = base.clone().set("CASE_AOA", aoa).name(f"aoa_{aoa:+.1f}")
        for j in jobs:
            builder.add_job(j)
        if aoa in postprocess_aoas:
            builder.add_job("POSTPROCESS_SINGLE_FENSAP")
        proj = builder.create()
        if mesh_hook is not None:
            mesh_hook(proj)
        proj.run()
        log.info(f"Completed angle {aoa}")
        cl = _cl_from_project(proj)
        results.append((aoa, cl, proj))
        aoa += step

    return results
