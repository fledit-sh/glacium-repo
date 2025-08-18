from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import scienceplots

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log
from glacium.post import analysis as post_analysis

plt.style.use(["science", "ieee"])


def load_single_project(root: Path) -> Project:
    pm = ProjectManager(root)
    uids = pm.list_uids()
    if not uids:
        raise FileNotFoundError(f"No projects found in {root}")
    if len(uids) > 1:
        log.warning("Multiple projects found, using the first one")
    return Project.load(root, uids[0])


def analyze_project(proj: Project, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    ice_dat = proj.root / "run_ICE3D" / "swimsol.ice.dat"
    if ice_dat.exists():
        df = post_analysis.read_wall_zone(ice_dat)
        chord = float(proj.get("CASE_CHARACTERISTIC_LENGTH"))
        proc, unit = post_analysis.process_wall_zone(df, chord=chord, unit="mm")
        post_analysis.plot_ice_thickness(proc, unit, out_dir / "ice_thickness.png")


def main(base_dir: Path | str = Path("")) -> None:
    base = Path(base_dir)
    root = base / "03_single_shot"
    try:
        proj = load_single_project(root)
    except FileNotFoundError as err:
        log.error(str(err))
        return
    analyze_project(proj, base / "04_single_shot_results")


if __name__ == "__main__":
    main()
