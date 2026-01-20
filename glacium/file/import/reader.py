from __future__ import annotations

from .convert.converg import ConvergParser
from .convert.text import TextParser
from .select import ParserSelector, ParserService


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
