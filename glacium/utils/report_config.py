#!/usr/bin/env python3
# -------------------------------------------------------------------------
#  generate_ice_report.py
#  Erstellt einen PDF-Report aus einer FENSAP-ICE-Konfigurationsdatei.
#
#  Aufruf:
#      python generate_ice_report.py ice.par  [-o ice_report.pdf]
# -------------------------------------------------------------------------
import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from fpdf import FPDF            # fpdf2 ≥ 2.x  (pip install fpdf2)
from glacium.utils.default_paths import dejavu_font_file

# -------------------------------------------------------------------------
# 1) Konfiguration: Filter + optionale Beschreibungen/Einheiten
# -------------------------------------------------------------------------
IGNORE_KEYS = {
    "ICE_GUI_BC_COLORS_B", "ICE_GUI_BC_COLORS_G", "ICE_GUI_BC_COLORS_R",
    "ICE_GUI_GRID_OUTPUT_FLAG", "ICE_GUI_CONDITIONS_COPIED",
    "ICE_GUI_USE_FORCE_FILE", "ICE_GUI_USE_RESTART_FILE",
    "ICE_GUI_WALL_OMX_DETECTED", "ICE_GUI_WALL_OMY_DETECTED",
    "ICE_GUI_WALL_OMZ_DETECTED", "ICE_GUI_WALL_ROTATION_TYPE",
    "ICE_WALL_OMX", "ICE_WALL_OMY", "ICE_WALL_OMZ",
    "ICE_GRID_FILE_WALL_ZONES", "ICE_NB_FAMILY", "ICE_TOT_BOUNDARY_CONDITIONS",
    "ICE_FILE_GRID_TIMESTAMP", "ICE_INPUT_FILE_VERSION"
}

DESCRIPTION_MAP: Dict[str, Tuple[str, str]] = {
    #   Schlüssel                    (Beschreibung, Einheit)
    "ICE_RECOVERY_FACTOR":       ("Adiabatic Recovery Factor", "–"),
    "ICE_REF_AIR_PRESSURE":      ("Bezugs-Luftdruck",          "kPa"),
    "ICE_REF_TEMPERATURE":       ("Bezugs-Temperatur",         "°C"),
    "ICE_REF_VELOCITY":          ("Bezugs-Geschwindigkeit",    "m s⁻¹"),
    "ICE_TEMPERATURE":           ("Eis-Temperatur",            "°C"),
    "ICE_MACH_NUMBER":           ("Freiström-Machzahl",        "–"),
    "ICE_REYNOLDS_NUMBER":       ("Reynolds-Zahl",             "–"),
    "ICE_LIQ_H2O_CONTENT":       ("Liquid Water Content",      "kg m⁻³"),
    "ICE_DROP_DIAM":             ("Median Drop Diameter",      "µm"),
    "ICE_LAT_HEAT_FUSION":       ("Schmelzenthalpie",          "J kg⁻¹"),
    "ICE_GUI_TOTAL_TIME":        ("Gesamte Akkretionszeit",    "s"),
    "ICE_NUMBER_TIME_STEP":      ("Anzahl Zeitschritte",       "–"),
    "ICE_TIME_STEP":             ("Zeitschrittweite",          "s"),
}

# -------------------------------------------------------------------------
# 2)  Parser
# -------------------------------------------------------------------------
CAT_RE   = re.compile(r"^#\s*Category:\s*(.+)$")
PARAM_RE = re.compile(r"^([A-Z0-9_]+)\s+(.+)$")

def parse_cfg(path: Path) -> Dict[str, List[Tuple[str, str]]]:
    data: Dict[str, List[Tuple[str, str]]] = {}
    current = "Uncategorized"

    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            if m := CAT_RE.match(line):
                current = m.group(1)
                data.setdefault(current, [])
                continue
            if m := PARAM_RE.match(line):
                key, val = m.groups()
                if key not in IGNORE_KEYS:
                    data.setdefault(current, []).append((key, val))
    return data

# -------------------------------------------------------------------------
# 3)  PDF-Klasse
# -------------------------------------------------------------------------
class IcePDF(FPDF):
    def __init__(self):
        super().__init__(format="A4")
        self.set_auto_page_break(True, margin=15)
        # eingebettete Unicode-Schrift
        self.add_font("DejaVu", "", str(dejavu_font_file()), uni=True)

    # Kopf- und Fußzeile
    def header(self):
        self.set_font("DejaVu", "", 14)
        self.cell(0, 10, "ICE Simulation Configuration Report", ln=True, align="C")
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.cell(0, 8, f"Seite {self.page_no()}/{{nb}}", align="C")

    # Kapitel-Tabelle
    def add_category(self, name: str, items: List[Tuple[str, str]]):
        if not items:
            return
        self.set_fill_color(200, 200, 200)
        self.set_font("DejaVu", "", 12)
        self.cell(0, 8, name, ln=True, fill=True)
        self.ln(1)

        # Tabellenkopf
        widths = (55, 60, 23, 50)   # Key | Value | Unit | Description
        self.set_font("DejaVu", "", 10)
        self.set_fill_color(230, 230, 230)
        headers = ("Parameter", "Wert", "Einheit", "Beschreibung")
        for w, text in zip(widths, headers):
            self.cell(w, 6, text, border=1, align="C", fill=True)
        self.ln()

        # Zeilen
        self.set_fill_color(255, 255, 255)
        for key, val in items:
            descr, unit = DESCRIPTION_MAP.get(key, ("", ""))
            self.cell(widths[0], 6, key,  border=1)
            self.cell(widths[1], 6, val,  border=1)
            self.cell(widths[2], 6, unit, border=1, align="C")
            self.cell(widths[3], 6, descr, border=1)
            self.ln()
        self.ln(4)

# -------------------------------------------------------------------------
# 4)  PDF-Erstellung
# -------------------------------------------------------------------------
def build_pdf(input_file: Path, output_file: Path):
    cfg = parse_cfg(input_file)

    pdf = IcePDF()
    pdf.set_title("ICE Simulation Configuration Report")
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 6, f"Input-Datei : {input_file.name}", ln=True)
    pdf.cell(0, 6, f"Generiert   : {datetime.now():%Y-%m-%d %H:%M:%S}", ln=True)
    pdf.ln(6)

    for cat in sorted(cfg):
        pdf.add_category(cat, cfg[cat])

    pdf.output(str(output_file))
    print(f"PDF gespeichert: {output_file}")

# -------------------------------------------------------------------------
# 5)  CLI
# -------------------------------------------------------------------------
def cli():
    ap = argparse.ArgumentParser(description="Erzeugt einen PDF-Report aus einer FENSAP-ICE-Konfigurationsdatei.")
    ap.add_argument("input",  type=Path, help="Pfad zur Konfigdatei (*.par / *.txt)")
    ap.add_argument("-o", "--output", type=Path, default="ice_report.pdf",
                    help="Ausgabedatei (PDF; Standard: ice_report.pdf)")
    args = ap.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(args.input)
    build_pdf(args.input, args.output)

if __name__ == "__main__":
    cli()
