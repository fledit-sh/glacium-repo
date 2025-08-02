#!/usr/bin/env python3
"""kite_power_diagrams.py – Berechnet und plottet die wichtigsten Diagramme
(Abb. 2, 4 & 5) aus Loyd (1980) *Crosswind Kite Power*.

Das Skript benötigt nur die aerodynamischen Kenngrößen des Kites
(CL und CD). Daraus wird das Verhältnis L/D, die relevanten
Leistungs‑Faktoren sowie optionale absolute Leistungen (mit Wing‑Area
und Windgeschwindigkeit) ermittelt und visualisiert.

Aufrufbeispiel (interaktiv):
    python kite_power_diagrams.py --cl 1.0 --cd 0.05 \
        --wing-area 576 --winds 5 10 15

Die Plots werden als PNG-Dateien im aktuellen Verzeichnis abgelegt und
zusätzlich auf dem Bildschirm angezeigt.

Referenzgleichungen (Loyd 1980):
    Fs  – Eq.(10)
    Fc  – Eq.(15)
    Fc,max – Eq.(16)
    Fd  – Eq.(20)
    Fd,max – Eq.(21)

Autor: ChatGPT – 2025‑07‑29
Lizenz: MIT
"""
from __future__ import annotations
import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------------------------
#   Leistungsfaktoren nach Loyd (1980)
# --------------------------------------

def F_simple(L_over_D: float | np.ndarray, v_ratio: np.ndarray) -> np.ndarray:
    """Relative Leistung eines *simple kite* (Abb. 2)."""
    return v_ratio * np.sqrt(1 + 1 / L_over_D**2 - v_ratio**2)


def F_cross(L_over_D: float | np.ndarray, v_ratio: np.ndarray) -> np.ndarray:
    """Crosswind‑Lift‑Power (Abb. 4, linke Kurve)."""
    return L_over_D * v_ratio * (1 - v_ratio)


def F_drag(L_over_D: float | np.ndarray, dp_dk: np.ndarray) -> np.ndarray:
    """Drag‑Power (Abb. 4, rechte Kurve)."""
    return (L_over_D**2) * (dp_dk) / (1 + dp_dk) ** 3

# --------------------------------------
#   Hilfsfunktionen
# --------------------------------------

def wind_power_density(rho: float, v_w: float) -> float:
    """Windleistungsdichte p_w = ½ ρ V_w³."""
    return 0.5 * rho * v_w ** 3


def potential_drag_power(cl: float, cd: float, v_w: float, area: float, rho: float = 1.225) -> float:
    """Maximale Drag‑Power (Fd,max) nach Eq.(21)."""
    L_over_D = cl / cd
    Fd_max = 4 / 27 * L_over_D ** 2
    return wind_power_density(rho, v_w) * area * cl * Fd_max

# --------------------------------------
#   Plot‑Routinen
# --------------------------------------

def plot_simple_kite(L_values: list[float], outdir: Path):
    v = np.linspace(0.0, 1.0, 600)
    plt.figure()
    for L in L_values:
        plt.plot(v, F_simple(L, v), label=f"L/D={L}")
    plt.xlabel(r"$V_L / V_w$")
    plt.ylabel(r"$F_s$")
    plt.title("Simple‑Kite‑Power (Loyd 1980, Fig. 2)")
    plt.legend()
    out = outdir / "figure_2_simple_kite.png"
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.show()


def plot_cross_drag(L_value: float, outdir: Path):
    # Crosswind lift (vs V_L/V_w)
    v = np.linspace(0.0, 1.0, 600)
    plt.figure()
    plt.plot(v, F_cross(L_value, v))
    plt.xlabel(r"$V_L / V_w$")
    plt.ylabel(r"$F_c$")
    plt.title(f"Crosswind‑Lift‑Power (Loyd 1980, Fig. 4) – L/D={L_value}")
    plt.savefig(outdir / "figure_4a_cross_lift.png", dpi=300, bbox_inches="tight")
    plt.show()

    # Drag power (vs D_P/D_K)
    d = np.linspace(0.0, 2.0, 600)
    plt.figure()
    plt.plot(d, F_drag(L_value, d))
    plt.xlabel(r"$D_P / D_K$")
    plt.ylabel(r"$F_d$")
    plt.title(f"Drag‑Power (Loyd 1980, Fig. 4) – L/D={L_value}")
    plt.savefig(outdir / "figure_4b_drag_power.png", dpi=300, bbox_inches="tight")
    plt.show()


def plot_potential_power(cl: float, cd: float, speeds: list[float], area: float, rho: float, outdir: Path):
    L_over_D = cl / cd
    Ls = np.linspace(1.0, L_over_D * 2, 300)  # x‑Achse erweitert über aktuelles L/D hinaus
    plt.figure()
    for v in speeds:
        Pw = 0.5 * rho * v ** 3
        Fd_max = 4 / 27 * Ls ** 2
        power = Pw * area * cl * Fd_max / 1e6  # → MW
        plt.plot(Ls, power, label=f"V_w={v} m/s")
    plt.xlabel("L/D")
    plt.ylabel("P_ideal [MW]")
    plt.title("Potentielle Drag‑Power (Loyd 1980, Fig. 5)")
    plt.legend()
    plt.savefig(outdir / "figure_5_potential_power.png", dpi=300, bbox_inches="tight")
    plt.show()

# --------------------------------------
#   CLI
# --------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Plot Loyd(1980) power diagrams for a given CL & CD.")
    parser.add_argument("--cl", type=float, required=True, help="Auftriebsbeiwert CL des Kites")
    parser.add_argument("--cd", type=float, required=True, help="Widerstandsbeiwert CD des Kites")
    parser.add_argument("--wing-area", type=float, default=576.0, help="Flügelfläche A in m² (Standard: 576, C‑5A)")
    parser.add_argument("--winds", type=float, nargs="*", default=[5.0, 10.0, 15.0], help="Windgeschwindigkeiten V_w in m/s für Fig. 5")
    parser.add_argument("--rho", type=float, default=1.225, help="Luftdichte ρ in kg/m³")
    parser.add_argument("--out", type=str, default="plots", help="Ausgabe‑Verzeichnis für PNG‑Dateien")
    args = parser.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    L_over_D = args.cl / args.cd
    # 1) Abb. 2 – Simple Kite
    plot_simple_kite([5, 10, 20, 50], outdir)

    # 2) Abb. 4 – Crosswind Lift & Drag (L/D des Users)
    plot_cross_drag(L_over_D, outdir)

    # 3) Abb. 5 – Potentiale Leistung
    plot_potential_power(args.cl, args.cd, args.winds, args.wing_area, args.rho, outdir)

    # Kurze Zusammenfassung in der Konsole
    print("\n===== Zusammenfassung =====")
    for v in args.winds:
        p = potential_drag_power(args.cl, args.cd, v, args.wing_area, args.rho)
        print(f"V_w = {v:>4.1f} m/s → P_drag,max = {p/1e6:>6.2f} MW (CL={args.cl}, CD={args.cd}, L/D={L_over_D:.1f})")


if __name__ == "__main__":
    main()
