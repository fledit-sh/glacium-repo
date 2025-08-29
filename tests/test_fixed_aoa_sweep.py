import importlib.util
import sys
import types
from pathlib import Path

# Minimal package structure for imports
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

# load helpers
spec = importlib.util.spec_from_file_location(
    "glacium.utils.aoa_sweep",
    Path(__file__).resolve().parents[1] / "glacium" / "utils" / "aoa_sweep.py",
)
aoa_sweep = importlib.util.module_from_spec(spec)
sys.modules["glacium.utils.aoa_sweep"] = aoa_sweep
spec.loader.exec_module(aoa_sweep)

spec = importlib.util.spec_from_file_location(
    "glacium.utils.fixed_aoa_sweep",
    Path(__file__).resolve().parents[1] / "glacium" / "utils" / "fixed_aoa_sweep.py",
)
fixed = importlib.util.module_from_spec(spec)
sys.modules["glacium.utils.fixed_aoa_sweep"] = fixed
spec.loader.exec_module(fixed)
run_fixed_step_aoa_sweep = fixed.run_fixed_step_aoa_sweep


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


class FakeBuilder:
    def __init__(self, cl_map, executed):
        self._cl_map = cl_map
        self._executed = executed
        self.params = {}
        self._name = None

    def name(self, name: str):
        self._name = name
        return self

    def set(self, key, value):
        self.params[key] = value
        return self

    def add_job(self, job):
        return self

    def create(self):
        aoa = self.params["CASE_AOA"]
        proj = FakeRunProject(aoa, self._cl_map, self._executed)
        proj.name = self._name
        return proj


class FakeProject:
    def __init__(self, cl_map):
        self._cl_map = cl_map
        self.executed = []

    def clone(self):
        return FakeBuilder(self._cl_map, self.executed)


def test_fixed_step_sweep_covers_all_and_no_prune():
    cl_map = {0.0: 0.0, 5.0: 5.0, 10.0: 4.0}
    base = FakeProject(cl_map)

    results = run_fixed_step_aoa_sweep(
        base,
        aoa_start=0.0,
        aoa_end=10.0,
        step=5.0,
        jobs=[],
        postprocess_aoas=set(),
    )

    aoas = [a for a, _c, _p in results]
    assert aoas == [0.0, 5.0, 10.0]

    cls = [c for _a, c, _p in results]
    assert cls == [0.0, 5.0, 4.0]

    assert base.executed == [0.0, 5.0, 10.0]
