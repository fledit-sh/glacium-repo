from __future__ import annotations

from pathlib import Path
import shutil

__all__ = ["update"]


def update(dest: str, src: str, *, root: Path | None = None) -> Path:
    """Overwrite a default config file with a custom version.

    Parameters
    ----------
    dest:
        File name under ``config/defaults`` to update, e.g. ``"global_default.yaml"``.
    src:
        File name under ``config/custom`` to copy from, e.g. ``"fensap.yaml"``.
    root:
        Optional base directory used instead of the repository root. This is
        mainly useful for testing.

    Returns
    -------
    Path
        Path to the updated destination file.
    """
    base = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    pkg_root = Path(__file__).resolve().parent

    custom_repo = base / "config" / "custom" / src
    custom_pkg = pkg_root / "config" / "custom" / src
    defaults_repo = base / "config" / "defaults" / dest
    defaults_pkg = pkg_root / "config" / "defaults" / dest

    custom_path = custom_repo if custom_repo.exists() else custom_pkg
    dest_path = defaults_repo if defaults_repo.exists() else defaults_pkg

    if not custom_path.exists():
        raise FileNotFoundError(custom_path)
    if not dest_path.parent.exists():
        dest_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(custom_path, dest_path)
    return dest_path
