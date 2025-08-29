"""Perform GCI analysis for the full power study.

The script aggregates results from grid-refinement runs, computes
sliding-window Grid Convergence Index (GCI) statistics and produces
plots along with a PDF summary report.

Key Functions
-------------
* :func:`load_runs` – collect run metadata.
* :func:`gci_analysis2` – perform the GCI calculations and plotting.
* :func:`generate_gci_pdf_report` – render a PDF summary.
* :func:`main` – command line entry point.

Inputs
------
base_dir : Path | str, optional
    Directory containing ``01_grid_dependency_study`` runs.

Outputs
-------
Plots and ``grid_convergence_report.pdf`` in ``02_grid_dependency_results``.

Usage
-----
``python scripts/02_full_power_gci.py``

See Also
--------
``docs/full_power_study.rst`` for a complete workflow walkthrough.
"""

from __future__ import annotations

from pathlib import Path
import math
import subprocess
import sys
import matplotlib.pyplot as plt

from glacium.post.multishot.plot_s import (
    _read_first_zone_with_conn,
    order_from_connectivity,
    arclength,
)

from glacium.api import Project
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log
from glacium.utils.convergence import project_cl_cd_stats, execution_time
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib import colors
from math import nan


def compute_h_from_merged(path: Path) -> float:
    """Return mean segment length from a merged Tecplot file.

    Parameters
    ----------
    path : Path
        Location of the ``merged.dat`` (or similar) file.

    Returns
    -------
    float
        Average edge length along the ordered polyline, or ``NaN`` on error.
    """
    try:
        nodes, conn, _, _ = _read_first_zone_with_conn(path)
        order = order_from_connectivity(len(nodes), conn)
        x = nodes[order, 0]
        y = nodes[order, 1]
        s = arclength(x, y)
        return float(s[-1]) / len(s)
    except Exception:
        return float("nan")


def load_runs(root: Path) -> list[tuple[float, float, float, Project]]:
    """Return grid spacing h, CL, CD and project for all runs."""
    pm = ProjectManager(root)
    runs: list[tuple[float, float, float, Project]] = []
    for uid in pm.list_uids():
        try:
            proj = Project.load(root, uid)
        except FileNotFoundError:
            continue

        soln = proj.root / "run_FENSAP" / "soln.dat"
        merged = proj.root / "analysis" / "FENSAP" / "merged.dat"
        if not soln.exists():
            log.warning(f"Missing soln.dat for {uid}, skipping run")
            continue

        if not merged.exists():
            merged.parent.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "glacium.post.multishot.merge",
                        str(soln),
                        "--out",
                        str(merged),
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError:
                log.warning(f"Failed to merge {soln} for {uid}")
                continue

        h = compute_h_from_merged(merged)

        try:
            cl = float(proj.get("LIFT_COEFFICIENT"))
            cd = float(proj.get("DRAG_COEFFICIENT"))
        except Exception:
            cl, _, cd, _ = project_cl_cd_stats(proj.root / "analysis" / "FENSAP")

        runs.append((h, cl, cd, proj))
    return runs


def fensap_runtime(proj: Project) -> float:
    """Return execution time in seconds for the FENSAP_RUN job."""
    log_file = proj.root / "run_FENSAP" / ".solvercmd.out"
    if log_file.exists():
        try:
            return execution_time(log_file)
        except Exception:
            return float("nan")
    return float("nan")


