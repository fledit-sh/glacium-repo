from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence
import csv

import numpy as np
import matplotlib.pyplot as plt
import scienceplots

from glacium.utils.solver_time import parse_execution_time, parse_time


class ConvergenceAnalyzer:
    """Helper class for analysing solver convergence history files."""

    # IO helpers -----------------------------------------------------
    def parse_headers(self, path: Path) -> list[str]:
        """Return column labels from the header section of ``path``."""
        labels: list[str] = []
        for line in path.read_text().splitlines():
            if not line.lstrip().startswith("#"):
                break
            if line.lstrip().startswith("#"):
                parts = line.split(maxsplit=2)
                if len(parts) >= 2:
                    labels.append(parts[-1].strip())
        return labels

    def read_history(self, file: str | Path, nrows: int | None = None) -> np.ndarray:
        """Return the last ``nrows`` rows from ``file``."""
        path = Path(file)
        data = [
            [float(val.replace("D", "E")) for val in line.split()]
            for line in path.read_text().splitlines()
            if not line.lstrip().startswith("#") and line.strip()
        ]
        arr = np.array(data, dtype=float)
        if nrows is not None:
            arr = arr[-nrows:]
        return arr

    def read_history_with_labels(
        self, file: str | Path, nrows: int | None = None
    ) -> tuple[list[str], np.ndarray]:
        """Return labels and data from ``file``."""
        path = Path(file)
        labels = self.parse_headers(path)
        data = [
            [float(val.replace("D", "E")) for val in line.split()]
            for line in path.read_text().splitlines()
            if not line.lstrip().startswith("#") and line.strip()
        ]
        arr = np.array(data, dtype=float)
        if nrows is not None:
            arr = arr[-nrows:]
        return labels, arr

    # Statistics -----------------------------------------------------
    def stats_last_n(self, data: np.ndarray, n: int = 15) -> tuple[np.ndarray, np.ndarray]:
        """Return column-wise mean and std of the last ``n`` rows in ``data``."""
        tail = data[-n:] if n else data
        return np.mean(tail, axis=0), np.std(tail, axis=0)

    def cl_cd_stats(self, directory: Path, n: int = 15) -> np.ndarray:
        """Return mean lift and drag coefficients from ``directory``."""
        results: list[tuple[int, float, float]] = []
        for file in sorted(Path(directory).glob("converg.fensap.*")):
            labels = self.parse_headers(file)
            try:
                cl_idx = labels.index("lift coefficient")
                cd_idx = labels.index("drag coefficient")
            except ValueError:
                continue
            data = self.read_history(file, n)
            tail = data[-n:] if n else data
            cl_mean = float(np.mean(tail[:, cl_idx]))
            cd_mean = float(np.mean(tail[:, cd_idx]))
            try:
                idx = int(file.name.split(".")[-1])
            except ValueError:
                idx = len(results)
            results.append((idx, cl_mean, cd_mean))
        return np.array(results, dtype=float)

    def execution_time(self, file: Path) -> float:
        """Return solver run time in seconds for ``file``."""
        value = parse_execution_time(file)
        if value is None:
            return 0.0
        return parse_time(value)

    def cl_cd_summary(self, directory: Path, n: int = 15) -> tuple[float, float, float, float]:
        """Return mean and std dev for lift and drag coefficients."""
        data = self.cl_cd_stats(directory, n)
        if data.size:
            cl_mean = float(data[:, 1].mean())
            cl_std = float(data[:, 1].std())
            cd_mean = float(data[:, 2].mean())
            cd_std = float(data[:, 2].std())
            return cl_mean, cl_std, cd_mean, cd_std
        return float("nan"), float("nan"), float("nan"), float("nan")

    def aggregate_report(
        self, directory: str | Path, n: int = 15
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Aggregate stats for all ``converg.fensap.*`` files in ``directory``."""
        root = Path(directory)
        means = []
        stds = []
        indices = []
        for file in sorted(root.glob("converg.fensap.*")):
            data = self.read_history(file, n)
            mean, std = self.stats_last_n(data, n)
            means.append(mean)
            stds.append(std)
            try:
                indices.append(int(file.name.split(".")[-1]))
            except ValueError:
                indices.append(len(indices))
        return (
            np.array(indices, dtype=int),
            np.vstack(means) if means else np.empty((0, 0)),
            np.vstack(stds) if stds else np.empty((0, 0)),
        )

    def project_cl_cd_stats(self, report_dir: Path, n: int = 15) -> tuple[float, float, float, float]:
        """Return overall mean and std deviation of lift/drag coefficients."""
        first = next(iter(sorted(Path(report_dir).glob("converg.fensap.*"))), None)
        if first is None:
            return float("nan"), float("nan"), float("nan"), float("nan")
        labels = self.parse_headers(first)
        try:
            cl_idx = labels.index("lift coefficient")
            cd_idx = labels.index("drag coefficient")
        except ValueError:
            return float("nan"), float("nan"), float("nan"), float("nan")
        _, means, stds = self.aggregate_report(report_dir, n)
        if not means.size:
            return float("nan"), float("nan"), float("nan"), float("nan")
        cl_mean = float(np.mean(means[:, cl_idx]))
        cl_std = float(np.mean(stds[:, cl_idx]))
        cd_mean = float(np.mean(means[:, cd_idx]))
        cd_std = float(np.mean(stds[:, cd_idx]))
        return cl_mean, cl_std, cd_mean, cd_std

    # Plotting -------------------------------------------------------
    def plot_stats(
        self,
        indices: Iterable[int],
        means: np.ndarray,
        stds: np.ndarray,
        out_dir: str | Path,
        labels: Iterable[str] | None = None,
    ) -> None:
        """Write plots visualising ``means`` and ``stds``."""
        plt.style.use(["science", "ieee"])
        plt.rcParams["text.usetex"] = False
        out = Path(out_dir)
        fig_dir = out / "figures"
        fig_dir.mkdir(parents=True, exist_ok=True)
        ind = np.array(list(indices))
        lbls = list(labels or [])
        for col in range(means.shape[1]):
            ylabel = lbls[col] if col < len(lbls) else f"column {col}"
            plt.figure()
            plt.errorbar(ind, means[:, col], yerr=stds[:, col], fmt="o-", capsize=3)
            plt.xlabel("multishot index")
            plt.ylabel(ylabel)
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(fig_dir / f"column_{col:02d}.png")
            plt.close()

    # High level helpers --------------------------------------------
    def analysis(self, cwd: Path, args: Sequence[str | Path]) -> None:
        """Aggregate convergence data and create plots."""
        if len(args) < 2:
            raise ValueError("analysis requires input and output directory")
        report_dir = Path(args[0])
        out_dir = Path(args[1])
        idx, means, stds = self.aggregate_report(report_dir)
        first = next(iter(sorted(report_dir.glob("converg.fensap.*"))), None)
        labels = self.parse_headers(first) if first else []
        if means.size:
            self.plot_stats(idx, means, stds, out_dir, labels)
        clcd = self.cl_cd_stats(report_dir)
        if clcd.size:
            out_dir.mkdir(parents=True, exist_ok=True)
            fig_dir = out_dir / "figures"
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

    def analysis_file(self, cwd: Path, args: Sequence[str | Path]) -> None:
        """Analyse a single convergence file and generate plots."""
        if len(args) < 2:
            raise ValueError("analysis_file requires input file and output directory")
        file = Path(args[0])
        out_dir = Path(args[1])
        labels, data = self.read_history_with_labels(file)
        out_dir.mkdir(parents=True, exist_ok=True)
        fig_dir = out_dir / "figures"
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
        mean, _ = self.stats_last_n(data, 15)
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
