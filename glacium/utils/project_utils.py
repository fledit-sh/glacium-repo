"""Helpers for working with :class:`~glacium.api.Project` instances."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported only for type checking
    from glacium.api import Project  # for type hints only

__all__ = ["reuse_mesh"]



def reuse_mesh(
    project: "Project",
    mesh_path: Path | str,
    job_name: str,
    *,
    roughness: Path | str | None = None,
    template: str | None = None,
) -> None:
    """Copy ``mesh_path`` into ``project`` and clear dependencies.

    Parameters
    ----------
    project
        The project to update.
    mesh_path
        Path to the mesh file that should be copied into ``project``.
    job_name
        Name of the job whose dependencies should be cleared.
    roughness
        Optional roughness file copied alongside the mesh.
    template
        Optional template selector value forwarded to :meth:`Project.set_mesh`.
    """
    roughness_path = Path(roughness) if roughness is not None else None
    project.set_mesh(Path(mesh_path), roughness=roughness_path, template=template)
    job = project.job_manager._jobs.get(job_name)
    if job is not None:
        job.deps = ()
