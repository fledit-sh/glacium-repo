from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Tuple


class Plotter(ABC):
    """Abstract interface for plotting backends.

    Concrete implementations wrap a specific plotting library while
    exposing a minimal, library-agnostic API.
    """

    @abstractmethod
    def new_figure(self, **kwargs: Any) -> Tuple[Any, Any]:
        """Return a new figure and axes pair.

        Parameters
        ----------
        **kwargs
            Backend specific figure options.

        Returns
        -------
        tuple
            Figure and axes objects provided by the backend.
        """

    @abstractmethod
    def line(self, ax: Any, x: Any, y: Any, *args: Any, **kwargs: Any) -> Any:
        """Plot a line on ``ax``.

        Parameters
        ----------
        ax
            Axes object to draw on.
        x, y
            Coordinates of the line.
        *args
            Positional backend arguments (e.g. format string).
        **kwargs
            Additional backend options.

        Returns
        -------
        Any
            Backend specific handle to the plotted line.
        """

    @abstractmethod
    def errorbar(self, ax: Any, x: Any, y: Any, yerr: Any, **kwargs: Any) -> Any:
        """Draw error bars on ``ax``.

        Parameters
        ----------
        ax
            Axes object to draw on.
        x, y
            Data points.
        yerr
            Symmetric or asymmetric errors.
        **kwargs
            Additional backend options.

        Returns
        -------
        Any
            Backend specific handle to the plotted elements.
        """

    @abstractmethod
    def scatter(self, ax: Any, x: Any, y: Any, **kwargs: Any) -> Any:
        """Create a scatter plot on ``ax``.

        Parameters
        ----------
        ax
            Axes object to draw on.
        x, y
            Coordinates of the points.
        **kwargs
            Additional backend options.

        Returns
        -------
        Any
            Backend specific handle to the scatter plot.
        """

    @abstractmethod
    def save(self, fig: Any, path: str | Path, **kwargs: Any) -> Path:
        """Write ``fig`` to ``path``.

        Parameters
        ----------
        fig
            Figure object returned by :meth:`new_figure`.
        path
            Destination file path.
        **kwargs
            Additional save options.

        Returns
        -------
        pathlib.Path
            The path where the figure was written.
        """

    @abstractmethod
    def close(self, fig: Any) -> None:
        """Close ``fig`` and release resources."""
