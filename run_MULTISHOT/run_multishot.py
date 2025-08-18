#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch-Verarbeitung mehrerer Shot-Datensätze.

Erwartet pro Shot (rekursiv gesucht) genau diese drei Dateien:
  - soln.fensap.<ID>.dat
  - droplet.drop.<ID>.dat
  - swimsol.ice.<ID>.dat
wobei <ID> eine 6-stellige Kennung ist (000001, 000002, ...).

Für jeden gefundenen Shot wird folgendes ausgeführt (alles direkt unter <output>/<ID>/):
  1) 00_merge.py (base + augments)  -> merged.dat
  2) 01_auto_cp_normals.py          -> merged_normals.png
  3) 01_plot.py                     -> plots/
  4) 02_correlate.py                -> correlation_analysis/
"""

from __future__ import annotations

import argparse
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

# Verzeichnis mit den Hilfsskripten (00_merge.py, 01_auto_cp_normals.py, 01_plot.py, 02_correlate.py)
SCRIPT_DIR = Path(__file__).parent.resolve()

# Exakte Dateimuster für die drei Dateien pro Shot (case-insensitive)
PATTERNS = {
    "base": re.compile(r"^soln\.fensap\.(\d{6})\.dat$", re.I),
    "drop": re.compile(r"^droplet\.drop\.(\d{6})\.dat$", re.I),
    "ice":  re.compile(r"^swimsol\.ice\.(\d{6})\.dat$", re.I),
}

def run_cmd(cmd: List[str], cwd: Path | None = None) -> None:
    logging.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=cwd)

def find_shots(input_dir: Path) -> Dict[str, List[Path]]:
    """
    Suche rekursiv nach exakt diesen drei Dateien pro ID:
      soln.fensap.<ID>.dat, droplet.drop.<ID>.dat, swimsol.ice.<ID>.dat
    und gib sie in fester Reihenfolge zurück: [base, drop, ice].
    """
    grouped: Dict[str, Dict[str, Path]] = {}

    for p in input_dir.rglob("*.dat"):
        name = p.name
        for key, rx in PATTERNS.items():
            m = rx.match(name)
            if m:
                sid = m.group(1)
                grouped.setdefault(sid, {})
                # erste gefundene Datei pro Rolle behalten
                grouped[sid].setdefault(key, p)

    shots: Dict[str, List[Path]] = {}
    for sid, parts in grouped.items():
        if all(k in parts for k in ("base", "drop", "ice")):
            shots[sid] = [parts["base"], parts["drop"], parts["ice"]]
    return shots

def process_shot(shot_id: str, files: List[Path], out_root: Path) -> None:
    """
    Verarbeite einen Shot mit Dateien [base, drop, ice].
    Schreibt direkt nach <out_root>/<shot_id>/...
    """
    logging.info("Processing shot %s", shot_id)
    # wenn out_root bereits die Shot-ID ist, nicht noch einmal anhängen
    shot_dir = out_root if out_root.name == shot_id else (out_root / shot_id)
    shot_dir.mkdir(parents=True, exist_ok=True)

    base, drop, ice = files

    # 1) Merge -> <shot_dir>/merged.dat
    merged = shot_dir / "merged.dat"
    merge_cmd = [
        sys.executable,
        str(SCRIPT_DIR / "00_merge.py"),
        str(base),
        "--out", str(merged),
        "--augment", str(drop),
        "--augment", str(ice),
    ]
    run_cmd(merge_cmd, cwd=shot_dir)

    # 2) Cp-Normalen -> <shot_dir>/merged_normals.png
    normals_png = shot_dir / "merged_normals.png"
    run_cmd(
        [
            sys.executable,
            str(SCRIPT_DIR / "01_auto_cp_normals.py"),
            "--solution", str(base),
            "--merged-in", str(merged),
            "--png-out", str(normals_png),
        ],
        cwd=shot_dir,
    )

    # 3) Plots -> <shot_dir>/plots
    plots_dir = shot_dir / "plots"
    run_cmd(
        [
            sys.executable,
            str(SCRIPT_DIR / "01_plot.py"),
            str(merged),
            "--outdir", str(plots_dir),
        ],
        cwd=shot_dir,
    )

    # 3b) s-plots -> <shot_dir>/plots/curve_s.pdf
    plots_dir = shot_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    s_pdf = plots_dir / "curve_s.pdf"
    run_cmd(
        [
            sys.executable,
            str(SCRIPT_DIR / "03_plot_s.py"),
            str(merged),
            str(s_pdf),
        ],
        cwd=shot_dir,
    )

    # 4) Korrelationen -> <shot_dir>/correlation_analysis
    corr_dir = shot_dir / "correlation_analysis"
    run_cmd(
        [
            sys.executable,
            str(SCRIPT_DIR / "02_correlate.py"),
            str(merged),
            "--outdir", str(corr_dir),
        ],
        cwd=shot_dir,
    )

    logging.info("Done. Results in: %s", shot_dir)

def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Batch-run der Analyseskripte über mehrere Shots. "
            "Standard: scannt rekursiv das aktuelle Verzeichnis und schreibt nach ./results."
        )
    )
    ap.add_argument(
        "--input-dir",
        type=Path,
        default=Path.cwd(),
        help="Verzeichnis, das rekursiv nach Shots durchsucht wird (Default: CWD)",
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),  # vorher: Path("results")
        help="Wurzelverzeichnis für die Ausgaben pro Shot (Default: CWD)",
    )
    ap.add_argument("--start-shot", type=int, default=None, help="nur IDs >= start-shot verarbeiten")
    ap.add_argument("--end-shot", type=int, default=None, help="nur IDs <= end-shot verarbeiten")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    shots = find_shots(args.input_dir)
    if not shots:
        logging.warning(
            "Keine Shots gefunden in %s. Erwartet werden Dateien (rekursiv) wie "
            "soln.fensap.<ID>.dat, droplet.drop.<ID>.dat, swimsol.ice.<ID>.dat.",
            args.input_dir,
        )
        return

    logging.info("Gefundene Shots: %d", len(shots))

    for sid in sorted(shots):
        val = int(sid)
        if args.start_shot is not None and val < args.start_shot:
            continue
        if args.end_shot is not None and val > args.end_shot:
            continue
        files = shots[sid]  # exakt [base, drop, ice]
        try:
            process_shot(sid, files, args.output_dir)
        except subprocess.CalledProcessError as cpe:
            logging.error("Shot %s failed (returncode %s): %s", sid, cpe.returncode, cpe.cmd)
        except Exception as exc:
            logging.error("Shot %s failed: %s", sid, exc)

if __name__ == "__main__":
    main()
