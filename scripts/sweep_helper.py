"""Legacy wrapper for angle-of-attack sweeps.

This module previously implemented bespoke stall detection and sweep
refinement logic.  It now delegates to :func:`glacium.utils.run_aoa_sweep`
which provides the multi-stage refinement algorithm.  The ``aoa_sweep``
function retains the original API for backward compatibility.
"""

from __future__ import annotations

from typing import Callable, Iterable, List, Tuple, Collection

from glacium.api import Project
from glacium.utils import run_aoa_sweep


def aoa_sweep(
    base: Project,
    aoas: Iterable[float],
    setup: Callable[[Project], None],
    *,
    postprocess_aoas: Collection[float] | None = None,
) -> List[Tuple[float, float, Project]]:
    """Execute an AOA sweep.

    Parameters
    ----------
    base:
        Base project configured with common parameters.
    aoas:
        Angles of attack to execute.  They must be evenly spaced.
    setup:
        Callback invoked with each created project before running.  This is
        used to apply case-specific setup such as mesh reuse.
    postprocess_aoas:
        Angles that should include the post-processing job.

    Returns
    -------
    list[tuple[float, float, Project]]
        ``(aoa, cl, project)`` tuples for each executed case.
    """

    aoa_list = sorted(float(a) for a in aoas)
    if len(aoa_list) >= 2:
        step = aoa_list[1] - aoa_list[0]
    else:
        step = 1.0

    return run_aoa_sweep(
        base,
        aoa_start=aoa_list[0],
        aoa_end=aoa_list[-1],
        step_sizes=[step, step / 2, step / 4],
        jobs=["FENSAP_CONVERGENCE_STATS", "FENSAP_ANALYSIS"],
        postprocess_aoas=set(postprocess_aoas or ()),
        mesh_hook=setup,
    )


__all__ = ["aoa_sweep"]

