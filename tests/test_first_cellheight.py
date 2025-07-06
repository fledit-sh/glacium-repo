import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from glacium.utils import first_cellheight, generate_global_defaults, global_default_config


def test_first_cellheight_from_case():
    case = Path(__file__).resolve().parents[1] / "glacium" / "config" / "defaults" / "case.yaml"
    expected = generate_global_defaults(case, global_default_config())["PWS_TREX_FIRST_HEIGHT"]
    assert first_cellheight(case) == pytest.approx(expected)
