import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from glacium.physics import ambient_pressure, interpolate_kinematic_viscosity
from glacium.utils import (
    first_cellheight,
    generate_global_defaults,
    resources,
)


def test_first_cellheight_from_case():
    case = (
        Path(__file__).resolve().parents[1]
        / "glacium"
        / "config"
        / "defaults"
        / "case.yaml"
    )
    expected = generate_global_defaults(case, resources.global_default_config())[ 
        "PWS_TREX_FIRST_HEIGHT"
    ]
    assert first_cellheight(case) == pytest.approx(expected)


def test_physics_helpers():
    assert ambient_pressure(0.0) == pytest.approx(101325.0)
    assert interpolate_kinematic_viscosity(300.0) == pytest.approx(1.568e-5)
