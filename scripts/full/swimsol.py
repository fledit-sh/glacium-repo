#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_vs_y_lines.py – Lineplots jeder Variable vs. Y aus Tecplot ASCII-Dateien
"""

import sys
import re
import glob
from pathlib import Path
import scienceplots

import matplotlib
matplotlib.rcParams["text.usetex"] = False  # Deaktiviere LaTeX vollständig
import matplotlib.pyplot as plt
import pandas as pd
plt.style.use(["science","ieee"])

def fix_exponent(token: str) -> str:
    token = token.replace("D", "E").replace("d", "E")
    if re.fullmatch(r"[+-]?\d*\.?\d+[+-]\d+", token):
        token = re.sub(r"([+-]?\d*\.?\d+)([+-]\d+)", r"\1E\2", token)
    return token


def read_first_zone(path: Path) -> pd.DataFrame:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    var_line = next(l for l in lines if l.strip().upper().startswith("VARIABLES"))
    var_names = [v.strip() for v in re.findall(r'"([^"]+)"', var_line)]

    data_start = next(i for i, l in enumerate(lines) if l.strip().upper().startswith("ZONE")) + 1
    rows = []
    for l in lines[data_start:]:
        if re.match(r"\s*[A-Za-z]", l):
            break
        if not l.strip():
            continue
        toks = [fix_exponent(t) for t in l.split()]
        try:
            rows.append([float(t) for t in toks])
        except ValueError:
            continue

    df = pd.DataFrame(rows, columns=var_names[:len(rows[0])])
    df.columns = df.columns.str.strip()  # Leerzeichen aus Spaltennamen
    return df


def safe_label(text: str) -> str:
    """Entfernt Unicode/LaTeX‑problematische Zeichen."""
    return (
        text.replace("\u202f", " ")
            .replace("\xa0", " ")
            .replace("^", "ˆ")
            .replace("$", "")
            .strip()
    )


def make_lineplots(df: pd.DataFrame, out_dir: Path, stem: str) -> None:
    # Sortiere nach Y, damit die Linien korrekt verlaufen
    sorted_df = df.sort_values("Y")
    y = sorted_df["Y"]

    for col in sorted_df.columns:
        if col == "Y":
            continue

        fig = plt.figure(figsize=(8, 5))
        plt.plot(y, sorted_df[col], lw=1.2)
        plt.xlabel("Y [m]")
        plt.ylabel(safe_label(col))
        plt.title(f"{safe_label(col)} vs Y")
        plt.grid(True)
        plt.tight_layout()

        safe = re.sub(r"[^\w\-.]", "_", col.strip())
        fig.savefig(out_dir / f"{stem}_{safe}.png", dpi=300)
        plt.close(fig)



def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_vs_y_lines.py <file_or_pattern> [...]")
        sys.exit(1)

    out_dir = Path("plots")
    out_dir.mkdir(exist_ok=True)

    for pattern in sys.argv[1:]:
        for file in sorted(glob.glob(pattern)):
            path = Path(file)
            df = read_first_zone(path)
            make_lineplots(df, out_dir, path.stem)
            print(f"✅ {path.name} → {len(df.columns)-1} Lineplots gespeichert in /plots/")


if __name__ == "__main__":
    main()
