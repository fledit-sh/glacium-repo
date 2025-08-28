"""Utilities to execute angle-of-attack sweeps.

This module provides :func:`run_aoa_sweep` which drives a series of
FENSAP runs over a range of angles of attack (AoA).  The sweep is
performed in successive refinement stages controlled by a list of step
sizes.  When a decrease in the lift coefficient (``CL``) is detected the
current stage stops before the decreasing sample, the last two results are
discarded and the sweep restarts two steps back using the next, finer
step size.  The returned list therefore contains only monotonically
increasing ``CL`` values.
"""

from __future__ import annotations

from typing import Callable, Iterable, List, Tuple, Set, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - used for type checkers only
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
    aoa_start: float,
    aoa_end: float,
    step_sizes: Iterable[float],
    jobs: list[str],
    postprocess_aoas: Set[float],
    mesh_hook: Callable[[Project], None] | None = None,
) -> List[Tuple[float, float, Project]]:
    """Execute an AoA sweep and return ``(aoa, cl, project)`` tuples.

    Parameters
    ----------
    base:
        Base project configured with common parameters.
    aoa_start, aoa_end:
        Start and end AoA values for the sweep.
    step_sizes:
        Ordered list of AoA step sizes.  The sweep starts with the first
        (coarsest) step and refines using the next entries whenever a
        decrease in ``CL`` is detected.
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
        return aoa, cl, proj

    aoa = float(aoa_start)
    for step in step_sizes:
        stalled = False
        while aoa <= aoa_end:
            current_aoa, cl, proj = _run_single(aoa)
            if results and cl < results[-1][1]:
                stalled = True
                del results[-2:]
                aoa = current_aoa - 2 * step
                break
            results.append((current_aoa, cl, proj))
            aoa += step
        if not stalled:
            break

    return results
