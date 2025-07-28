from __future__ import annotations

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import scienceplots

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log

plt.style.use(["science", "ieee"])


def load_multishot_project(root: Path) -> Project:
    """Return the single multishot project located in ``root``."""
    pm = ProjectManager(root)
    uids = pm.list_uids()
    if not uids:
        raise FileNotFoundError(f"No projects found in {root}")
    if len(uids) > 1:
        log.warning("Multiple projects found, using the first one")
    return Project.load(root, uids[0])


def plot_cl_cd(csv_file: Path, out_dir: Path) -> None:
    """Plot CL and CD values from ``csv_file`` and save into ``out_dir``."""
    data = np.loadtxt(csv_file, delimiter=",", skiprows=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    idx, cl, cd = data[:, 0], data[:, 1], data[:, 2]

    out_dir.mkdir(parents=True, exist_ok=True)

    plt.figure()
    plt.plot(idx, cl, marker="o", label="CL")
    plt.plot(idx, cd, marker="o", label="CD")
    plt.xlabel("shot index")
    plt.ylabel("coefficient")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "cl_cd_vs_index.png")
    plt.close()


def main(base_dir: Path | str = Path("")) -> None:
    """Analyze a multishot project located under ``base_dir``."""

    base = Path(base_dir)
    project_root = base / "Multishot"
    project = load_multishot_project(project_root)
    csv_path = project.root / "analysis" / "MULTISHOT" / "cl_cd_stats.csv"
    plot_cl_cd(csv_path, base / "multishot_results")


if __name__ == "__main__":
    main()
