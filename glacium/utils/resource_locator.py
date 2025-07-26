from __future__ import annotations

from pathlib import Path


class ResourceLocator:
    """Locate built-in config and font files."""

    def __init__(self, repo_root: Path | None = None, pkg_root: Path | None = None) -> None:
        root = Path(__file__).resolve()
        self.repo_root = repo_root or root.parents[2]
        self.pkg_root = pkg_root or root.parents[1]

    # ------------------------------------------------------------------
    def global_default_config(self) -> Path:
        """Return ``config/defaults/global_default.yaml``."""
        a = self.repo_root / "config" / "defaults" / "global_default.yaml"
        b = self.pkg_root / "config" / "defaults" / "global_default.yaml"
        return a if a.exists() else b

    def default_case_file(self) -> Path:
        """Return ``config/defaults/case.yaml``."""
        a = self.repo_root / "config" / "defaults" / "case.yaml"
        b = self.pkg_root / "config" / "defaults" / "case.yaml"
        return a if a.exists() else b

    def dejavu_font_file(self) -> Path:
        """Return ``DejaVuSans.ttf`` for PDF reports."""
        a = self.repo_root / "glacium" / "DejaVuSans.ttf"
        b = self.pkg_root / "DejaVuSans.ttf"
        return a if a.exists() else b
