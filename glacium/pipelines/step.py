from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PipelineStep:
    """Single pipeline step configuration."""

    recipe_name: str
    case_params: Dict[str, object] | None = None
    post_jobs: List[str] = field(default_factory=list)

__all__ = ["PipelineStep"]
