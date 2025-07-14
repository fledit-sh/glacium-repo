#!/usr/bin/env python3
# -------------------------------------------------------------------------
#  make_conv_report.py
#  Erstellt einen PDF-Report mit Mittelwert & Varianz der letzten 5 Iterationen.
# -------------------------------------------------------------------------
import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import List

import numpy as np
from fpdf2 import FPDF            # fpdf2 ≥ 2.x

# -------------------------------------------------------------------------
# 1)  HEADER-PARSE-REGEX
# -------------------------------------------------------------------------
HEADER_RE = re.compile(r"#\s*\d+\s+(.+?)\s*$")   # extrahiert Spaltenlabel

# -------------------------------------------------------------------------
# 2)  Datei einlesen
# -------------------------------------------------------------------------
def read_file(path: Path):
    labels: List[str] = []
    rows: List[List[float]] = []

    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip()
            if line.startswith("#"):
                m = HEADER_RE.match(line)
                if m:
                    labels.append(m.group(1))
                continue
            if not line.strip():
                continue
            numbers = [float(tok.replace("E", "e")) for tok in line.split()]
            rows.append(numbers)

    # Sicherheits-Assert: Label-Anzahl kann 1–2 kleiner sein, wenn Flags=0
    if len(labels) < len(rows[0]):
        # Dummy-Labels für fehlende Spalten ergänzen
        for i in range(len(rows[0]) - len(labels)):
            labels.insert(i + 1, f"col_{i+1}")

    return labels, np.asarray(rows, dtype=float)

# -------------------------------------------------------------------------
# 3)  Statistik der letzten 5 Zeilen
# -------------------------------------------------------------------------
def last5_stats(matrix: np.ndarray):
    last5 = matrix[-5:, :]
    mean  = last5.mean(axis=0)
    var   = last5.var(axis=0, ddof=0)   # Pop-Varianz
    return mean, var

# -------------------------------------------------------------------------
# 4)  PDF-Report
# -------------------------------------------------------------------------
class ConvPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(True, 15)
        self.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)

    def header(self):
        self.set_font("DejaVu", "", 14)
        self.cell(0, 10, "Solver Convergence Report (Last 5 Iterations)", ln=True, align="C")
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.cell(0, 8, f"Seite {self.page_no()}/{{nb}}", align="C")

    def add_table(self, labels: List[str], mean: np.ndarray, var: np.ndarray):
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
def build_report(input_file: Path, output_file: Path):
    labels, data = read_file(input_file)
    mean, var    = last5_stats(data)

    pdf = ConvPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 6, f"Eingabedatei : {input_file.name}", ln=True)
    pdf.cell(0, 6, f"Generiert   : {datetime.now():%Y-%m-%d %H:%M:%S}", ln=True)
    pdf.ln(4)

    pdf.add_table(labels, mean, var)
    pdf.output(str(output_file))
    print(f"Report geschrieben → {output_file}")

# -------------------------------------------------------------------------
# 6)  CLI-Wrapper
# -------------------------------------------------------------------------
def cli():
    ap = argparse.ArgumentParser(description="Erzeugt einen PDF-Report mit Mittelwert & Varianz der letzten 5 Solver-Iterationen.")
    ap.add_argument("input",  type=Path, help="Solver-Ausgabedatei")
    ap.add_argument("-o", "--output", type=Path, default="conv_report.pdf",
                    help="Name des erzeugten PDFs")
    args = ap.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(args.input)
    build_report(args.input, args.output)

if __name__ == "__main__":
    cli()
