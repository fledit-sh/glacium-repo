# icing_results_report_fpdf2.py
"""
Generate a PDF containing only the **Results** section of the icing analysis
using the *fpdf2* library (https://github.com/PyFPDF/fpdf2).

Fixes compared to the first version
-----------------------------------
1. **Unicode support** — a TrueType font (DejaVuSans) is embedded so that the Greek letter
   β and en‑dash (–) render without errors.
2. **Deprecation warnings** — replaced `ln=True` with
   `new_x=XPos.LMARGIN, new_y=YPos.NEXT`.
3. **ASCII‑only fall‑back** — if the font file is missing, the script falls back to the core
   Helvetica font and automatically strips non‑ASCII characters, preventing crashes.

Place these four result images in the same directory (or adjust the paths):
  • ice_shape_sequence.png
  • CL_CD_vs_time.png
  • surface_temperature.png
  • beta_contour.png

Install dependencies:
    pip install fpdf2

Download font (if you do not already have it) and save as `DejaVuSans.ttf` in the same folder:
    https://dejavu-fonts.github.io/
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Tuple

from fpdf import FPDF, XPos, YPos

TITLE = "Icing Analysis – Results"  # en‑dash OK with Unicode font
AUTHOR = "Noel"
TODAY = datetime.now().strftime("%Y‑%m‑%d")
FONT_PATH = Path("DejaVuSans.ttf")  # Expected TTF; change path if needed

FIGURES: list[Tuple[str, str]] = [
    ("ice_shape_sequence.png", "Figure1 – Ice‑shape growth at t=0s, 60s, 300s, 600s."),
    ("CL_CD_vs_time.png", "Figure2 – Normalised coefficients C_L/C_L0 and C_D/C_D0 versus accretion time."),
    ("surface_temperature.png", "Figure3 – Surface temperature at final simulation timestep."),
    ("beta_contour.png", "Figure4 – Droplet collection efficiency β over the airfoil surface."),
]


def ascii_safe(text: str) -> str:
    """Remove characters outside Latin‑1 if not using Unicode font."""
    return re.sub(r"[^\x00-\xFF]", "?", text)


class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Try to load Unicode font first
        if FONT_PATH.is_file():
            self.add_font("DejaVuSans.ttf", "", str(FONT_PATH), uni=True)
            self.default_font_family = "DejaVuSans"
            self.unicode_ready = True
        else:
            self.default_font_family = "DejaVuSans"
            self.unicode_ready = False
            print("Warning: Unicode font not found — non‑ASCII characters will be replaced.")

    # -------------------------------------------------- Header / Footer
    def header(self):
        self.set_font(self.default_font_family, style="B", size=16)
        txt = TITLE if self.unicode_ready else ascii_safe(TITLE)
        self.cell(0, 10, txt, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        if self.page_no() == 1:
            self.ln(2)
            self.set_font(self.default_font_family, size=12)
            self.cell(0, 8, f"Author: {AUTHOR}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            self.cell(0, 8, f"Date: {TODAY}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            self.ln(4)
        else:
            self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.default_font_family, style="I", size=10)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    # -------------------------------------------------- Utility helpers
    def add_heading(self, txt: str, level: int = 1):
        sizes = {1: 14, 2: 12, 3: 11}
        style = "B" if level <= 2 else ""
        text = txt if self.unicode_ready else ascii_safe(txt)
        self.set_font(self.default_font_family, style=style, size=sizes.get(level, 11))
        self.multi_cell(0, 8, text)
        self.ln(2)

    def add_paragraph(self, txt: str):
        text = txt if self.unicode_ready else ascii_safe(txt)
        self.set_font(self.default_font_family, size=11)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def add_figure(self, path: str, caption: str, width: int = 160):
        img_path = Path(path)
        if img_path.is_file():
            self.image(str(img_path), w=width)
        else:
            # Placeholder if image not found
            self.set_font(self.default_font_family, style="I", size=11)
            self.set_fill_color(220, 220, 220)
            self.cell(width, 40, f"[Missing image: {img_path.name}]", border=1, fill=True, align="C")
            self.ln(1)
        cap_text = caption if self.unicode_ready else ascii_safe(caption)
        self.set_font(self.default_font_family, size=11)
        self.multi_cell(0, 6, cap_text, align="C")
        self.ln(4)


# ------------------------------------------------------ Main build routine

def build_pdf(out_path: str = "icing_results.pdf") -> None:
    pdf = PDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()

    # ---------------- Results Section ----------------
    pdf.add_heading("Results", level=1)

    subsections = [
        ("Ice Shape Evolution", FIGURES[0]),
        ("Aerodynamic Performance Degradation", FIGURES[1]),
        ("Surface Temperature Distribution", FIGURES[2]),
        ("Collection Efficiency", FIGURES[3]),
    ]

    for title, fig in subsections:
        pdf.add_heading(title, level=2)
        pdf.add_figure(*fig)

    # Key formulas
    pdf.add_heading("Key Formulas", level=2)
    pdf.add_paragraph("β = ṁ_accreted / ṁ_incoming")
    pdf.add_paragraph("ṁ_w L_f + ṁ_w c_w (T_w − T_f) = h (T_∞ − T_s) + ṗ̇_q_r + k_i (∂T/∂n)|_{wall}")

    pdf.output(out_path)
    print(f"PDF written to: {out_path}")


if __name__ == "__main__":
    build_pdf()
