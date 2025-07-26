"""Helpers for analysing FENSAP convergence history files."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from glacium.analysis import ConvergenceAnalyzer

_analyzer = ConvergenceAnalyzer()

parse_headers = _analyzer.parse_headers
read_history = _analyzer.read_history
read_history_with_labels = _analyzer.read_history_with_labels
stats_last_n = _analyzer.stats_last_n
cl_cd_stats = _analyzer.cl_cd_stats
execution_time = _analyzer.execution_time
cl_cd_summary = _analyzer.cl_cd_summary
project_cl_cd_stats = _analyzer.project_cl_cd_stats
aggregate_report = _analyzer.aggregate_report
plot_stats = _analyzer.plot_stats

__all__ = [
    "parse_headers",
    "read_history",
    "read_history_with_labels",
    "stats_last_n",
    "cl_cd_stats",
    "execution_time",
    "cl_cd_summary",
    "project_cl_cd_stats",
    "aggregate_report",
    "plot_stats",
    "analysis",
    "analysis_file",
    "ConvergenceAnalyzer",
]


def analysis(cwd: Path, args: Sequence[str | Path]) -> None:
    """Aggregate convergence data and create plots."""
    _analyzer.analysis(cwd, args)


def analysis_file(cwd: Path, args: Sequence[str | Path]) -> None:
    """Analyse a single convergence file and generate plots."""
    _analyzer.analysis_file(cwd, args)
