"""Utilities to execute angle-of-attack sweeps.

This module provides :func:`run_aoa_sweep` which drives a series of
FENSAP runs over a range of angles of attack (AoA).  The sweep is
performed in successive refinement stages controlled by a list of step
sizes.  When a decrease in the lift coefficient (``CL``) is detected the
current stage discards the last computed sample and the sweep restarts
from the preceding angle using the next, finer step size.  Previously
computed results are retained so the returned list contains all sampled
cases with monotonically increasing ``CL`` values.  The last stable
project is also returned for callers that want to restart the sweep using
it as a base for further refinement.
"""

from __future__ import annotations

import math
from typing import Callable, Iterable, List, Tuple, Set, TYPE_CHECKING, Dict

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
            cl = float(val)
            if not math.isnan(cl):
                return cl
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
    skip_aoas: Set[float] = set(),
    precomputed: Dict[float, Project] | None = None,
) -> Tuple[List[Tuple[float, float, Project]], Project]:
    """Execute an AoA sweep.

    The sweep progresses over ``aoa_start``..``aoa_end`` using the
    provided step sizes in sequence.  When a drop in the lift coefficient
    is detected, the most recent result is discarded and the sweep
    restarts from the previous angle with the next, finer step size.

    Parameters
    ----------
    base:
        Base project configured with common parameters.
    aoa_start, aoa_end:
        Start and end AoA values for the sweep.
    step_sizes:
        Ordered list of AoA step sizes.  The sweep starts with the first
        (coarsest) step and refines using subsequent entries whenever a
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
    skip_aoas:
        Angles that must not be executed. Results for these angles are
        taken from ``precomputed``; omitting an entry for a skipped angle
        raises :class:`KeyError`.
    precomputed:
        Mapping of AoA values to already existing projects.  Typical use
        is supplying data for ``skip_aoas`` entries.

    Returns
    -------
    list[tuple[float, float, Project]], Project
        ``(aoa, cl, project)`` tuples for all sampled cases and the last
        stable project.  The project can be cloned by callers to restart a
        sweep with finer step sizes.
    """

    results: List[Tuple[float, float, Project]] = []
    aoa_history: List[float] = []
    postprocess_aoas = set(postprocess_aoas)
    skip_aoas = set(skip_aoas)

    def _run_single(aoa: float) -> Tuple[float, float, Project]:
        builder = base.clone().name(f"aoa_{aoa:+.1f}").set("CASE_AOA", aoa)
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
    last_stable: Tuple[float, float, Project] | None = None
    last_project: Project = base

    for step in step_sizes:
        stalled = False
        if last_stable is not None:
            base = last_stable[2]
            aoa = last_stable[0] + step
        else:
            aoa = float(aoa_start)
        while aoa <= aoa_end:
            if aoa in skip_aoas:
                if precomputed is None or aoa not in precomputed:
                    raise KeyError(f"No precomputed project for skipped AoA {aoa}")
                proj = precomputed[aoa]
                cl = _cl_from_project(proj)
                if results and cl < results[-1][1]:
                    stalled = True
                    if results:
                        results.pop()
                        aoa_history.pop()
                        last_stable = results[-1] if results else None
                        last_project = last_stable[2] if last_stable else base
                    break
                results.append((aoa, cl, proj))
                aoa_history.append(aoa)
                last_project = proj
                aoa += step
                continue
            current_aoa, cl, proj = _run_single(aoa)
            if results and cl < results[-1][1]:
                stalled = True
                if results:
                    results.pop()
                    aoa_history.pop()
                    last_stable = results[-1] if results else None
                    last_project = last_stable[2] if last_stable else base
                break
            results.append((current_aoa, cl, proj))
            aoa_history.append(current_aoa)
            last_project = proj
            aoa += step
        if not stalled:
            break

    return results, last_project
