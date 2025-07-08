import yaml
from pathlib import Path
from click.testing import CliRunner

from glacium.cli import cli


def test_cli_projects_columns(tmp_path):
    runner = CliRunner()
    env = {"HOME": str(tmp_path), "COLUMNS": "200"}

    res = runner.invoke(cli, ["new", "demo", "-y"], env=env)
    assert res.exit_code == 0
    uid = res.output.strip().splitlines()[-1]

    case_file = Path("runs") / uid / "case.yaml"
    assert case_file.exists()
    case = yaml.safe_load(case_file.read_text()) or {}

    result = runner.invoke(cli, ["projects"], env=env)
    assert result.exit_code == 0

    import re
    ansi = re.compile(r"\x1b\[[0-9;]*[mK]")
    clean = ansi.sub("", result.output)

    assert ("Recipe" in clean) or ("Re\u2026" in clean)
    found = False
    for key in case.keys():
        if key in clean or (key[:2] + "\u2026") in clean:
            found = True
            break
    assert found
