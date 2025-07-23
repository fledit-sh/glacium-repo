from pathlib import Path
import math
import matplotlib.pyplot as plt

import glacium as glc
from glacium.api import Project
from glacium.utils.logging import log
from glacium.utils.convergence import project_cl_cd_stats


def main():
    # create projects below ./runs in the current directory

    base_project = (
        Project("GridDependencyStudy")
        .name("X Grid")
        .create()
    )

    base_project.set("CASE_CHARACTERISTIC_LENGTH", 0.431)
    base_project.set("CASE_VELOCITY", 50)
    base_project.set("CASE_ALTITUDE", 0)
    base_project.set("CASE_TEMPERATURE", 263.15)
    base_project.set("CASE_AOA", 0)
    base_project.set("CASE_YPLUS", 0.3)

    # Job definitions that will be reused for each refinement
    base_jobs = [
        "XFOIL_REFINE",
        "XFOIL_THICKEN_TE",
        "XFOIL_PW_CONVERT",
        "POINTWISE_GCI",
        "FLUENT2FENSAP",
        "FENSAP_RUN",
        "FENSAP_CONVERGENCE_STATS",
        "FENSAP_ANALYSIS",
    ]

    refinements = [0.125 * (2**i) for i in range(8)]
    runs: list[tuple[float, float, float, Project]] = []

    for factor in refinements:
        proj = base_project.clone()
        proj.set("PWS_REFINEMENT", factor)
        for job in base_jobs:
            proj.add_job(job)

        proj.run()

        cl, _, cd, _ = project_cl_cd_stats(proj.root / "analysis" / "FENSAP")
        runs.append((factor, cl, cd, proj))

    factors = [r[0] for r in runs]
    cl_vals = [r[1] for r in runs]
    cd_vals = [r[2] for r in runs]

    out_dir = Path("grid_dependency_results")
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.figure()
    plt.plot(factors, cl_vals, marker="o")
    plt.xlabel("PWS_REFINEMENT")
    plt.ylabel("CL")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_dir / "cl_vs_refinement.png")
    plt.close()

    plt.figure()
    plt.plot(factors, cd_vals, marker="o")
    plt.xlabel("PWS_REFINEMENT")
    plt.ylabel("CD")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_dir / "cd_vs_refinement.png")
    plt.close()

    # Order of accuracy and GCI using the three finest grids
    sorted_runs = sorted(runs, key=lambda t: t[0])
    f1, phi1_cl, phi1_cd, _ = sorted_runs[0]
    f2, phi2_cl, phi2_cd, _ = sorted_runs[1]
    f3, phi3_cl, phi3_cd, _ = sorted_runs[2]
    r = f2 / f1

    p_cl = math.log(abs(phi3_cl - phi2_cl) / abs(phi2_cl - phi1_cl)) / math.log(r)
    p_cd = math.log(abs(phi3_cd - phi2_cd) / abs(phi2_cd - phi1_cd)) / math.log(r)

    Fs = 1.25
    gcis: list[tuple[float, Project]] = []
    for i in range(len(sorted_runs) - 1):
        phi_fine = sorted_runs[i][1]
        phi_coarse = sorted_runs[i + 1][1]
        gci = Fs * abs(phi_coarse - phi_fine) / (abs(phi_fine) * (r**p_cl - 1)) * 100.0
        gcis.append((gci, sorted_runs[i][3]))

    best_gci, best_proj = min(gcis, key=lambda t: t[0])

    log.info(f"Order of accuracy (CL): {p_cl:.3f}")
    log.info(f"Order of accuracy (CD): {p_cd:.3f}")
    log.info(f"Lowest GCI: {best_gci:.3f}% for refinement {best_proj.get('PWS_REFINEMENT')}")
    log.info(f"Recommended project: {best_proj.uid} ({best_proj.root})")


if __name__ == "__main__":
    main()
