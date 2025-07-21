from __future__ import annotations

from pathlib import Path
import shutil
from ruamel.yaml import YAML

__all__ = ["update"]

_yaml = YAML(typ="rt")          # round‑trip – preserves comments & order
_yaml.indent(mapping=2, sequence=4, offset=2)


def _deep_merge(base: dict, patch: dict) -> None:
    """Recursively merge *patch* into *base* in‑place."""
    for k, v in patch.items():
        if (
            k in base
            and isinstance(base[k], dict)
            and isinstance(v, dict)
        ):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def update(dest: str, src: str, *, root: Path | None = None) -> Path:
    """
    Overlay values from ``config/custom/src`` onto ``config/defaults/dest``.

    Returns
    -------
    Path
        Path to the updated destination YAML.
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
    if not dest_path.exists():
        # ensure the defaults file exists (copy pristine template if needed)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(custom_path, dest_path)  # first fill with something

    # --- merge ----------------------------------------------------------------
    with dest_path.open("r", encoding="utf‑8") as f:
        base_cfg = _yaml.load(f) or {}

    with custom_path.open("r", encoding="utf‑8") as f:
        patch_cfg = _yaml.load(f) or {}

    _deep_merge(base_cfg, patch_cfg)

    with dest_path.open("w", encoding="utf‑8") as f:
        _yaml.dump(base_cfg, f)

    return dest_path
