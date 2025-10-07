"""
Perform GCI analysis for the full power study.

The script aggregates results from grid-refinement runs, computes
sliding-window Grid Convergence Index (GCI) statistics and produces
plots along with a PDF summary report.

Key Functions
-------------
* load_runs – collect run metadata.
* gci_analysis2 – perform the GCI calculations and plotting.
* generate_gci_pdf_report – render a PDF summary.
* main – command line entry point.

Inputs
------
base_dir : Path | str, optional
    Directory containing ``01_grid_dependency_study`` runs.

Outputs
-------
Plots and ``grid_convergence_report.pdf`` in ``02_grid_dependency_results``.

Usage
-----
python scripts/02_full_power_gci.py

See Also
--------
docs/full_power_study.rst for a complete workflow walkthrough.
"""

from __future__ import annotations

from pathlib import Path
import math
import subprocess
import sys
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, LogFormatterMathtext, NullFormatter

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


# --- Plot styling helpers -----------------------------------------------------
def set_scientific_style():
    """Apply a consistent, paper-ready Matplotlib style."""
    plt.rcParams.update({
        "figure.figsize": (6.0, 3.8),
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.linestyle": "--",
        "grid.linewidth": 0.5,
        "grid.alpha": 0.35,
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "lines.linewidth": 1.2,
        "lines.markersize": 5.5,
        "pdf.fonttype": 42,  # editable text in vector outputs
        "ps.fonttype": 42,
    })


