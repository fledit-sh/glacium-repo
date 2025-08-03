from __future__ import annotations

from pathlib import Path
import shutil
import yaml

from glacium.api import Project
from glacium.utils.logging import log
from glacium.utils import generate_global_defaults, global_default_config

from full_power_gci import load_runs, gci_analysis2


def main(base_dir: Path | str = Path("")) -> None:
    """Create a single-shot DROP3D/ICE3D run from the best grid."""

    base = Path(base_dir)

    runs = load_runs(base / "GridDependencyStudy")
    result = gci_analysis2(runs, base / "grid_dependency_results")
    if result is None:
        return

    _, _, best_proj = result
    dest_root = base / "SingleShot"
    dest_root.mkdir(parents=True, exist_ok=True)
    dest = dest_root / best_proj.uid
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(best_proj.root, dest)

    proj = Project.load(dest_root, best_proj.uid)

    case_file = proj.root / "case.yaml"
    case_data = yaml.safe_load(case_file.read_text()) if case_file.exists() else {}
    defaults = generate_global_defaults(case_file, global_default_config())
    total = float(case_data.get("ICE_GUI_TOTAL_TIME", defaults.get("ICE_GUI_TOTAL_TIME")))



    jobs = [
        "DROP3D_RUN",
        "DROP3D_CONVERGENCE_STATS",
        "ICE3D_RUN",
        "ICE3D_CONVERGENCE_STATS",
        "POSTPROCESS_SINGLE_FENSAP",
        "FENSAP_ANALYSIS",
    ]
    for j in jobs:
        proj.add_job(j)

    proj.run()
    log.info(f"Completed single-shot project {proj.uid}")


if __name__ == "__main__":
    main()
