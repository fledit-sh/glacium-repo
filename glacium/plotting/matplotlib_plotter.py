from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple

from matplotlib import pyplot as plt

from .base import Plotter


class MatplotlibPlotter(Plotter):
    """`Plotter` implementation using :mod:`matplotlib`."""

    def new_figure(self, **kwargs: Any) -> Tuple[Any, Any]:
        fig, ax = plt.subplots(**kwargs)
        return fig, ax

    def line(self, ax: Any, x: Any, y: Any, *args: Any, **kwargs: Any) -> Any:
        return ax.plot(x, y, *args, **kwargs)

    def errorbar(self, ax: Any, x: Any, y: Any, yerr: Any, **kwargs: Any) -> Any:
        return ax.errorbar(x, y, yerr=yerr, **kwargs)

    def scatter(self, ax: Any, x: Any, y: Any, **kwargs: Any) -> Any:
        return ax.scatter(x, y, **kwargs)

    def save(self, fig: Any, path: str | Path, **kwargs: Any) -> Path:
        outfile = Path(path)
        fig.savefig(outfile, **kwargs)
        return outfile

    def close(self, fig: Any) -> None:
        plt.close(fig)


def get_default_plotter() -> MatplotlibPlotter:
    """Return the default :class:`MatplotlibPlotter` instance."""

    return MatplotlibPlotter()
