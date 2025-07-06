import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml
import pytest
from click.testing import CliRunner

from glacium.cli import cli
from glacium.utils import generate_global_defaults, global_default_config


def test_cli_generate_numeric_values(tmp_path):
    runner = CliRunner()
    case = Path(__file__).resolve().parents[1] / "glacium" / "config" / "defaults" / "case.yaml"
    with runner.isolated_filesystem(temp_dir=tmp_path):
        out = Path("out.yaml")
        result = runner.invoke(cli, ["generate", str(case), "-o", str(out)])
        assert result.exit_code == 0
        data = yaml.safe_load(out.read_text())
        expected = generate_global_defaults(case, global_default_config())
        assert data["FSP_MACH_NUMBER"] == pytest.approx(expected["FSP_MACH_NUMBER"])
        assert data["FSP_REYNOLDS_NUMBER"] == pytest.approx(expected["FSP_REYNOLDS_NUMBER"])
        assert data["ICE_REYNOLDS_NUMBER"] == pytest.approx(expected["ICE_REYNOLDS_NUMBER"])
        assert data["PWS_TREX_FIRST_HEIGHT"] == pytest.approx(expected["PWS_TREX_FIRST_HEIGHT"])
        assert data["MSH_GLOBMIN"] == pytest.approx(expected["MSH_GLOBMIN"])
