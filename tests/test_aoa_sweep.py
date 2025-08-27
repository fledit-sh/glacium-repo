import importlib.util
import math
import sys
import types
from pathlib import Path

# Create minimal package structure to satisfy imports inside aoa_sweep
pkg = types.ModuleType("glacium")
utils_pkg = types.ModuleType("glacium.utils")

convergence = types.ModuleType("glacium.utils.convergence")
convergence.project_cl_cd_stats = lambda *args, **kwargs: (0.0, 0.0, 0.0)

logging_pkg = types.ModuleType("glacium.utils.logging")
logging_pkg.log = type("Log", (), {"info": lambda *args, **kwargs: None})()

sys.modules.update(
    {
        "glacium": pkg,
        "glacium.utils": utils_pkg,
        "glacium.utils.convergence": convergence,
        "glacium.utils.logging": logging_pkg,
    }
)

spec = importlib.util.spec_from_file_location(
    "glacium.utils.aoa_sweep", Path(__file__).resolve().parents[1] / "glacium" / "utils" / "aoa_sweep.py"
)
aoa_sweep = importlib.util.module_from_spec(spec)
sys.modules["glacium.utils.aoa_sweep"] = aoa_sweep
spec.loader.exec_module(aoa_sweep)
run_aoa_sweep = aoa_sweep.run_aoa_sweep


class FakeRunProject:
    def __init__(self, aoa, cl_map, executed):
        self.aoa = aoa
        self._cl_map = cl_map
        self._executed = executed
        self.root = Path(".")

    def run(self):
        self._executed.append(self.aoa)

    def get(self, key):
        if key == "LIFT_COEFFICIENT":
            return self._cl_map[self.aoa]
        return None

    def clone(self):
        return FakeBuilder(self._cl_map, self._executed)


class FakeBuilder:
    def __init__(self, cl_map, executed):
        self._cl_map = cl_map
        self._executed = executed
        self.params = {}

    def set(self, key, value):
        self.params[key] = value
        return self

    def add_job(self, job):
        return self

    def create(self):
        aoa = self.params["CASE_AOA"]
        return FakeRunProject(aoa, self._cl_map, self._executed)


class FakeProject:
    def __init__(self, cl_map):
        self._cl_map = cl_map
        self.executed = []

    def clone(self):
        return FakeBuilder(self._cl_map, self.executed)


def test_run_aoa_sweep_refinement():
    cl_map = {
        0.0: 0.0,
        2.0: 2.0,
        4.0: 4.0,
        6.0: 6.0,
        8.0: 8.0,
        9.0: 9.0,
        10.0: 10.0,
        10.5: 10.25,
        11.0: 10.5,
        11.5: 10.0,
        12.0: 9.0,
    }
    base = FakeProject(cl_map)

    results, last_proj = run_aoa_sweep(
        base,
        aoa_start=0.0,
        aoa_end=14.0,
        step_sizes=[2.0, 1.0, 0.5],
        jobs=[],
        postprocess_aoas=set(),
    )
    aoas = [a for a, _cl, _p in results]
    assert aoas == [0.0, 2.0, 4.0, 6.0, 8.0, 9.0, 10.0, 10.5]

    cls = [c for _a, c, _p in results]
    assert all(x < y for x, y in zip(cls, cls[1:]))

    assert base.executed == [
        0.0,
        2.0,
        4.0,
        6.0,
        8.0,
        10.0,
        12.0,
        9.0,
        10.0,
        11.0,
        12.0,
        10.5,
        11.0,
        11.5,
    ]

    assert last_proj.aoa == aoas[-1]


def test_run_aoa_sweep_handles_nan_cl():
    cl_map = {0.0: float("nan"), 2.0: 2.0, 4.0: 4.0}
    base = FakeProject(cl_map)

    results, _ = run_aoa_sweep(
        base,
        aoa_start=0.0,
        aoa_end=4.0,
        step_sizes=[2.0],
        jobs=[],
        postprocess_aoas=set(),
    )

    cls = [c for _a, c, _p in results]
    assert all(math.isfinite(c) for c in cls)


def test_run_aoa_sweep_skips_aoa_zero():
    cl_map = {0.0: 0.0, 2.0: 2.0}
    base = FakeProject(cl_map)
    pre_exec: list[float] = []
    precomputed = {0.0: FakeRunProject(0.0, cl_map, pre_exec)}

    results, _ = run_aoa_sweep(
        base,
        aoa_start=0.0,
        aoa_end=2.0,
        step_sizes=[2.0],
        jobs=[],
        postprocess_aoas=set(),
        skip_aoas={0.0},
        precomputed=precomputed,
    )

    aoas = [a for a, _c, _p in results]
    assert aoas == [0.0, 2.0]
    # ensure the precomputed project was not executed
    assert pre_exec == []
    assert base.executed == [2.0]
