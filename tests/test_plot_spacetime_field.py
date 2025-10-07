import logging
import sys
import types
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
if "h5py" not in sys.modules:
    h5py_stub = types.ModuleType("h5py")
    h5py_stub.File = object  # type: ignore[attr-defined]
    sys.modules["h5py"] = h5py_stub
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from scripts.plot_test import plot_spacetime_field


def test_plot_spacetime_field_single_time_slice(tmp_path, caplog):
    times = [0.25]
    s_coords = [np.linspace(-1.0, 1.0, 5)]
    values = [np.linspace(0.0, 1.0, 5)]

    with caplog.at_level(logging.WARNING):
        plot_spacetime_field(
            tmp_path,
            times,
            s_coords,
            values,
            label="Test Field",
            stem="test_field",
        )

    output_file = Path(tmp_path) / "test_field_spacetime.pdf"
    assert output_file.is_file()
    assert any("falling back to 1D plot" in msg for msg in caplog.messages)
