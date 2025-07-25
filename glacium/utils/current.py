from __future__ import annotations

"""Current project selection token."""

from pathlib import Path

from .selection_store import SelectionStore

PROJECT_TOKEN = SelectionStore(Path.home() / ".glacium_current")
