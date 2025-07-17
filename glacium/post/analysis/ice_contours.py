from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
import trimesh

__all__ = ["load_contours", "plot_overlay", "animate_growth"]


def _sorted_files(pattern: str) -> List[str]:
    files = list(Path().glob(pattern))
    if not files:
        raise FileNotFoundError("No STL files found – check pattern")

    def key(p: Path) -> int:
        import re

        m = re.search(r"([0-9]+)\.stl$", p.name)
        return int(m.group(1)) if m else -1

    return [str(p) for p in sorted(files, key=key)]


def _boundary_edges_xy(mesh: trimesh.Trimesh) -> np.ndarray:
    if hasattr(mesh, "edges_unique_counts"):
        edges = mesh.edges_unique[mesh.edges_unique_counts == 1]
    elif hasattr(mesh, "edges_unique_faces"):
        faces = mesh.edges_unique_faces
        edges = mesh.edges_unique[faces[:, 1] == -1]
    else:
        inv = mesh.edges_unique_inverse
        counts = np.bincount(inv, minlength=len(mesh.edges_unique))
        edges = mesh.edges_unique[counts == 1]

    return mesh.vertices[edges][:, :, :2]


def load_contours(pattern: str) -> List[np.ndarray]:
    files = _sorted_files(pattern)
    segments: List[np.ndarray] = []
    for fname in files:
        mesh = trimesh.load_mesh(fname, process=False)
        segments.append(_boundary_edges_xy(mesh))
    return segments


def plot_overlay(segments: Iterable[np.ndarray], outfile: str | Path, *, alpha: float = 0.9, linewidth: float = 1.2, dpi: int = 150) -> Path:
    segments = list(segments)
    cmap = plt.get_cmap("viridis", len(segments))
    fig, ax = plt.subplots(dpi=dpi)
    for idx, seg in enumerate(segments, start=1):
        color = cmap(idx - 1)
        for s in seg:
            ax.plot(s[:, 0], s[:, 1], color=color, alpha=alpha, linewidth=linewidth)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=1, vmax=len(segments)))
    plt.colorbar(sm, ax=ax, label="Frame")
    fig.tight_layout()
    outfile = Path(outfile)
    fig.savefig(outfile, dpi=dpi)
    plt.close(fig)
    return outfile


def animate_growth(segments: Iterable[np.ndarray], outfile: str | Path, *, fps: int = 10, alpha: float = 0.9, linewidth: float = 1.2, dpi: int = 150) -> Path:
    segments = list(segments)
    cmap = plt.get_cmap("viridis", len(segments))
    fig, ax = plt.subplots(dpi=dpi)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")

    def init() -> list[plt.Artist]:
        ax.set_xlim(min(seg[:, :, 0].min() for seg in segments), max(seg[:, :, 0].max() for seg in segments))
        ax.set_ylim(min(seg[:, :, 1].min() for seg in segments), max(seg[:, :, 1].max() for seg in segments))
        return []

    def update(frame: int) -> list[plt.Artist]:
        ax.cla()
        ax.set_aspect("equal")
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
        for i in range(frame + 1):
            for s in segments[i]:
                ax.plot(s[:, 0], s[:, 1], color=cmap(i), alpha=alpha, linewidth=linewidth)
        ax.set_title(f"Ice Growth – Frame {frame+1}/{len(segments)}")
        return []

    ani = animation.FuncAnimation(fig, update, init_func=init, frames=len(segments), blit=False)

    outfile = Path(outfile)
    writer: animation.AbstractMovieWriter
    if outfile.suffix.lower() in {".mp4", ".mkv"}:
        try:
            writer = animation.FFMpegWriter(fps=fps)
        except Exception:
            outfile = outfile.with_suffix(".gif")
            writer = animation.PillowWriter(fps=fps)
    else:
        writer = animation.PillowWriter(fps=fps)

    ani.save(outfile, writer=writer, dpi=dpi)
    plt.close(fig)
    return outfile


def main() -> None:
    """CLI entry point for contour overlay and animation."""
    import argparse

    ap = argparse.ArgumentParser(description="Visualise a series of STL ice contours")
    ap.add_argument("pattern", help="Glob pattern for STL files")
    ap.add_argument("-o", "--output", type=Path, required=True, help="Output file")
    ap.add_argument("--animate", action="store_true", help="Create animation instead of static overlay")
    ap.add_argument("--fps", type=int, default=10, help="Frames per second for animation")
    ap.add_argument("--alpha", type=float, default=0.9, help="Line alpha value")
    ap.add_argument("--linewidth", type=float, default=1.2, help="Line width")
    ap.add_argument("--dpi", type=int, default=150, help="Figure resolution")
    args = ap.parse_args()

    segments = load_contours(args.pattern)
    if args.animate:
        animate_growth(segments, args.output, fps=args.fps, alpha=args.alpha, linewidth=args.linewidth, dpi=args.dpi)
    else:
        plot_overlay(segments, args.output, alpha=args.alpha, linewidth=args.linewidth, dpi=args.dpi)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