def gci_analysis2(
    runs: list[tuple[float, float, float, Project]],
    out_dir: Path,
) -> tuple[tuple, list[tuple], Project]:
    """Compute sliding-window GCI statistics for all grids and create summary plots + PDF report.

    The analysis calculates the efficiency index ``E`` for both lift and drag
    GCIs.  Validity is determined separately for lift (CL) and drag (CD): a
    coefficient is invalid when the observed order ``p`` or the corresponding GCI
    is negative or ``NaN``.  Triplets may therefore be partially valid when only
    one coefficient fails.  The recommended grid is chosen based on the lowest
    valid ``E`` for lift; drag values are reported for reference.

    Returns a tuple ``(best_triplet, sliding_results, best_proj)`` where
    ``best_proj`` is the project matching the smallest grid spacing ``h`` from
    ``best_triplet``.
    """
    if not runs:
        log.error("No completed runs found.")
        return

    # Sort fine → coarse (smallest h = finest grid)
    runs.sort(key=lambda t: t[0])
    h_vals = [r[0] for r in runs]
    cl_vals = [r[1] for r in runs]
    cd_vals = [r[2] for r in runs]
    runtimes = [fensap_runtime(r[3]) for r in runs]

    # Collect basic run information for reporting
    run_table = [
        (proj.uid, h, cl, cd) for h, cl, cd, proj in runs
    ]

    out_dir.mkdir(parents=True, exist_ok=True)

    # === Sliding 3-grid Richardson analysis ===
    if len(runs) < 3:
        log.error("At least three grids are required for GCI analysis.")
        return

    sliding_results = (
        []
    )  # tuples: (h, p_cl, p_cd, cl_ext, cd_ext, gci_cl, gci_cd, time, e_cl, e_cd, valid_cl, valid_cd)
    Fs = 1.25  # Safety factor

    best_idx_cl: int | None = None
    best_idx_cd: int | None = None
    best_e_cl = float("inf")
    best_e_cd = float("inf")
    for i in range(len(runs) - 2):
        # Take triplet G_i (fine), G_{i+1} (medium), G_{i+2} (coarse)
        f1, phi1_cl, phi1_cd, _ = runs[i]
        f2, phi2_cl, phi2_cd, _ = runs[i + 1]
        f3, phi3_cl, phi3_cd, _ = runs[i + 2]
        r = f2 / f1  # > 1, since f2 is coarser

        # Observed order of accuracy p
        try:
            p_cl = math.log(abs(phi3_cl - phi2_cl) / abs(phi2_cl - phi1_cl)) / math.log(
                r
            )
        except (ZeroDivisionError, ValueError, OverflowError, FloatingPointError):
            p_cl = nan

        try:
            p_cd = math.log(abs(phi3_cd - phi2_cd) / abs(phi2_cd - phi1_cd)) / math.log(
                r
            )
        except (ZeroDivisionError, ValueError, OverflowError, FloatingPointError):
            p_cd = nan

        try:
            cl_ext = phi1_cl + (phi1_cl - phi2_cl) / (r**p_cl - 1)
        except (ZeroDivisionError, ValueError, OverflowError, FloatingPointError):
            cl_ext = nan

        try:
            cd_ext = phi1_cd + (phi1_cd - phi2_cd) / (r**p_cd - 1)
        except (ZeroDivisionError, ValueError, OverflowError, FloatingPointError):
            cd_ext = nan

        # GCI between finest & next-finer grid
        try:
            gci_cl = (
                Fs * abs(phi2_cl - phi1_cl) / (abs(phi1_cl) * (r**p_cl - 1)) * 100.0
            )
        except (ZeroDivisionError, ValueError, OverflowError, FloatingPointError):
            gci_cl = nan

        try:
            gci_cd = (
                Fs * abs(phi2_cd - phi1_cd) / (abs(phi1_cd) * (r**p_cd - 1)) * 100.0
            )
        except (ZeroDivisionError, ValueError, OverflowError, FloatingPointError):
            gci_cd = nan

        t = runtimes[i]

        valid_cl = not (
            p_cl != p_cl or p_cl < 0 or gci_cl != gci_cl or gci_cl < 0
        )
        valid_cd = not (
            p_cd != p_cd or p_cd < 0 or gci_cd != gci_cd or gci_cd < 0
        )

        e_cl = gci_cl * t if t == t and valid_cl else float("inf")
        e_cd = gci_cd * t if t == t and valid_cd else float("inf")

        if valid_cl and e_cl < best_e_cl:
            best_e_cl = e_cl
            best_idx_cl = i

        if valid_cd and e_cd < best_e_cd:
            best_e_cd = e_cd
            best_idx_cd = i

        sliding_results.append(
            (
                f1,
                p_cl,
                p_cd,
                cl_ext,
                cd_ext,
                gci_cl,
                gci_cd,
                t,
                e_cl,
                e_cd,
                valid_cl,
                valid_cd,
            )
        )

    # === Basic plots (log h) ===
    plt.figure()
    plt.plot(h_vals, cl_vals, marker="o")
    plt.xscale("log")
    plt.xlabel("h (log scale)")
    plt.ylabel("CL")
    plt.tight_layout()
    plt.savefig(out_dir / "cl_vs_h.png")
    plt.close()

    plt.figure()
    plt.plot(h_vals, cd_vals, marker="o")
    plt.xscale("log")
    plt.xlabel("h (log scale)")
    plt.ylabel("CD")
    plt.tight_layout()
    plt.savefig(out_dir / "cd_vs_h.png")
    plt.close()

    # === Log the sliding analysis ===
    log.info("Sliding-window GCI analysis (per 3-grid triplet):")
    for (
        f1,
        p_cl,
        p_cd,
        cl_ext,
        cd_ext,
        gci_cl,
        gci_cd,
        t,
        e_cl,
        e_cd,
        valid_cl,
        valid_cd,
    ) in sliding_results:
        log.info(
            f"h={f1}: p(CL)={p_cl:.3f}, p(CD)={p_cd:.3f}, "
            f"CL∞={cl_ext:.6f}, CD∞={cd_ext:.6f}, "
            f"GCI(CL)={gci_cl:.2f}%, GCI(CD)={gci_cd:.2f}%, "
            f"time={t:.1f}s, E(CL)={e_cl:.2f}, E(CD)={e_cd:.2f}, "
            f"valid_CL={valid_cl}, valid_CD={valid_cd}"
        )

    # === Extract evolution of p and extrapolated solution ===
    h_levels = [res[0] for res in sliding_results]
    p_cl_vals = [res[1] for res in sliding_results]
    p_cd_vals = [res[2] for res in sliding_results]
    cl_ext_vals = [res[3] for res in sliding_results]
    cd_ext_vals = [res[4] for res in sliding_results]

    # Plot p evolution
    plt.figure()
    plt.plot(h_levels, p_cl_vals, marker="o")
    plt.plot(h_levels, p_cd_vals, marker="s")
    plt.xscale("log")
    plt.xlabel("h (log scale)")
    plt.ylabel("Observed Order p")
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(out_dir / "order_of_accuracy_vs_h.png")
    plt.close()

    # Plot extrapolated solution evolution
    plt.figure()
    plt.plot(h_levels, cl_ext_vals, marker="o")
    plt.plot(h_levels, cd_ext_vals, marker="s")
    plt.xscale("log")
    plt.xlabel("h (log scale)")
    plt.ylabel("Extrapolated infinite-grid value")
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(out_dir / "extrapolated_solution_vs_h.png")
    plt.close()

    # === Pick triplet with lowest efficiency index ===
    if best_idx_cl is None:
        best_idx_cl = 0
    if best_idx_cd is None:
        best_idx_cd = 0

    best_triplet = sliding_results[best_idx_cl]
    (
        best_h,
        best_p_cl,
        best_p_cd,
        best_cl_ext,
        best_cd_ext,
        best_gci_cl,
        best_gci_cd,
        best_time,
        best_e_cl,
        best_e_cd,
        _,
        _,
    ) = best_triplet

    best_proj = next(
        (proj for h, _, _, proj in runs if h == best_h),
        None,
    )

    log.info("\nRecommended grid:")
    log.info(f"Order p (CL)={best_p_cl:.3f}, p (CD)={best_p_cd:.3f}")
    log.info(f"CL∞={best_cl_ext:.6f}, CD∞={best_cd_ext:.6f}")
    log.info(
        f"GCI(CL)={best_gci_cl:.2f}%, GCI(CD)={best_gci_cd:.2f}%, "
        f"time={best_time:.1f}s, E(CL)={best_e_cl:.2f}, E(CD)={best_e_cd:.2f}"
    )

    # === Create PDF report including the detailed table ===
    report_path = out_dir / "grid_convergence_report.pdf"
    generate_gci_pdf_report(
        out_pdf=report_path,
        cl_ext=best_cl_ext,
        cd_ext=best_cd_ext,
        p_cl=best_p_cl,
        p_cd=best_p_cd,
        best_gci=best_gci_cl,  # we take CL GCI as main reference
        best_h=best_h,
        best_e_cl=best_e_cl,
        best_e_cd=best_e_cd,
        plots_dir=out_dir,
        sliding_results=sliding_results,  # include full table in report
        run_table=run_table,
    )

    return best_triplet, sliding_results, best_proj


