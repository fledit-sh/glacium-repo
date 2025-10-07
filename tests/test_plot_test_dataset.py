from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

h5py = pytest.importorskip("h5py")

spec = importlib.util.spec_from_file_location(
    "plot_test_module", Path(__file__).resolve().parents[1] / "scripts" / "plot_test.py"
)
plot_test = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(plot_test)


def _write_convergence_histories(base: Path) -> None:
    (base / "converg.fensap.000001").write_text(
        "\n".join(
            [
                "# 1 lift coefficient",
                "# 2 drag coefficient",
                "1.0 2.0",
                "3.0 4.0",
                "5.0 6.0",
            ]
        ),
        encoding="utf-8",
    )

    (base / "converg.drop.000001").write_text(
        "\n".join(
            [
                "# 1 residual",
                "0.1",
                "0.2",
                "0.3",
            ]
        ),
        encoding="utf-8",
    )


def _prepare_project(tmp_path: Path) -> tuple[Path, Path]:
    case_yaml = tmp_path / "case.yaml"
    case_yaml.write_text(
        "\n".join(
            [
                "CASE_ROUGHNESS: 0.5",
                "CASE_VELOCITY: 42",
                "CASE_AOA: 7.0",
                "CASE_YPLUS: 0.3",
                "CASE_MULTISHOT: [1.2]",
            ]
        ),
        encoding="utf-8",
    )

    root = tmp_path / "analysis" / "MULTISHOT"
    (root / "000001").mkdir(parents=True)
    return case_yaml, root


def test_save_preprocessed_dataset_writes_case_attributes(tmp_path, monkeypatch):
    case_yaml, root = _prepare_project(tmp_path)

    run_multishot_dir = tmp_path / "run_MULTISHOT"
    run_multishot_dir.mkdir()
    _write_convergence_histories(run_multishot_dir)

    def fake_load_shot(_root, _idx):
        nodes = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 2.0]])
        conn = np.array([], dtype=int).reshape(0, 2)
        var_names = ["X", "Y", "Cp"]
        vmap = {"x": 0, "y": 1, "cp": 2}
        return nodes, conn, var_names, vmap

    monkeypatch.setattr(plot_test, "load_shot", fake_load_shot)

    dataset = tmp_path / "dataset.h5"
    plot_test.save_preprocessed_dataset(dataset, case_yaml, root)

    with h5py.File(dataset, "r") as h5:
        assert "CASE_ROUGHNESS" in h5.attrs
        assert "CASE_MULTISHOT" not in h5.attrs
        assert pytest.approx(0.5) == h5.attrs["CASE_ROUGHNESS"]
        assert int(h5.attrs["CASE_VELOCITY"]) == 42
        assert pytest.approx(7.0) == h5.attrs["CASE_AOA"]
        assert pytest.approx(0.3) == h5.attrs["CASE_YPLUS"]
        assert h5.attrs["num_shots"] == 1
        times = json.loads(h5.attrs["case_times"])
        assert len(times) == 1
        assert pytest.approx(1.2) == times[0]

        shot_grp = h5["000001"]
        assert "converg_fensap_stats" not in shot_grp.attrs
        assert "converg_drop_stats" not in shot_grp.attrs

        lift_stats = np.asarray(shot_grp.attrs["fensap_lift_coefficient"], dtype=float)
        drag_stats = np.asarray(shot_grp.attrs["fensap_drag_coefficient"], dtype=float)
        residual_stats = np.asarray(shot_grp.attrs["drop_residual"], dtype=float)

        np.testing.assert_allclose(lift_stats, [3.0, 8.0 / 3.0])
        np.testing.assert_allclose(drag_stats, [4.0, 8.0 / 3.0])
        np.testing.assert_allclose(residual_stats, [0.2, 0.0066666666])


def test_save_preprocessed_dataset_prefers_local_stats(tmp_path, monkeypatch):
    case_yaml, root = _prepare_project(tmp_path)

    shot_dir = root / "000001"
    multishot_dir = shot_dir / "run_MULTISHOT"
    multishot_dir.mkdir(parents=True, exist_ok=True)
    _write_convergence_histories(multishot_dir)

    def fake_load_shot(_root, _idx):
        nodes = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 2.0]])
        conn = np.array([], dtype=int).reshape(0, 2)
        var_names = ["X", "Y", "Cp"]
        vmap = {"x": 0, "y": 1, "cp": 2}
        return nodes, conn, var_names, vmap

    monkeypatch.setattr(plot_test, "load_shot", fake_load_shot)

    dataset = tmp_path / "dataset_local.h5"
    plot_test.save_preprocessed_dataset(dataset, case_yaml, root)

    with h5py.File(dataset, "r") as h5:
        shot_grp = h5["000001"]
        assert "converg_fensap_stats" not in shot_grp.attrs
        assert "converg_drop_stats" not in shot_grp.attrs

        fensap_lift = np.asarray(shot_grp.attrs["fensap_lift_coefficient"], dtype=float)
        drop_residual = np.asarray(shot_grp.attrs["drop_residual"], dtype=float)

        np.testing.assert_allclose(fensap_lift, [3.0, 8.0 / 3.0])
        np.testing.assert_allclose(drop_residual, [0.2, 0.0066666666])

