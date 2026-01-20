from __future__ import annotations

from dataclasses import dataclass
from .abc import Parser
from .meta import FileMeta
from .parsers import ConvergParser, TextParser
from .result import ConvResult
from .select import ParserSelector


@dataclass
class ParserService:
    selector: ParserSelector

    def parse(self, content: bytes | str, meta: FileMeta) -> ConvResult:
        return self.selector.select(meta).parse(content, meta)


def build_default_parser_service() -> ParserService:
    text: Parser = TextParser()
    converg: Parser = ConvergParser()

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
