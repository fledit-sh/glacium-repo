from __future__ import annotations

"""Current job selection token."""

from pathlib import Path

from .selection_store import SelectionStore

JOB_TOKEN = SelectionStore(Path.home() / ".glacium_current_job")
