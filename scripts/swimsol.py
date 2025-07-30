#!/usr/bin/env python3
# -*- coding: utf‑8 -*-
"""
tecplot_freezing_fraction.py

Usage:
    python tecplot_freezing_fraction.py path/to/file.dat

Created for Noel – 30 Jul 2025
"""
from pathlib import Path
import re
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def fix_exponent(token: str) -> str:
    """
    Bringt Exponenten in die Form 1.23E+03.
    Beispiele:
        '0.6419779458645019+151'  -> '0.6419779458645019E+151'
        '0.1301311461814025-149'  -> '0.1301311461814025E-149'
        '5.4D-02'                 -> '5.4E-02'
    """
    # D‑Notation
    token = token.replace("D", "E").replace("d", "E")

    # Fehlendes 'E'
    if re.fullmatch(r"[+-]?\d*\.?\d+[+-]\d+", token):
        token = re.sub(r"([+-]?\d*\.?\d+)([+-]\d+)", r"\1E\2", token)
    return token


def read_first_zone(path: Path) -> pd.DataFrame:
    """
    Liest nur den ersten FEQUADRILATERAL‑Datenblock.
    """
    with path.open("r", encoding="utf‑8", errors="ignore") as f:
        lines = f.readlines()

    # 1) Variable‑Namen ermitteln
    var_line = next(l for l in lines if l.strip().upper().startswith("VARIABLES"))
    # Variablennamen liegen in "..." – einschließlich Kommas innerhalb der Anführungszeichen splitten
    var_names = re.findall(r'"([^"]+)"', var_line)

    # 2) Datenzeilen sammeln: alles zwischen der ersten ZONE‑Zeile
    #    und der darauffolgenden Zeile, die wieder mit Buchstaben beginnt
    data_start = None
    for idx, l in enumerate(lines):
        if l.strip().upper().startswith("ZONE"):
            data_start = idx + 1
            break
    if data_start is None:
        raise RuntimeError("Keine ZONE‑Zeile gefunden.")

    data_rows = []
    for l in lines[data_start:]:
        # Abbruch, sobald wieder eine nichtnumerische Zeile kommt
        if re.match(r"\s*[A-Za-z]", l):  # beginnt mit Buchstabe
            break
        if not l.strip():
            continue
        # Tokenisieren, Exponenten fixen, floats konvertieren
        tokens = [fix_exponent(t) for t in l.split()]
        try:
            data_rows.append([float(t) for t in tokens])
        except ValueError:
            # Wenn eine Zeile nicht korrekt ist, ignorieren
            continue

    df = pd.DataFrame(data_rows, columns=var_names[: len(data_rows[0])])
    return df


def plot_freezing_fraction(df: pd.DataFrame) -> None:
    """
    Streudiagramm X‑Y, Farbe = Freezing fraction.
    """
    x, y = df["X"], df["Y"]
    ff = df["Freezing fraction"]

    plt.figure(figsize=(7, 6))
    sc = plt.scatter(x, y, c=ff, s=8, cmap="viridis", edgecolors="none")
    cbar = plt.colorbar(sc, label="Freezing fraction")
    plt.xlabel("X [m]")
    plt.ylabel("Y [m]")
    plt.title("Freezing fraction distribution")
    plt.axis("equal")
    plt.tight_layout()
    plt.show()


def main():
    if len(sys.argv) != 2:
        print("Usage: python tecplot_freezing_fraction.py <file_path>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    df = read_first_zone(file_path)
    print(f"Geladene Zeilen: {len(df)}  |  Spalten: {list(df.columns)}")

    plot_freezing_fraction(df)


if __name__ == "__main__":
    main()
