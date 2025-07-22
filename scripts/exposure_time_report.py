# appendix_c_report.py  – Generate PDF report with Appendix C exposure‑time plot and LaTeX‑rendered formulas
"""Generate a two‑page PDF report:
    • Page 1 – Exposure‑time curves vs. horizontal flight speed for Appendix C standard extents
    • Page 2 – Key formulas rendered with LaTeX

Usage (default speeds 20 m/s and 50 m/s):
    python appendix_c_report.py

Optional custom speeds (comma‑separated list in m/s):
    python appendix_c_report.py 15,40,60

The script produces 'appendix_c_report.pdf' in the current directory.
"""

from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# ────────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────────
NM_TO_M = 1852                       # metres per nautical mile
S_CONT_NM = 17.4                     # Continuous‑maximum extent [NM]
S_INT_NM  = 2.6                      # Intermittent‑maximum extent [NM]
PDF_NAME  = Path("appendix_c_report.pdf")

# Parse speeds given on the command line ---------------------------------------
if len(sys.argv) > 1:
    try:
        speeds_mark = np.array([float(v) for v in sys.argv[1].split(',') if v], dtype=float)
    except ValueError as exc:
        raise SystemExit(f"Invalid speed list: {exc}")
else:
    speeds_mark = np.array([20.0, 50.0])          # default speeds in m s⁻¹

# Derived constants -------------------------------------------------------------
S_CONT_M = S_CONT_NM * NM_TO_M
S_INT_M  = S_INT_NM  * NM_TO_M

# Continuous speed grid for smooth curves
V_GRID = np.linspace(10, 70, 400)                 # m s⁻¹

t_cont = (S_CONT_M / V_GRID) / 60.0               # minutes
t_int  = (S_INT_M  / V_GRID) / 60.0               # minutes

# ────────────────────────────────────────────────────────────────────────────────
# Page 1 – Exposure‑time curves
# ────────────────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "text.usetex": False,   # switch to True if a full LaTeX installation is present
    "font.size": 11,
})

fig1, ax = plt.subplots(figsize=(8, 5))
ax.plot(V_GRID, t_cont, label=f"Continuous Max {S_CONT_NM} NM")
ax.plot(V_GRID, t_int,  label=f"Intermittent Max {S_INT_NM} NM")

for v in speeds_mark:
    ax.scatter(v, (S_CONT_M / v) / 60.0, marker="o", zorder=3)
    ax.scatter(v, (S_INT_M  / v) / 60.0, marker="s", zorder=3)

ax.set_xlabel(r"Horizontal Flight Speed $V\,[\mathrm{m\,s^{-1}}]$")
ax.set_ylabel(r"Exposure Time $t\,[\mathrm{min}]$")
ax.set_title("Exposure Time versus Horizontal Speed\n(Appendix C Standard Extents)")
ax.grid(True)
ax.legend()
fig1.tight_layout()

# ────────────────────────────────────────────────────────────────────────────────
# Page 2 – Key formulas (LaTeX rendered via mathtext)
# ────────────────────────────────────────────────────────────────────────────────
fig2 = plt.figure(figsize=(8, 5))
ax2 = fig2.add_subplot(111)
ax2.axis("off")

# Heading (plain text, bold)
ax2.text(0.5, 0.9, "Key Formulas", ha="center", va="center",
         fontsize=16, fontweight="bold", transform=ax2.transAxes)

# Formulas ----------------------------------------------------------------------
line_y = 0.7
line_dy = 0.15

ax2.text(0.5, line_y,   rf"$s_{{\mathrm{{cont}}}} = {S_CONT_NM}\,\mathrm{{NM}} \;\approx\; {S_CONT_M:,.0f}\,\mathrm{{m}}$",
         ha="center", va="center", fontsize=14, transform=ax2.transAxes)
ax2.text(0.5, line_y - line_dy, rf"$s_{{\mathrm{{int}}}}  = {S_INT_NM}\,\mathrm{{NM}} \;\approx\; {S_INT_M:,.0f}\,\mathrm{{m}}$",
         ha="center", va="center", fontsize=14, transform=ax2.transAxes)
ax2.text(0.5, line_y - 2*line_dy, r"$t = \dfrac{s}{V}$",
         ha="center", va="center", fontsize=14, transform=ax2.transAxes)

# ────────────────────────────────────────────────────────────────────────────────
# Write PDF
# ────────────────────────────────────────────────────────────────────────────────
with PdfPages(PDF_NAME) as pdf:
    pdf.savefig(fig1)
    pdf.savefig(fig2)

print(f"Report written to: {PDF_NAME.resolve()}")