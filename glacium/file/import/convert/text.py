from __future__ import annotations

from dataclasses import dataclass

from ..meta import FileMeta


@dataclass(frozen=True)
class TextParser:
    """Generic fallback: returns the whole text."""

    def parse(self, content: bytes | str, meta: FileMeta) -> str:
        if isinstance(content, bytes):
            return content.decode(errors="replace")
        return content