def generate_gci_pdf_report(
    out_pdf: Path,
    cl_ext: float,
    cd_ext: float,
    p_cl: float,
    p_cd: float,
    best_gci: float,
    best_h: float,
    best_e_cl: float,
    best_e_cd: float,
    plots_dir: Path,
    sliding_results: list[tuple] | None = None,
    run_table: list[tuple[str, float, float, float]] | None = None,
):
    """
    Create a PDF report summarizing the grid dependency study.

    Parameters
    ----------
    out_pdf:
        Destination PDF path.
    cl_ext / cd_ext:
        Richardson extrapolated coefficients.
    p_cl / p_cd:
        Observed order of accuracy.
    best_gci:
        Best grid convergence index (CL).
    best_h:
        Grid spacing h of the recommended grid.
    best_e_cl / best_e_cd:
        Efficiency indices for CL and CD of the recommended grid.
    plots_dir:
        Directory containing generated plots.
    sliding_results:
        Optional table of all triplet results.
    run_table:
        Optional list of raw run data ``(UID, h, CL, CD)``.
    """
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(
        Paragraph("<b>Grid Convergence Study & GCI Analysis</b>", styles["Title"])
    )
    story.append(Spacer(1, 0.5 * cm))

    # Intro
    intro_text = """
    This report summarizes a grid dependency study using the Grid Convergence Index (GCI) method.
    The study evaluates the impact of mesh refinement on the aerodynamic coefficients (CL, CD).
    Three levels of refinement were used to estimate the observed order of accuracy and extrapolate
    the infinite-grid solution using Richardson extrapolation.
    """
    story.append(Paragraph(intro_text, styles["BodyText"]))
    story.append(Spacer(1, 0.3 * cm))

    # Formulas
    formulas_text = """
    <b>Richardson Extrapolation</b><br/>
    For a quantity &phi; on the finest (1) and next-coarser (2) grids with refinement ratio r and
    observed order p, the infinite-grid solution is:<br/>
    <br/>
    &phi;<sub>ext</sub> = &phi;<sub>1</sub> + ( &phi;<sub>1</sub> - &phi;<sub>2</sub> ) / ( r<sup>p</sup> - 1 )<br/>
    <br/>
    <b>Observed Order of Accuracy</b><br/>
    p = ln( ( &phi;<sub>3</sub> - &phi;<sub>2</sub> ) / ( &phi;<sub>2</sub> - &phi;<sub>1</sub> ) ) / ln(r)<br/>
    <br/>
    <b>Grid Convergence Index (GCI)</b><br/>
    GCI = F<sub>s</sub> * | &phi;<sub>coarse</sub> - &phi;<sub>fine</sub> | / ( |&phi;<sub>fine</sub>| * (r<sup>p</sup> - 1) ) * 100%
    """
    story.append(Paragraph(formulas_text, styles["BodyText"]))
    story.append(Spacer(1, 0.4 * cm))

    # Results section
    results_text = f"""
    <b>Observed order of accuracy</b><br/>
    p (CL) = {p_cl:.3f}<br/>
    p (CD) = {p_cd:.3f}<br/><br/>

    <b>Richardson extrapolated infinite-grid solutions</b><br/>
    CL∞ = {cl_ext:.6f}<br/>
    CD∞ = {cd_ext:.6f}<br/><br/>

    <b>Lowest E(CL)</b>: {best_e_cl:.2f} at h = {best_h}<br/>
    <b>E(CD)</b>: {best_e_cd:.2f}
    """
    story.append(Paragraph(results_text, styles["BodyText"]))
    story.append(Spacer(1, 0.5 * cm))

    # Insert plots
    cl_plot_path = plots_dir / "cl_vs_h.png"
    cd_plot_path = plots_dir / "cd_vs_h.png"
    if cl_plot_path.exists():
        story.append(Paragraph("<b>CL vs h</b>", styles["Heading2"]))
        story.append(Image(str(cl_plot_path), width=14 * cm, height=8 * cm))
        story.append(Spacer(1, 0.5 * cm))
    if cd_plot_path.exists():
        story.append(Paragraph("<b>CD vs h</b>", styles["Heading2"]))
        story.append(Image(str(cd_plot_path), width=14 * cm, height=8 * cm))
        story.append(Spacer(1, 0.5 * cm))

    # Run summary table
    if run_table:
        story.append(Paragraph("<b>Run Summary</b>", styles["Heading2"]))
        summary_data = [["UID", "h", "CL", "CD"]]
        for uid, h, cl, cd in run_table:
            summary_data.append(
                [uid, f"{h:.4f}", f"{cl:.6f}", f"{cd:.6f}"]
            )
        t = Table(summary_data, hAlign="LEFT")
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 0.5 * cm))

    # Detailed convergence results
    if sliding_results:
        story.append(
            Paragraph("<b>Detailed Grid Convergence Table</b>", styles["Heading2"])
        )
        table_data = [
            [
                "h",
                "p(CL)",
                "p(CD)",
                "CL∞",
                "CD∞",
                "GCI(CL)%",
                "GCI(CD)%",
                "time [s]",
                "E(CL)",
                "E(CD)",
                "valid_CL",
                "valid_CD",
            ]
        ]
        for (
            f1,
            pcl,
            pcd,
            cl_inf,
            cd_inf,
            gci_cl,
            gci_cd,
            t,
            e_cl,
            e_cd,
            valid_cl,
            valid_cd,
        ) in sliding_results:
            table_data.append(
                [
                    f"{f1:.4f}",
                    f"{pcl:.3f}",
                    f"{pcd:.3f}",
                    f"{cl_inf:.6f}",
                    f"{cd_inf:.6f}",
                    f"{gci_cl:.2f}",
                    f"{gci_cd:.2f}",
                    f"{t:.1f}",
                    f"{e_cl:.2f}",
                    f"{e_cd:.2f}",
                    str(valid_cl),
                    str(valid_cd),
                ]
            )

        t = Table(table_data, hAlign="LEFT")
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 0.5 * cm))

    # Conclusion
    conclusion_text = """
    Based on the observed order of accuracy and Richardson extrapolation, the infinite-grid solutions
    were estimated. The lowest GCI indicates the recommended grid spacing h for further studies.
    """
    story.append(Paragraph(conclusion_text, styles["BodyText"]))

    # Build PDF
    doc = SimpleDocTemplate(str(out_pdf), pagesize=A4)
    doc.build(story)
    print(f"✅ PDF report created: {out_pdf}")


def main(base_dir: Path | str = Path("")) -> None:
    base = Path(base_dir)
    root = base / "01_grid_dependency_study"
    runs = load_runs(root)
    gci_analysis2(runs, base / "02_grid_dependency_results")


if __name__ == "__main__":
    main()
