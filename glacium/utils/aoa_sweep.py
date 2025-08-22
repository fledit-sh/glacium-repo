"""Utilities to execute angle-of-attack sweeps.

This module provides :func:`run_aoa_sweep` which drives a series of
FENSAP runs over a list of angles of attack (AoA).  It executes the
requested jobs for each AoA and optionally reruns the last three angles in
0.5° steps once a stall is detected.
"""

from __future__ import annotations

from typing import Callable, Iterable, List, Tuple, Set

from glacium.api import Project
from glacium.utils.convergence import project_cl_cd_stats
from glacium.utils.logging import log

__all__ = ["run_aoa_sweep"]


def _cl_from_project(proj: Project) -> float:
    """Return the lift coefficient for ``proj``.

    The value is read from the project configuration; if unavailable a
    fallback is extracted from the convergence statistics.
    """
    try:
        val = proj.get("LIFT_COEFFICIENT")
        if val is not None:
            return float(val)
    except Exception:
        pass

    try:
        cl, *_ = project_cl_cd_stats(proj.root / "analysis" / "FENSAP")
        return float(cl)
    except FileNotFoundError:
        return float("nan")


def run_aoa_sweep(
    base: Project,
    aoas: Iterable[float],
    jobs: list[str],
    postprocess_aoas: Set[float],
    mesh_hook: Callable[[Project], None] | None = None,
) -> List[Tuple[float, float, Project]]:
    """Execute an AoA sweep and return ``(aoa, cl, project)`` tuples.

    Parameters
    ----------
    base:
        Base project configured with common parameters.
    aoas:
        Angles of attack to execute.
    jobs:
        Jobs to run for each AoA. ``POSTPROCESS_SINGLE_FENSAP`` will be
        appended automatically for angles listed in ``postprocess_aoas``.
    postprocess_aoas:
        Angles that should include the post-processing job.
    mesh_hook:
        Optional callback applied to each created project after creation
        but before executing the jobs. This can be used to attach or reuse
        meshes and adjust job dependencies.
    """

    results: List[Tuple[float, float, Project]] = []
    executed: Set[float] = set()
    prev_cl: float | None = None
    stalled = False
    postprocess_aoas = set(postprocess_aoas)

    def _run_single(aoa: float) -> Tuple[float, float, Project]:
        builder = base.clone().set("CASE_AOA", aoa)
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
        executed.add(aoa)
        return aoa, cl, proj

    for aoa in aoas:
        aoa, cl, proj = _run_single(float(aoa))
        results.append((aoa, cl, proj))
        if prev_cl is not None and cl < prev_cl:
            stalled = True
            break
        prev_cl = cl

    if stalled and len(results) >= 3:
        window = results[-3:]
        min_a = min(a for a, _, _ in window)
        max_a = max(a for a, _, _ in window)
        start = int(min_a * 2)
        end = int(max_a * 2)
        for half in range(start, end + 1):
            aoa = half / 2
            if aoa in executed:
                continue
            aoa, cl, proj = _run_single(aoa)
            results.append((aoa, cl, proj))

    return results
