#!/usr/bin/env python3
# -*- coding: utf‑8 -*-
"""
tecplot_freezing_fraction.py – erweiterte Version mit Histogramm
"""
from pathlib import Path
import re
import sys
import matplotlib.pyplot as plt
import pandas as pd


def fix_exponent(token: str) -> str:
    token = token.replace("D", "E").replace("d", "E")
    if re.fullmatch(r"[+-]?\d*\.?\d+[+-]\d+", token):
        token = re.sub(r"([+-]?\d*\.?\d+)([+-]\d+)", r"\1E\2", token)
    return token


def read_first_zone(path: Path) -> pd.DataFrame:
    with path.open("r", encoding="utf‑8", errors="ignore") as f:
        lines = f.readlines()

    var_line = next(l for l in lines if l.strip().upper().startswith("VARIABLES"))
    var_names = re.findall(r'"([^"]+)"', var_line)

    data_start = None
    for idx, l in enumerate(lines):
        if l.strip().upper().startswith("ZONE"):
            data_start = idx + 1
            break
    if data_start is None:
        raise RuntimeError("Keine ZONE‑Zeile gefunden.")

    data_rows = []
    for l in lines[data_start:]:
        if re.match(r"\s*[A-Za-z]", l):
            break
        if not l.strip():
            continue
        tokens = [fix_exponent(t) for t in l.split()]
        try:
            data_rows.append([float(t) for t in tokens])
        except ValueError:
            continue

    return pd.DataFrame(data_rows, columns=var_names[: len(data_rows[0])])


def plot_freezing_fraction(df: pd.DataFrame) -> None:
    x, y = df["X"], df["Y"]
    ff = df["Freezing fraction"]

    # Scatter-Plot
    plt.figure(figsize=(7, 6))
    sc = plt.scatter(x, y, c=ff, s=8, cmap="viridis", edgecolors="none")
    plt.colorbar(sc, label="Freezing fraction")
    plt.xlabel("X [m]")
    plt.ylabel("Y [m]")
    plt.title("Freezing fraction distribution")
    plt.axis("equal")
    plt.tight_layout()

    # Histogram
    plt.figure(figsize=(7, 4))
    plt.hist(ff, bins=40, color="steelblue", edgecolor="black")
    plt.xlabel("Freezing fraction")
    plt.ylabel("Häufigkeit")
    plt.title("Histogramm der Freezing fraction")
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
