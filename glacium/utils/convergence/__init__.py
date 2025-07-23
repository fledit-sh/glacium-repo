"""Helpers for analysing FENSAP convergence history files."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .io import parse_headers, read_history, read_history_with_labels
from .stats import (
    stats_last_n,
    cl_cd_stats,
    execution_time,
    cl_cd_summary,
    project_cl_cd_stats,
    aggregate_report,
)
from .plot import plot_stats

__all__ = [
    "parse_headers",
    "read_history",
    "read_history_with_labels",
    "stats_last_n",
    "cl_cd_stats",
    "execution_time",
    "cl_cd_summary",
    "project_cl_cd_stats",
    "aggregate_report",
    "plot_stats",
    "analysis",
    "analysis_file",
]


def analysis(cwd: Path, args: Sequence[str | Path]) -> None:
    """Aggregate convergence data and create plots."""

    if len(args) < 2:
        raise ValueError("analysis requires input and output directory")

    report_dir = Path(args[0])
    out_dir = Path(args[1])
    fig_dir = out_dir / "figures"

    idx, means, stds = aggregate_report(report_dir)

    first = next(iter(sorted(report_dir.glob("converg.fensap.*"))), None)
    labels = parse_headers(first) if first else []

    if means.size:
        plot_stats(idx, means, stds, out_dir, labels)

    clcd = cl_cd_stats(report_dir)
    if clcd.size:
        import numpy as np
        import matplotlib.pyplot as plt

        out_dir.mkdir(parents=True, exist_ok=True)
        fig_dir.mkdir(parents=True, exist_ok=True)

        np.savetxt(
            out_dir / "cl_cd_stats.csv",
            clcd,
            delimiter=",",
            header="index,CL,CD",
            comments="",
        )

        plt.figure()
        plt.plot(clcd[:, 0], clcd[:, 1], marker=None)
        plt.xlabel("multishot index")
        plt.ylabel("CL")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(fig_dir / "cl.png")
        plt.close()

        plt.figure()
        plt.plot(clcd[:, 0], clcd[:, 2], marker=None)
        plt.xlabel("multishot index")
        plt.ylabel("CD")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(fig_dir / "cd.png")
        plt.close()

        plt.figure()
        plt.plot(clcd[:, 0], clcd[:, 1], label="CL", marker=None)
        plt.plot(clcd[:, 0], clcd[:, 2], label="CD", marker=None)
        plt.xlabel("multishot index")
        plt.ylabel("coefficient")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig(fig_dir / "cl_cd.png")
        plt.close()


def analysis_file(cwd: Path, args: Sequence[str | Path]) -> None:
    """Analyse a single FENSAP convergence file and generate plots."""

    if len(args) < 2:
        raise ValueError("analysis_file requires input file and output directory")

    file = Path(args[0])
    out_dir = Path(args[1])
    fig_dir = out_dir / "figures"

    import numpy as np
    import matplotlib.pyplot as plt
    import csv

    labels, data = read_history_with_labels(file)

    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    iterations = np.arange(1, data.shape[0] + 1)
    for col in range(data.shape[1]):
        plt.figure()
        plt.plot(iterations, data[:, col], marker=None)
        plt.xlabel("iteration")
        ylabel = labels[col] if col < len(labels) else f"column {col}"
        plt.ylabel(ylabel)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(fig_dir / f"column_{col:02d}.png")
        plt.close()

    mean, _ = stats_last_n(data, 15)
    variance = np.var(data[-15:], axis=0)

    with (out_dir / "stats.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["label", "mean", "variance"])
        for col in range(data.shape[1]):
            label = labels[col] if col < len(labels) else f"column {col}"
            writer.writerow([label, mean[col], variance[col]])

    try:
        cl_idx = labels.index("lift coefficient")
        cd_idx = labels.index("drag coefficient")
    except ValueError:
        return

    clcd = np.column_stack((iterations, data[:, cl_idx], data[:, cd_idx]))
    np.savetxt(
        out_dir / "cl_cd_stats.csv",
        clcd,
        delimiter=",",
        header="index,CL,CD",
        comments="",
    )

    plt.figure()
    plt.plot(iterations, data[:, cl_idx], marker=None)
    plt.xlabel("iteration")
    plt.ylabel("CL")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(fig_dir / "cl.png")
    plt.close()

    plt.figure()
    plt.plot(iterations, data[:, cd_idx], marker=None)
    plt.xlabel("iteration")
    plt.ylabel("CD")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(fig_dir / "cd.png")
    plt.close()

    plt.figure()
    plt.plot(iterations, data[:, cl_idx], label="CL", marker=None)
    plt.plot(iterations, data[:, cd_idx], label="CD", marker=None)
    plt.xlabel("iteration")
    plt.ylabel("coefficient")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "cl_cd.png")
    plt.close()
