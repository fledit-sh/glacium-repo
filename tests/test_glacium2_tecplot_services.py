import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium2.gui.tecplot.cameraservice import CameraService
from glacium2.gui.tecplot.scalarservice import ScalarService
from glacium2.gui.tecplot.sceneinfo import SceneInfoService
from glacium2.gui.tecplot.viewerstate import ViewerState, ZoneItem
from glacium2.gui.tecplot.zoneservice import ZoneService


class FakeDataset:
    def __init__(self, n_points=0, n_cells=0, bounds=(0, 1, 0, 1, 0, 1), point_data=None, cell_data=None):
        self.n_points = n_points
        self.n_cells = n_cells
        self.bounds = bounds
        self.point_data = point_data or {}
        self.cell_data = cell_data or {}


class FakeMultiBlock:
    def __init__(self, blocks: dict[str, object]):
        self._blocks = blocks

    def keys(self):
        return self._blocks.keys()

    def get(self, key):
        return self._blocks.get(key)


def test_zone_service_flatten_and_select():
    mb = FakeMultiBlock(
        {
            "A": FakeDataset(n_points=10, n_cells=5),
            "B": FakeMultiBlock({"C": FakeDataset(n_points=1, n_cells=2)}),
            "EMPTY": FakeDataset(),
        }
    )
    zones = ZoneService.extract_zones(mb)
    assert len(zones) == 2
    assert "A" in zones[0].label
    assert "B / C" in zones[1].label
    assert ZoneService.select_active_indices(zones, 0) == [0, 1]
    assert ZoneService.select_active_indices(zones, 2) == [1]


def test_scalar_scene_and_camera_services():
    ds1 = FakeDataset(n_points=3, n_cells=4, bounds=(0, 2, 0, 1, -1, 1), point_data={"p": [1]}, cell_data={"c": [2]})
    ds2 = FakeDataset(n_points=1, n_cells=2, bounds=(-2, 1, -3, 4, 0, 2), point_data={"p": [2], "v": [0]})
    state = ViewerState(
        path=Path("demo.dat"),
        zones=[ZoneItem(label="z1", dataset=ds1), ZoneItem(label="z2", dataset=ds2)],
        active_indices=[0, 1],
    )

    names = ScalarService.scalar_names_for_active(state)
    assert names == ["p", "c", "v"]
    assert ScalarService.derive_active_scalar(names, "v") == "v"
    assert ScalarService.derive_active_scalar(names, "(none)") == "p"

    bounds = CameraService.bounds_union([ds1.bounds, ds2.bounds])
    assert bounds == (-2, 2, -3, 4, -1, 2)
    center = CameraService.scene_center(bounds)
    assert center == (0.0, 0.5, 0.5)
    assert CameraService.camera_from_preset(center, 2.0, "Isometric") is not None

    pts, cells = SceneInfoService.sum_points_and_cells([ds1, ds2])
    assert (pts, cells) == (4, 6)
    zone_label = SceneInfoService.zone_label(["z1", "z2"], [0, 1])
    assert zone_label == "ALL"
    text = SceneInfoService.build_label_text("demo.dat", zone_label, pts, cells, "p")
    assert "points=4" in text
    assert "scalar=p" in text
