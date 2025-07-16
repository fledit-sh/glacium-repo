#!/usr/bin/env python3
# -------------------------------------------------------------------------
#  make_conv_report.py
#  Erstellt einen PDF-Report mit Mittelwert & Varianz der letzten n Iterationen.
# -------------------------------------------------------------------------
import argparse
import csv
from datetime import datetime
from pathlib import Path

import numpy as np
from fpdf import FPDF  # fpdf2 ≥ 2.x
from glacium.utils.logging import log
from glacium.utils.default_paths import dejavu_font_file

# -------------------------------------------------------------------------
# 1)  Statistikdatei einlesen
# -------------------------------------------------------------------------
def read_stats(path: Path) -> tuple[list[str], np.ndarray, np.ndarray]:
    labels: list[str] = []
    mean: list[float] = []
    var: list[float] = []

    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            labels.append(row["label"])
            mean.append(float(row["mean"]))
            var.append(float(row["variance"]))

    return labels, np.asarray(mean, dtype=float), np.asarray(var, dtype=float)

# -------------------------------------------------------------------------
# 4)  PDF-Report
# -------------------------------------------------------------------------
class ConvPDF(FPDF):
    def __init__(self, n: int) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.n = n
        self.set_auto_page_break(True, 15)
        self.add_font("DejaVu", "", str(dejavu_font_file()), uni=True)

    def header(self):
        self.set_font("DejaVu", "", 14)
        self.cell(
            0,
            10,
            f"Solver Convergence Report (Last {self.n} Iterations)",
            ln=True,
            align="C",
        )
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.cell(0, 8, f"Seite {self.page_no()}/{{nb}}", align="C")

    def add_table(self, labels: list[str], mean: np.ndarray, var: np.ndarray):
        self.set_font("DejaVu", "", 10)
        widths = (65, 50, 50)            # Label | Mean | Variance

        # Kopf
        self.set_fill_color(200, 200, 200)
        for w, txt in zip(widths, ("Spalte", "Mittelwert", "Varianz")):
            self.cell(w, 7, txt, border=1, align="C", fill=True)
        self.ln()

        # Daten
        self.set_fill_color(255, 255, 255)

        for lbl, m, v in zip(labels, mean, var):
            self.cell(widths[0], 6, lbl, border=1)
            self.cell(widths[1], 6, f"{m:.3e}", border=1, align="R")  # 4 sign. Stellen
            self.cell(widths[2], 6, f"{v:.3e}", border=1, align="R")  # 4 sign. Stellen
            self.ln()


# -------------------------------------------------------------------------
# 5)  Hauptfunktion
# -------------------------------------------------------------------------
def build_report(
    analysis_dir: Path,
    output_file: Path | None = None,
    n: int = 15,
) -> Path:
    """Create a PDF report from ``analysis_dir``.

    Parameters
    ----------
    analysis_dir:
        Directory created by :func:`glacium.utils.convergence.analysis_file`.
    output_file:
        Destination PDF file.
    n:
        Number of trailing iterations represented in ``stats.csv``.
    """

    if output_file is None:
        output_file = analysis_dir / "report.pdf"

    stats_file = analysis_dir / "stats.csv"
    labels, mean, var = read_stats(stats_file)

    pdf = ConvPDF(n)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 6, f"Analysis directory: {analysis_dir.name}", ln=True)
    pdf.cell(0, 6, f"Generated        : {datetime.now():%Y-%m-%d %H:%M:%S}", ln=True)
    pdf.ln(4)

    pdf.add_table(labels, mean, var)

    for name in ("cl_cd.png", "cl.png", "cd.png"):
        fig = analysis_dir / "figures" / name
        if fig.exists():
            pdf.ln(4)
            pdf.image(str(fig), w=160)

    pdf.output(str(output_file))
    log.success(f"Report geschrieben → {output_file}")

    return output_file

# -------------------------------------------------------------------------
# 6)  CLI-Wrapper
# -------------------------------------------------------------------------
def cli():
    ap = argparse.ArgumentParser(
        description="Erzeugt einen PDF-Report mit Mittelwert & Varianz der letzten Solver-Iterationen."
    )
    ap.add_argument("input", type=Path, help="Analyse-Verzeichnis")
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default="conv_report.pdf",
        help="Name des erzeugten PDFs",
    )
    ap.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=15,
        help="Anzahl betrachteter Iterationen",
    )
    args = ap.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(args.input)
    build_report(args.input, args.output, args.iterations)

if __name__ == "__main__":
    cli()
