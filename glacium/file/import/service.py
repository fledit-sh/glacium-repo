from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .meta import FileMeta
from .parsers import ConvergParser, TextParser
from .select import ParserSelector


@dataclass
class ParserService:
    selector: ParserSelector

    def parse(self, content: bytes | str, meta: FileMeta) -> Any:
        return self.selector.select(meta).parse(content, meta)


def build_default_parser_service() -> ParserService:
    text = TextParser()
    converg = ConvergParser()

    selector = ParserSelector(
        by_filetype={
            "converg.drop": converg,
            "converg.fensap": converg,
        },
        by_suffix={
            ".log": text,
            ".out": text,
            ".txt": text,
        },
        default=text,
    )

    return ParserService(selector=selector)
