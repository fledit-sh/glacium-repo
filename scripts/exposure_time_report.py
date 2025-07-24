#!/usr/bin/env python3
"""
Generate a two-page PDF report with:
  • Page 1 – Exposure-time curves vs. horizontal flight speed (Appendix C)
  • Page 2 – Key formulas rendered with LaTeX-like mathtext

Usage:
    python appendix_c_report.py
    python appendix_c_report.py 15,40,60

Produces 'appendix_c_report.pdf'
"""

from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import scienceplots
plt.style.use(["science", "ieee"])

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# ────────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────────
NM_TO_M = 1852                       # metres per nautical mile
S_CONT_NM = 17.4                     # Continuous-maximum extent [NM]
S_INT_NM  = 2.6                      # Intermittent-maximum extent [NM]
PDF_NAME  = Path("appendix_c_report.pdf")
PLOT_PNG  = Path("appendix_c_plot.png")

# Temporary mathtext-rendered formula images
FORMULA_PNGS = [
    Path("formula_s_cont.png"),
    Path("formula_s_int.png"),
    Path("formula_t.png")
]

# Parse speeds from CLI ---------------------------------------------------------
if len(sys.argv) > 1:
    try:
        speeds_mark = np.array([float(v) for v in sys.argv[1].split(',') if v], dtype=float)
    except ValueError as exc:
        raise SystemExit(f"Invalid speed list: {exc}")
else:
    speeds_mark = np.array([20.0, 50.0])  # default speeds in m/s

# Derived constants -------------------------------------------------------------
S_CONT_M = S_CONT_NM * NM_TO_M
S_INT_M  = S_INT_NM  * NM_TO_M

V_GRID = np.linspace(10, 70, 400)  # m/s

t_cont = (S_CONT_M / V_GRID) / 60.0  # minutes
t_int  = (S_INT_M  / V_GRID) / 60.0  # minutes

# ────────────────────────────────────────────────────────────────────────────────
# Generate the exposure-time plot and save as PNG
# ────────────────────────────────────────────────────────────────────────────────
from matplotlib.ticker import MultipleLocator


def make_exposure_plot():
    plt.rcParams.update({
        "text.usetex": False,
        "font.size": 11,
    })

    # Existing exposure times in minutes
    t_cont_min = (S_CONT_M / V_GRID) / 60.0
    t_int_min = (S_INT_M / V_GRID) / 60.0

    # Also in seconds
    t_cont_sec = S_CONT_M / V_GRID
    t_int_sec = S_INT_M / V_GRID

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(V_GRID, t_cont_min, label=f"Continuous {S_CONT_NM} NM", color="black")
    ax1.plot(V_GRID, t_int_min, label=f"Intermittent {S_INT_NM} NM", color="black")

    # Labeling
    ax1.set_xlabel("Horizontal Flight Speed [m/s]")
    ax1.set_ylabel("Exposure Time [min]")
    ax1.set_title("Exposure Time vs Horizontal Speed\n(Appendix C Standard Extents)")

    # More grid ticks using MultipleLocator
    ax1.xaxis.set_major_locator(MultipleLocator(5))  # major ticks every 5 m/s
    ax1.xaxis.set_minor_locator(MultipleLocator(1))  # minor ticks every 1 m/s
    ax1.yaxis.set_major_locator(MultipleLocator(4))  # major ticks every 2 min
    ax1.yaxis.set_minor_locator(MultipleLocator(2))  # minor ticks every 0.5 min
    ax1.set_xlim(10,70)
    ax1.set_ylim(0,48)
    ax1.grid(True, which="both", linestyle="--", alpha=0.6)
    ax1.legend(loc="upper right")

    # Second y-axis for seconds
    ax2 = ax1.twinx()
    ax2.set_ylabel("Exposure Time [s]")
    # keep seconds in sync with minutes
    y_min, y_max = ax1.get_ylim()
    ax2.set_ylim(y_min * 60, y_max * 60)

    # Annotate the selected speeds
    for v in speeds_mark:
        # Compute times
        t_c_min = (S_CONT_M / v) / 60.0
        t_i_min = (S_INT_M / v) / 60.0
        t_c_sec = S_CONT_M / v
        t_i_sec = S_INT_M / v

        # Scatter points
        ax1.scatter(v, t_c_min, marker="+", color="red", zorder=4)
        ax1.scatter(v, t_i_min, marker="+", color="blue", zorder=4)

        # Annotate (slightly offset)
        ax1.annotate(
            f"{v:.0f} m/s\n{t_c_sec:.1f} s\n({t_c_min:.1f} min)",
            (v, t_c_min),
            textcoords="offset points",
            xytext=(+10, +5),
            fontsize=9,
            color="red",
            arrowprops=dict(arrowstyle="->", lw=0.5, color="red")
        )
        ax1.annotate(
            f"{v:.0f} m/s\n{t_i_sec:.1f} s\n({t_i_min:.1f} min)",
            (v, t_i_min),
            textcoords="offset points",
            xytext=(+10, +5),
            fontsize=9,
            color="blue",
            arrowprops=dict(arrowstyle="->", lw=0.5, color="blue")
        )

    fig.tight_layout()
    fig.savefig(PLOT_PNG, dpi=1200)
    plt.close(fig)


