import importlib.util
from pathlib import Path

module_path = Path(__file__).resolve().parents[1] / "glacium/post/multishot/auto_cp_normals.py"
spec = importlib.util.spec_from_file_location("auto_cp_normals", module_path)
auto_cp_normals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auto_cp_normals)
_infer_inlet = auto_cp_normals._infer_inlet


def test_infer_inlet_minimal():
    lines = [
        'VARIABLES = "x" "pressure"',
        'ZONE T="INLET", N=1',
        '0 101325',
    ]
    var_names = ["x", "pressure"]
    result = _infer_inlet(lines, var_names)
    assert "p_inf" in result
