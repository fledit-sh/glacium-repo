from __future__ import annotations

from dataclasses import dataclass

from .abc import Parser
from .meta import FileMeta


@dataclass
class ParserSelector:
    by_filetype: dict[str, Parser]
    by_suffix: dict[str, Parser]
    default: Parser

    def select(self, meta: FileMeta) -> Parser:
        parser = self.by_filetype.get(meta.filetype)
        if parser is not None:
            return parser

        parser = self.by_suffix.get(meta.filepath.suffix.lower())
        if parser is not None:
            return parser

        return self.default
