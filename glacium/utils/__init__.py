"""Utility helpers used across the Glacium code base."""

from importlib import import_module
import sys

from .JobIndex import list_jobs
from .current_job import JOB_TOKEN
from .current import PROJECT_TOKEN

save_current_job = JOB_TOKEN.save
load_current_job = JOB_TOKEN.load
from .default_paths import global_default_config, default_case_file
from .case_to_global import generate_global_defaults
from .first_cellheight import from_case as first_cellheight
from .convergence.io import parse_headers, read_history, read_history_with_labels
from .convergence.stats import stats_last_n, aggregate_report
from .convergence.plot import plot_stats
from .solver_time import parse_execution_time
from .string_utils import normalise_key

# ---------------------------------------------------------------------------
# Backwards compatibility shims
# ---------------------------------------------------------------------------

_analysis_mods = {
    "mesh_analysis": "analysis.mesh_analysis",
    "postprocess_fensap": "analysis.postprocess_fensap",
    "postprocess_mesh_html": "analysis.postprocess_mesh_html",
    "postprocess_mesh_multi": "analysis.postprocess_mesh_multi",
    "postprocess_mesh_html(deprecated)": "analysis.postprocess_mesh_html(deprecated)",
}
for _name, _path in _analysis_mods.items():
    _mod = import_module(f".{_path}", __name__)
    sys.modules[f"{__name__}.{_name}"] = _mod

_reporting_mods = {
    "report_config": "reporting.report_config",
    "report_converg_fensap": "reporting.report_converg_fensap",
    "report_project": "reporting.report_project",
}
for _name, _path in _reporting_mods.items():
    _mod = import_module(f".{_path}", __name__)
    sys.modules[f"{__name__}.{_name}"] = _mod
