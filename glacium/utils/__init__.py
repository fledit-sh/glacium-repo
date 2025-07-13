"""Utility helpers used across the Glacium code base."""

from .JobIndex import list_jobs
from .current_job import save as save_current_job, load as load_current_job
from .default_paths import global_default_config, default_case_file
from .case_to_global import generate_global_defaults
from .first_cellheight import from_case as first_cellheight
from .convergence import (
    parse_headers,
    read_history,
    read_history_with_labels,
    stats_last_n,
    aggregate_report,
    plot_stats,
)
from .solver_time import parse_execution_time
