#!/usr/bin/env python3
"""
plot_ice_contours.py
====================

Liest sequenziell nummerierte STL‑Dateien einer 2.5D‑Vereisungssimulation ein,
plottet die äußere Eis‑Kontur und bietet jetzt zusätzlich:

* **Speichern der einzelnen Konturen** als CSV (x, y) pro Schritt
* **Speichern des Overlay‑Plots** als PNG (und optional PDF)
* **Animation des Wachstums** (cumulative overlay) mit frei wählbarer Framerate
  und Ausgabe als MP4 oder GIF, abhängig von verfügbarem Writer (ffmpeg oder
  pillow).

Dependencies
------------
    pip install trimesh[all] matplotlib numpy
    # Für MP4: ffmpeg installieren (oder "pip install pillow" für GIF)

Usage Example
-------------
    python plot_ice_contours.py \
        --pattern "ice.ice.*.stl" \
        --save-curves \
        --save-overlay \
        --animation ice_growth.mp4 --fps 10 \
        --outdir results
"""

from __future__ import annotations

import argparse
import glob
import os
import pathlib
import re
from typing import List
import ffmpeg
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
import trimesh

# -----------------------------------------------------------------------------
# Hilfsfunktionen
# -----------------------------------------------------------------------------

def sorted_files(pattern: str) -> List[str]:
    """Sortiere STL‑Dateien numerisch anhand der Endung *NNNNNN.stl*."""

    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError("Keine STL‑Dateien gefunden – Pfad/Muster prüfen.")

    def key(name: str) -> int:
        m = re.search(r"([0-9]+)\.stl$", name)
        return int(m.group(1)) if m else -1

    return sorted(files, key=key)


def boundary_edges_xy(mesh: trimesh.Trimesh) -> np.ndarray:
    """Gibt 2D‑Randkanten *[N, 2, 2]* (x‑y) zurück (robust für verschiedene APIs)."""

    if hasattr(mesh, "edges_unique_counts"):
        edges = mesh.edges_unique[mesh.edges_unique_counts == 1]
    elif hasattr(mesh, "edges_unique_faces"):
        faces = mesh.edges_unique_faces
        edges = mesh.edges_unique[faces[:, 1] == -1]
    else:
        inv = mesh.edges_unique_inverse
        counts = np.bincount(inv, minlength=len(mesh.edges_unique))
        edges = mesh.edges_unique[counts == 1]

    return mesh.vertices[edges][:, :, :2]  # nur (x, y)


def plot_segments(ax: plt.Axes, segments: np.ndarray, **kwargs) -> None:
    """Zeichnet Liniensegmente (N, 2, 2) in eine Achse."""

    for seg in segments:
        ax.plot(seg[:, 0], seg[:, 1], **kwargs)