def format_log_x_axis(ax, num_major: int = 8):
    """Format the x-axis as log10 with clean major/minor ticks."""
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(LogLocator(base=10.0, numticks=num_major))
    ax.xaxis.set_major_formatter(LogFormatterMathtext())
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=tuple(range(2, 10)), numticks=100))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.tick_params(axis="both", which="both", direction="in", top=True, right=True)


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

    set_scientific_style()  # apply unified figure style

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

    sliding_results = []
    # tuples: (h1, h2, h3, cl1, cl2, cl3, cd1, cd2, cd3, p_cl, p_cd, cl_ext, cd_ext,
    #          gci_cl, gci_cd, time, e_cl, e_cd, valid_cl, valid_cd)
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
            p_cl = math.log(abs(phi3_cl - phi2_cl) / abs(phi2_cl - phi1_cl)) / math.log(r)
        except (ZeroDivisionError, ValueError, OverflowError, FloatingPointError):
            p_cl = nan

        try:
            p_cd = math.log(abs(phi3_cd - phi2_cd) / abs(phi2_cd - phi1_cd)) / math.log(r)
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
            gci_cl = Fs * abs(phi2_cl - phi1_cl) / (abs(phi1_cl) * (r**p_cl - 1)) * 100.0
        except (ZeroDivisionError, ValueError, OverflowError, FloatingPointError):
            gci_cl = nan

        try:
            gci_cd = Fs * abs(phi2_cd - phi1_cd) / (abs(phi1_cd) * (r**p_cd - 1)) * 100.0
        except (ZeroDivisionError, ValueError, OverflowError, FloatingPointError):
            gci_cd = nan

        t = runtimes[i]

        valid_cl = not (p_cl != p_cl or p_cl < 0 or gci_cl != gci_cl or gci_cl < 0)
        valid_cd = not (p_cd != p_cd or p_cd < 0 or gci_cd != gci_cd or gci_cd < 0)

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
                f1, f2, f3,
                phi1_cl, phi2_cl, phi3_cl,
                phi1_cd, phi2_cd, phi3_cd,
                p_cl, p_cd, cl_ext, cd_ext,
                gci_cl, gci_cd, t, e_cl, e_cd,
                valid_cl, valid_cd,
            )
        )

    # === CL vs h (log-x) ===
    fig, ax = plt.subplots()
    ax.plot(
        h_vals, cl_vals,
        marker="o", markerfacecolor="white", markeredgewidth=1.0,
        label=r"$C_L$"
    )
    format_log_x_axis(ax)
    ax.set_xlabel(r"$h$")
    ax.set_ylabel(r"$C_L$")
    ax.legend(frameon=False, handlelength=2.5)
    fig.tight_layout()
    fig.savefig(out_dir / "cl_vs_h.png")
    fig.savefig(out_dir / "cl_vs_h.pdf")
    plt.close(fig)

    # === CD vs h (log-x) ===
    fig, ax = plt.subplots()
    ax.plot(
        h_vals, cd_vals,
        marker="s", markerfacecolor="white", markeredgewidth=1.0,
        label=r"$C_D$"
    )
    format_log_x_axis(ax)
    ax.set_xlabel(r"$h$")
    ax.set_ylabel(r"$C_D$")
    ax.legend(frameon=False, handlelength=2.5)
    fig.tight_layout()
    fig.savefig(out_dir / "cd_vs_h.png")
    fig.savefig(out_dir / "cd_vs_h.pdf")
    plt.close(fig)

    # === Extract evolution of p and extrapolated solution ===
    h_levels = [res[0] for res in sliding_results]
    p_cl_vals = [res[9] for res in sliding_results]
    p_cd_vals = [res[10] for res in sliding_results]
    cl_ext_vals = [res[11] for res in sliding_results]
    cd_ext_vals = [res[12] for res in sliding_results]

    # Observed order p vs h (log-x)
    fig, ax = plt.subplots()
    ax.plot(
        h_levels, p_cl_vals,
        marker="o", markerfacecolor="white", markeredgewidth=1.0,
        label=r"$p(C_L)$"
    )
    ax.plot(
        h_levels, p_cd_vals,
        marker="^", markerfacecolor="white", markeredgewidth=1.0,
        label=r"$p(C_D)$"
    )
    format_log_x_axis(ax)
    ax.set_xlabel(r"$h$")
    ax.set_ylabel(r"Observed order $p$")
    ax.legend(frameon=False, ncol=2, handlelength=2.5)
    fig.tight_layout()
    fig.savefig(out_dir / "order_of_accuracy_vs_h.png")
    fig.savefig(out_dir / "order_of_accuracy_vs_h.pdf")
    plt.close(fig)

    # Extrapolated infinite-grid value vs h (log-x)
    fig, ax = plt.subplots()
    ax.plot(
        h_levels, cl_ext_vals,
        marker="o", markerfacecolor="white", markeredgewidth=1.0,
        label=r"$C_{L,\infty}$"
    )
    ax.plot(
        h_levels, cd_ext_vals,
        marker="^", markerfacecolor="white", markeredgewidth=1.0,
        label=r"$C_{D,\infty}$"
    )
    format_log_x_axis(ax)
    ax.set_xlabel(r"$h$")
    ax.set_ylabel(r"Extrapolated $\phi_{\infty}$")
    ax.legend(frameon=False, ncol=2, handlelength=2.5)
    fig.tight_layout()
    fig.savefig(out_dir / "extrapolated_solution_vs_h.png")
    fig.savefig(out_dir / "extrapolated_solution_vs_h.pdf")
    plt.close(fig)

    # === Pick triplet with lowest efficiency index ===
    if best_idx_cl is None:
        best_idx_cl = 0
    if best_idx_cd is None:
        best_idx_cd = 0

    best_triplet = sliding_results[best_idx_cl]
    (
        best_h, _, _,
        _, _, _,
        _, _, _,
        best_p_cl, best_p_cd,
        best_cl_ext, best_cd_ext,
        best_gci_cl, best_gci_cd,
        best_time, best_e_cl, best_e_cd,
        _, _,
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
        best_gci=best_gci_cl,  # take CL GCI as main reference
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
    """
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("<b>Grid Convergence Study & GCI Analysis</b>", styles["Title"]))
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
    observed order p, the infinite-grid solution is:<br/><br/>
    &phi;<sub>ext</sub> = &phi;<sub>1</sub> + ( &phi;<sub>1</sub> - &phi;<sub>2</sub> ) / ( r<sup>p</sup> - 1 )<br/><br/>
    <b>Observed Order of Accuracy</b><br/>
    p = ln( ( &phi;<sub>3</sub> - &phi;<sub>2</sub> ) / ( &phi;<sub>2</sub> - &phi;<sub>1</sub> ) ) / ln(r)<br/><br/>
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
            summary_data.append([uid, f"{h:.4f}", f"{cl:.6f}", f"{cd:.6f}"])
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
        story.append(Paragraph("<b>Detailed Grid Convergence Table</b>", styles["Heading2"]))
        table_data = [[
            "h1","h2","h3","CL1","CL2","CL3","CD1","CD2","CD3",
            "p(CL)","p(CD)","CL∞","CD∞","GCI(CL)%","GCI(CD)%","time [s]","E(CL)","E(CD)","valid_CL","valid_CD"
        ]]
        for (
            h1, h2, h3,
            cl1, cl2, cl3,
            cd1, cd2, cd3,
            pcl, pcd, cl_inf, cd_inf,
            gci_cl, gci_cd, t, e_cl, e_cd, valid_cl, valid_cd,
        ) in sliding_results:
            table_data.append([
                f"{h1:.4f}", f"{h2:.4f}", f"{h3:.4f}",
                f"{cl1:.6f}", f"{cl2:.6f}", f"{cl3:.6f}",
                f"{cd1:.6f}", f"{cd2:.6f}", f"{cd3:.6f}",
                f"{pcl:.3f}", f"{pcd:.3f}",
                f"{cl_inf:.6f}", f"{cd_inf:.6f}",
                f"{gci_cl:.2f}", f"{gci_cd:.2f}",
                f"{t:.1f}", f"{e_cl:.2f}", f"{e_cd:.2f}",
                str(valid_cl), str(valid_cd),
            ])

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
