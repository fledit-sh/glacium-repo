from __future__ import annotations

from pathlib import Path
import math
import matplotlib.pyplot as plt

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


def load_runs(root: Path) -> list[tuple[float, float, float, Project]]:
    """Return refinement factor, CL, CD and project for all runs."""
    pm = ProjectManager(root)
    runs: list[tuple[float, float, float, Project]] = []
    for uid in pm.list_uids():
        try:
            proj = Project.load(root, uid)
        except FileNotFoundError:
            continue
        try:
            factor = float(proj.get("PWS_REFINEMENT"))
        except Exception:
            continue

        try:
            cl = float(proj.get("LIFT_COEFFICIENT"))
            cd = float(proj.get("DRAG_COEFFICIENT"))
        except Exception:
            cl, _, cd, _ = project_cl_cd_stats(proj.root / "analysis" / "FENSAP")

        runs.append((factor, cl, cd, proj))
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

    Returns a tuple ``(best_triplet, sliding_results, best_proj)`` where ``best_proj``
    is the project matching the finest refinement from ``best_triplet``.
    """
    if not runs:
        log.error("No completed runs found.")
        return

    # Sort fine → coarse (smallest refinement factor = finest grid)
    runs.sort(key=lambda t: t[0])
    factors = [r[0] for r in runs]
    cl_vals = [r[1] for r in runs]
    cd_vals = [r[2] for r in runs]
    runtimes = [fensap_runtime(r[3]) for r in runs]

    out_dir.mkdir(parents=True, exist_ok=True)

    # === Basic plots (log refinement) ===
    plt.figure()
    plt.plot(factors, cl_vals, marker="o")
    plt.xscale("log")
    plt.xlabel("PWS_REFINEMENT (log scale)")
    plt.ylabel("CL")
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(out_dir / "cl_vs_refinement.png")
    plt.close()

    plt.figure()
    plt.plot(factors, cd_vals, marker="o")
    plt.xscale("log")
    plt.xlabel("PWS_REFINEMENT (log scale)")
    plt.ylabel("CD")
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(out_dir / "cd_vs_refinement.png")
    plt.close()

    # === Sliding 3-grid Richardson analysis ===
    if len(runs) < 3:
        log.error("At least three grids are required for GCI analysis.")
        return

    sliding_results = (
        []
    )  # tuples: (refinement, p_cl, p_cd, cl_ext, cd_ext, gci_cl, gci_cd, time, efficiency)
    Fs = 1.25  # Safety factor

    best_idx = 0
    best_e = float("inf")
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
        e = gci_cl * t if t == t and gci_cl == gci_cl else float("inf")
        if e < best_e:
            best_e = e
            best_idx = i

        sliding_results.append((f1, p_cl, p_cd, cl_ext, cd_ext, gci_cl, gci_cd, t, e))

    # === Log the sliding analysis ===
    log.info("Sliding-window GCI analysis (per 3-grid triplet):")
    for f1, p_cl, p_cd, cl_ext, cd_ext, gci_cl, gci_cd, t, e in sliding_results:
        log.info(
            f"Refinement={f1}: p(CL)={p_cl:.3f}, p(CD)={p_cd:.3f}, "
            f"CL∞={cl_ext:.6f}, CD∞={cd_ext:.6f}, "
            f"GCI(CL)={gci_cl:.2f}%, time={t:.1f}s, E={e:.2f}"
        )

    # === Extract evolution of p and extrapolated solution ===
    ref_levels = [res[0] for res in sliding_results]
    p_cl_vals = [res[1] for res in sliding_results]
    p_cd_vals = [res[2] for res in sliding_results]
    cl_ext_vals = [res[3] for res in sliding_results]
    cd_ext_vals = [res[4] for res in sliding_results]

    # Plot p evolution
    plt.figure()
    plt.plot(ref_levels, p_cl_vals, marker="o", label="Order p (CL)")
    plt.plot(ref_levels, p_cd_vals, marker="s", label="Order p (CD)")
    plt.xscale("log")
    plt.xlabel("PWS_REFINEMENT (log scale)")
    plt.ylabel("Observed Order p")
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "order_of_accuracy_vs_refinement.png")
    plt.close()

    # Plot extrapolated solution evolution
    plt.figure()
    plt.plot(ref_levels, cl_ext_vals, marker="o", label="CL∞ (Richardson ext.)")
    plt.plot(ref_levels, cd_ext_vals, marker="s", label="CD∞ (Richardson ext.)")
    plt.xscale("log")
    plt.xlabel("PWS_REFINEMENT (log scale)")
    plt.ylabel("Extrapolated infinite-grid value")
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "extrapolated_solution_vs_refinement.png")
    plt.close()

    # === Pick triplet with lowest efficiency index ===
    best_triplet = sliding_results[best_idx]
    (
        best_refinement,
        best_p_cl,
        best_p_cd,
        best_cl_ext,
        best_cd_ext,
        best_gci_cl,
        best_gci_cd,
        best_time,
        best_efficiency,
    ) = best_triplet

    best_proj = next(
        (proj for factor, _, _, proj in runs if factor == best_refinement),
        None,
    )

    log.info("\nRecommended grid:")
    log.info(f"Order p (CL)={best_p_cl:.3f}, p (CD)={best_p_cd:.3f}")
    log.info(f"CL∞={best_cl_ext:.6f}, CD∞={best_cd_ext:.6f}")
    log.info(
        f"GCI(CL)={best_gci_cl:.2f}%, GCI(CD)={best_gci_cd:.2f}%, "
        f"time={best_time:.1f}s, E={best_efficiency:.2f}"
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
        best_refinement=best_refinement,
        best_efficiency=best_efficiency,
        plots_dir=out_dir,
        sliding_results=sliding_results,  # include full table in report
    )

    return best_triplet, sliding_results, best_proj


def generate_gci_pdf_report(
    out_pdf: Path,
    cl_ext: float,
    cd_ext: float,
    p_cl: float,
    p_cd: float,
    best_gci: float,
    best_refinement: float,
    best_efficiency: float,
    plots_dir: Path,
    sliding_results: list[tuple] | None = None,  # <--- NEU
):
    """
    Creates a PDF report summarizing the grid dependency study.
    Includes formulas, a brief description of the method,
    and the generated refinement plots.
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

    <b>Lowest E</b>: {best_efficiency:.2f} for refinement {best_refinement}
    """
    story.append(Paragraph(results_text, styles["BodyText"]))
    story.append(Spacer(1, 0.5 * cm))

    # Insert plots
    cl_plot_path = plots_dir / "cl_vs_refinement.png"
    cd_plot_path = plots_dir / "cd_vs_refinement.png"
    if cl_plot_path.exists():
        story.append(Paragraph("<b>CL vs Refinement</b>", styles["Heading2"]))
        story.append(Image(str(cl_plot_path), width=14 * cm, height=8 * cm))
        story.append(Spacer(1, 0.5 * cm))
    if cd_plot_path.exists():
        story.append(Paragraph("<b>CD vs Refinement</b>", styles["Heading2"]))
        story.append(Image(str(cd_plot_path), width=14 * cm, height=8 * cm))
        story.append(Spacer(1, 0.5 * cm))

    # --- NEU: Tabelle mit sliding_results ---
    if sliding_results:
        story.append(
            Paragraph("<b>Detailed Grid Convergence Table</b>", styles["Heading2"])
        )
        table_data = [
            [
                "Refinement",
                "p(CL)",
                "p(CD)",
                "CL∞",
                "CD∞",
                "GCI(CL)%",
                "GCI(CD)%",
                "time [s]",
                "E",
            ]
        ]
        for f1, pcl, pcd, cl_inf, cd_inf, gci_cl, gci_cd, t, e in sliding_results:
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
                    f"{e:.2f}",
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
    were estimated. The lowest GCI indicates the recommended refinement level for further studies.
    """
    story.append(Paragraph(conclusion_text, styles["BodyText"]))

    # Build PDF
    doc = SimpleDocTemplate(str(out_pdf), pagesize=A4)
    doc.build(story)
    print(f"✅ PDF report created: {out_pdf}")


def main(base_dir: Path | str = Path("")) -> None:
    base = Path(base_dir)
    root = base / "GridDependencyStudy"
    runs = load_runs(root)
    gci_analysis2(runs, base / "grid_dependency_results")


if __name__ == "__main__":
    main()