# -----------------------------------------------------------------------------
# Hauptprogramm
# -----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Plot & export ice contour STL files (2.5D)")
    parser.add_argument("--pattern", default="ice.ice.*.stl", help="Glob pattern der STL‑Dateien")
    parser.add_argument("--no-overlay", dest="overlay", action="store_false", help="Alle Konturen separat plotten statt Overlay")
    parser.set_defaults(overlay=True)

    # Export‑Optionen
    parser.add_argument("--save-curves", action="store_true", help="Konturen als CSV speichern")
    parser.add_argument("--save-overlay", action="store_true", help="Overlay‑Plot als PNG speichern")
    parser.add_argument("--animation", metavar="FILE", help="Dateiname für Animation (z.B. ice_growth.mp4 oder .gif)")
    parser.add_argument("--fps", type=int, default=10, help="Framerate für Animation (default: 10 fps)")
    parser.add_argument("--outdir", default="output", help="Zielordner für alle Export‑Dateien")

    # Styling
    parser.add_argument("--alpha", type=float, default=0.9, help="Linien‑Transparenz")
    parser.add_argument("--linewidth", type=float, default=1.2, help="Linienbreite")
    parser.add_argument("--dpi", type=int, default=150, help="DPI für gespeicherte Grafiken")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    files = sorted_files(args.pattern)
    cmap = plt.get_cmap("viridis", len(files))

    # Daten sammeln
    segments_list: list[np.ndarray] = []

    if args.overlay:
        fig_overlay, ax_overlay = plt.subplots(dpi=args.dpi)

    for idx, fname in enumerate(files, start=1):
        mesh = trimesh.load_mesh(fname, process=False)
        segments = boundary_edges_xy(mesh)
        segments_list.append(segments)

        color = cmap(idx - 1) if args.overlay else "k"
        title = f"Ice Contour {idx} – {pathlib.Path(fname).name}"

        # Overlay oder Einzelplot
        if args.overlay:
            plot_segments(ax_overlay, segments, color=color, alpha=args.alpha, linewidth=args.linewidth)
        else:
            fig, ax = plt.subplots(dpi=args.dpi)
            plot_segments(ax, segments, color=color, alpha=args.alpha, linewidth=args.linewidth)
            ax.set_aspect("equal")
            ax.set_title(title)
            ax.set_xlabel("x [m]")
            ax.set_ylabel("y [m]")
            plt.show()

        # Export einzelner Kontur als CSV
        if args.save_curves:
            fname_csv = os.path.join(args.outdir, f"contour_{idx:06d}.csv")
            np.savetxt(fname_csv, segments.reshape(-1, 2), delimiter=",", header="x,y", comments="")

    # ------------------------------------------------------------------
    # Overlay‑Plot abschließen & speichern
    # ------------------------------------------------------------------

    if args.overlay:
        ax_overlay.set_aspect("equal")
        ax_overlay.set_xlabel("x [m]")
        ax_overlay.set_ylabel("y [m]")
        ax_overlay.set_title("Ice Contours Overlay")
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=1, vmax=len(files)))
        plt.colorbar(sm, ax=ax_overlay, label="Frame")

        if args.save_overlay:
            p_png = os.path.join(args.outdir, "overlay.png")
            fig_overlay.savefig(p_png, dpi=args.dpi, bbox_inches="tight")
            # Zusätzlich PDF, falls gewünscht
            p_pdf = os.path.join(args.outdir, "overlay.pdf")
            fig_overlay.savefig(p_pdf, bbox_inches="tight")

        plt.show()

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    if args.animation:
        anim_path = os.path.join(args.outdir, args.animation)
        fig_anim, ax_anim = plt.subplots(dpi=args.dpi)
        ax_anim.set_aspect("equal")
        ax_anim.set_xlabel("x [m]")
        ax_anim.set_ylabel("y [m]")

        def init():
            ax_anim.set_xlim(ax_overlay.get_xlim() if args.overlay else None)
            ax_anim.set_ylim(ax_overlay.get_ylim() if args.overlay else None)
            return []

        def update(frame: int):
            ax_anim.cla()
            ax_anim.set_aspect("equal")
            ax_anim.set_xlabel("x [m]")
            ax_anim.set_ylabel("y [m]")
            ax_anim.set_title(f"Ice Growth – Frame {frame+1}/{len(segments_list)}")
            for i in range(frame + 1):  # kumulativ bis zum aktuellen Frame
                plot_segments(ax_anim, segments_list[i], color=cmap(i), alpha=args.alpha, linewidth=args.linewidth)
            return []

        ani = animation.FuncAnimation(fig_anim, update, init_func=init, frames=len(segments_list), blit=False)

        # Writer wählen (ffmpeg bevorzugt, sonst Pillow)
        Writer = None
        if anim_path.lower().endswith((".mp4", ".mkv")):
            try:
                Writer = animation.FFMpegWriter
            except Exception:  # pragma: no cover
                print("ffmpeg nicht verfügbar – verwende GIF‑Ausgabe")
                anim_path = anim_path.rsplit(".", 1)[0] + ".gif"
                Writer = animation.PillowWriter
        else:
            Writer = animation.PillowWriter  # GIF

        writer = Writer(fps=args.fps)
        ani.save(anim_path, writer=writer, dpi=args.dpi)
        print(f"Animation gespeichert: {anim_path}")


if __name__ == "__main__":
    main()
