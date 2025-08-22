"""Utilities for running angle-of-attack sweeps.

This module contains helper logic shared by the clean and iced sweep
creation scripts.  The :func:`aoa_sweep` function executes a sweep over a
set of angles of attack, recording lift coefficients after each run and
optionally refining the sweep once the lift begins to decrease.
"""

from __future__ import annotations

from typing import Callable, Iterable, List, Tuple

from glacium.api import Project
from glacium.utils.convergence import project_cl_cd_stats
from glacium.utils.logging import log


def _jobs_for_aoa(aoa: float) -> list[str]:
    """Return the job list for a given angle of attack."""

    jobs = ["FENSAP_CONVERGENCE_STATS", "FENSAP_ANALYSIS"]
    if aoa == 0:
        jobs.append("POSTPROCESS_SINGLE_FENSAP")
    return jobs


def aoa_sweep(
    base: Project,
    aoas: Iterable[float],
    setup: Callable[[Project], None],
) -> List[Tuple[float, float, Project]]:
    """Execute an AOA sweep.

    Parameters
    ----------
    base:
        Base project configured with common parameters.
    aoas:
        Angles of attack to execute.
    setup:
        Callback invoked with each created project before running.  This is
        used to apply case-specific setup such as mesh reuse.

    Returns
    -------
    list[tuple[float, float, Project]]
        ``(aoa, cl, project)`` tuples for each executed case.
    """

    results: List[Tuple[float, float, Project]] = []
    prev_cl: float | None = None
    stalled = False

    for aoa in aoas:
        builder = base.clone().set("CASE_AOA", aoa)
        for job in _jobs_for_aoa(aoa):
            builder.add_job(job)
        proj = builder.create()
        setup(proj)
        proj.run()
        log.info(f"Completed angle {aoa}")

        cl = proj.get("LIFT_COEFFICIENT")
        if cl is None:
            try:
                cl, *_ = project_cl_cd_stats(proj.root / "analysis" / "FENSAP")
            except FileNotFoundError:
                cl = float("nan")

        results.append((aoa, cl, proj))
        if prev_cl is not None and cl < prev_cl:
            stalled = True
            break
        prev_cl = cl

    if stalled and len(results) >= 3:
        last = results[-3:]
        min_aoa = min(a for a, _, _ in last)
        max_aoa = max(a for a, _, _ in last)
        executed = {a for a, _, _ in results}
        for half in range(int(min_aoa * 2), int(max_aoa * 2) + 1):
            aoa = half / 2
            if aoa in executed:
                continue
            builder = base.clone().set("CASE_AOA", aoa)
            for job in _jobs_for_aoa(aoa):
                builder.add_job(job)
            proj = builder.create()
            setup(proj)
            proj.run()
            log.info(f"Completed angle {aoa}")

            cl = proj.get("LIFT_COEFFICIENT")
            if cl is None:
                try:
                    cl, *_ = project_cl_cd_stats(proj.root / "analysis" / "FENSAP")
                except FileNotFoundError:
                    cl = float("nan")
            results.append((aoa, cl, proj))

    return results


__all__ = ["aoa_sweep"]

