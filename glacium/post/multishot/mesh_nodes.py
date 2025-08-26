#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erzeuge eine Übersichtsgrafik der Knotenzahl pro Shot auf Basis von grid.ice.<ID>-Dateien.

Nutzung (Beispiele):
  python 04_mesh.py --src . --out mesh_nodes_per_shot.png
  python 04_mesh.py --src /path/to/case --csv mesh_nodes_per_shot.csv --out mesh_nodes_per_shot.png
  python 04_mesh.py --src . --exe convertgrid.exe

Hinweise:
- Es wird rekursiv nach Dateien "grid.ice.<ID>" gesucht, wobei <ID> aus genau 6 Ziffern besteht.
- Die Knotenzahl wird via `convertgrid.exe -d <file>` ausgelesen (Pfad anpassbar mit --exe oder der Umgebungsvariable CONVERTGRID_EXE).
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt


GRID_RX = re.compile(r"^grid\.ice\.(\d{6})$")
NODE_RX = re.compile(r"Number of nodes\s*[:=]\s*(\d+)", re.IGNORECASE)


def get_node_count(
    grid_file: Path, exe: str = os.environ.get("CONVERTGRID_EXE", "convertgrid.exe")
) -> int | None:
    """Rufe `convertgrid.exe -d <grid_file>` auf und parse die Knotenzahl."""
    try:
        result = subprocess.run([exe, "-d", str(grid_file)], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        print(f"[ERROR] Executable not found: {exe}")
        return None

    output = (result.stdout or "") + "\n" + (result.stderr or "")
    for line in output.splitlines():
        if m := NODE_RX.search(line):
            try:
                return int(m.group(1))
            except ValueError:
                pass
    print(f"[WARN] Keine Knotenzahl gefunden in {grid_file}")
    return None


def collect_nodes(src: Path, exe: str) -> Tuple[List[int], List[int]]:
    """
    Suche rekursiv nach grid.ice.<ID> und sammle (ID, nodes).
    Rückgabe: (shot_ids (int), node_counts (int)), jeweils sortiert nach ID.
    """
    found = {}
    for p in src.rglob("grid.ice.*"):
        name = p.name
        m = GRID_RX.match(name)
        if not m:
            continue
        sid = int(m.group(1))
        if sid in found:
            # Duplikate vermeiden – nimm die erste gefundene Datei
            continue
        n = get_node_count(p, exe=exe)
        if n is not None:
            found[sid] = n

    shots = sorted(found.keys())
    nodes = [found[s] for s in shots]
    return shots, nodes


def plot_and_save(shots: List[int], nodes: List[int], out_png: Path) -> None:
    """Erzeuge eine PNG-Grafik der Knotenzahl pro Shot."""
    if not shots:
        print("[ERROR] Keine gültigen Daten zum Plotten.")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(shots, nodes, marker="o")
    plt.xlabel("Shot-Nummer")
    plt.ylabel("Anzahl Knoten")
    plt.title("Knotenzahl pro Shot")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    print(f"[INFO] Plot gespeichert: {out_png}")


def save_csv(shots: List[int], nodes: List[int], out_csv: Path) -> None:
    """Speichere (shot, nodes) als CSV."""
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["shot_id", "node_count"])
        for s, n in zip(shots, nodes):
            w.writerow([s, n])
    print(f"[INFO] CSV gespeichert: {out_csv}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Übersicht der Knotenzahl pro Shot aus grid.ice.<ID>-Dateien.")
    ap.add_argument("--src", type=Path, default=Path.cwd(), help="Wurzelverzeichnis (rekursiv) für die Suche (Default: CWD)")
    ap.add_argument("--out", type=Path, default=Path("mesh_nodes_per_shot.png"), help="Pfad zur Ausgabegrafik (PNG)")
    ap.add_argument("--csv", type=Path, default=None, help="Optionaler Pfad für CSV-Ausgabe")
    ap.add_argument(
        "--exe",
        type=str,
        default=os.environ.get("CONVERTGRID_EXE", "convertgrid.exe"),
        help=(
            "Pfad/Name des convertgrid-Tools (Default: $CONVERTGRID_EXE oder 'convertgrid.exe')"
        ),
    )
    args = ap.parse_args()

    shots, nodes = collect_nodes(args.src, args.exe)
    if not shots:
        print("[ERROR] Keine grid.ice.<ID>-Dateien mit Knotenzahl gefunden.")
        return

    if args.csv:
        save_csv(shots, nodes, args.csv)

    plot_and_save(shots, nodes, args.out)


if __name__ == "__main__":
    main()
