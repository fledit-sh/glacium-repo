import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.utils.solver_time import parse_execution_time


def test_parse_execution_time_total_sim(tmp_path):
    log = tmp_path / ".solvercmd.out"
    lines = [
        "some output",
        "more output",
        "     |               total simulation = 01:23:45.67 |",
    ]
    log.write_text("\n".join(lines))
    assert parse_execution_time(log, last_lines=5) == "01:23:45.67"


def test_parse_execution_time_wall_time(tmp_path):
    log = tmp_path / ".solvercmd.out"
    lines = [
        "random line",
        "     |  Wall time for calculations:      123.456 s. |",
    ]
    log.write_text("\n".join(lines))
    assert parse_execution_time(log, last_lines=5) == "123.456 s"


def test_parse_execution_time_none(tmp_path):
    log = tmp_path / ".solvercmd.out"
    log.write_text("no timing info here")
    assert parse_execution_time(log) is None