# ────────────────────────────────────────────────────────────────────────────────
# Render a LaTeX/mathtext formula to PNG using matplotlib
# ────────────────────────────────────────────────────────────────────────────────
def render_formula(formula: str, outfile: Path, fontsize: int = 24):
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0.5, 0.5, f"${formula}$", ha="center", va="center", fontsize=fontsize)
    fig.savefig(outfile, dpi=200, transparent=True, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)

def make_formula_images():
    # LaTeX-style formulas
    f1 = rf"s_{{\mathrm{{cont}}}} = {S_CONT_NM}\,\mathrm{{NM}} \approx {S_CONT_M:,.0f}\,\mathrm{{m}}"
    f2 = rf"s_{{\mathrm{{int}}}} = {S_INT_NM}\,\mathrm{{NM}} \approx {S_INT_M:,.0f}\,\mathrm{{m}}"
    f3 = r"t = \dfrac{s}{V}"

    formulas = [f1, f2, f3]

    for formula, png in zip(formulas, FORMULA_PNGS):
        render_formula(formula, png)

# ────────────────────────────────────────────────────────────────────────────────
# Build PDF with ReportLab (A4)
# ────────────────────────────────────────────────────────────────────────────────
PAGE_WIDTH, PAGE_HEIGHT = A4

def build_pdf():
    c = canvas.Canvas(str(PDF_NAME), pagesize=A4)

    # Title at top
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT - 2*cm, "Appendix C Exposure-Time Report")

    # ───── Plot section ─────
    img_width = 14*cm
    img_height = 9*cm
    img_x = (PAGE_WIDTH - img_width)/2
    img_y = PAGE_HEIGHT - 2*cm - img_height - 1*cm  # leave some space below title
    c.drawImage(str(PLOT_PNG), img_x, img_y, width=img_width, height=img_height)

    # Caption for plot
    c.setFont("Helvetica", 9)
    c.drawCentredString(
        PAGE_WIDTH/2,
        img_y - 0.4*cm,
        "Figure: Exposure time vs horizontal speed for Appendix C continuous & intermittent extents"
    )

    # ───── Formulas section ─────
    section_y = img_y - 2.5*cm  # Start a bit lower after plot
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(PAGE_WIDTH/2, section_y, "Key Formulas")

    # Load formula images and normalize scaling
    from PIL import Image as PILImage
    widths = []
    heights = []
    for f_png in FORMULA_PNGS:
        with PILImage.open(f_png) as im:
            w, h = im.size
            widths.append(w)
            heights.append(h)
    max_w = max(widths)

    target_pdf_width = 8 * cm  # smaller width to fit neatly
    scale_factors = [target_pdf_width / max_w] * len(FORMULA_PNGS)

    # Place formulas centered
    y = section_y - 1.5*cm
    gap = 0.7*cm
    for f_png, orig_h, scale in zip(FORMULA_PNGS, heights, scale_factors):
        scaled_h = orig_h * scale
        c.drawImage(
            str(f_png),
            (PAGE_WIDTH - target_pdf_width)/2,
            y - scaled_h,
            width=target_pdf_width,
            height=scaled_h,
            preserveAspectRatio=True,
            mask='auto'
        )
        y -= scaled_h + gap

    # ───── Explanatory text below formulas ─────
    explanation = (
        "Here, s_cont and s_int denote the maximum continuous and intermittent icing extents "
        "defined in Appendix C, converted from nautical miles (NM) to metres (m). "
        "The exposure time t for a given segment is obtained by dividing the distance s by the "
        "horizontal flight speed V."
    )
    text_y = y - 0.8*cm
    text_width = PAGE_WIDTH - 4*cm
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    # To render Paragraph into a fixed position
    from reportlab.platypus import Frame
    frame = Frame(2*cm, text_y-2*cm, text_width, 2*cm, showBoundary=0)
    story = [Paragraph(explanation, normal)]
    frame.addFromList(story, c)

    # Done
    c.showPage()
    c.save()
# ────────────────────────────────────────────────────────────────────────────────
# Cleanup temporary images
# ────────────────────────────────────────────────────────────────────────────────
def cleanup():
    for f in [PLOT_PNG] + FORMULA_PNGS:
        try:
            f.unlink()
        except FileNotFoundError:
            pass

# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    make_exposure_plot()
    make_formula_images()
    build_pdf()
    cleanup()
    print(f"Report written to: {PDF_NAME.resolve()}")
