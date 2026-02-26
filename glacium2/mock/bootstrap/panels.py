from __future__ import annotations

from ..core.panelspec import PanelSpec
from ..panels.mesh_viewer_panel import MeshViewerPanel
from ..panels.plots_panel import PlotsPanel
from ..panels.skeleton_panel import SkeletonPanel


def make() -> tuple[PanelSpec, ...]:
    return (
        PanelSpec(
            id="panel.skeleton",
            title="Project Skeleton",
            area=SkeletonPanel.default_dock_area,
            factory=lambda log, logger, settings, project_store: SkeletonPanel(
                log, logger, settings, project_store
            ),
        ),
        PanelSpec(
            id="panel.plots",
            title="Plots",
            area=PlotsPanel.default_dock_area,
            factory=lambda log, logger, settings, project_store: PlotsPanel(
                log, logger, settings, project_store
            ),
        ),
        PanelSpec(
            id="panel.mesh_viewer",
            title="Mesh Viewer",
            area=MeshViewerPanel.default_dock_area,
            factory=lambda log, logger, settings, project_store: MeshViewerPanel(
                log, logger, settings, project_store
            ),
            dock=False,
            workspace=True,
        ),
    )
