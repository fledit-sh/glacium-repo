from __future__ import annotations

from typing import Protocol, Any
import re

import logging
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import pandas as pd

logger = logging.getLogger("sim")

PROJECT_ROOT = Path("")

@dataclass(frozen=True)
class FileMeta:
    filepath: Path
    filetype: str
    filedate: datetime
    shot: int | None

@dataclass
class Indexer:
    root: Path
    files: List[FileMeta] = field(default_factory=list)

    def __post_init__(self):
        self.index_files()

    def index_files(self) -> None:
        files = []
        for p in self.root.rglob("*"):

            if p.is_file():
                tokens = p.name.split(".")

                shot = None
                if tokens[-1].isdigit():
                    shot = int(tokens.pop(-1))

                filetype = ".".join(tokens)
                filedate = datetime.fromtimestamp(p.stat().st_mtime)

                files.append(
                    FileMeta(
                        filepath=p,
                        filetype=filetype,
                        filedate=filedate,
                        shot=shot,
                    )
                )

        self.files = files




# ----------------------------
# Input metadata (from Indexer)
# ----------------------------

@dataclass(frozen=True)
class FileMeta:
    filepath: Path
    filetype: str          # e.g. "converg.drop" or "converg.fensap"
    filedate: datetime
    shot: int | None


# ----------------------------
# Standard parser interface
# ----------------------------

class Parser(Protocol):
    def parse(self, meta: FileMeta) -> Any: ...


# ----------------------------
# Concrete parsers
# ----------------------------

from dataclasses import dataclass
from pathlib import Path
import io
import re
import pandas as pd


@dataclass(frozen=True)
class ConvergParser:
    """
    Parses converg.* text files into a pandas DataFrame.
    - Header lines start with '#'
    - Data is whitespace-separated
    - Header lines often include leading column index, e.g. '#  1  time step'
    """

    def parse(self, meta: "FileMeta") -> pd.DataFrame:
        path: Path = meta.filepath

        header_lines: list[str] = []
        data_lines: list[str] = []

        # --- read file ONCE ---
        with path.open("r", errors="replace") as f:
            for line in f:
                if line.startswith("#") and not data_lines:
                    header_lines.append(line)
                else:
                    data_lines.append(line)

        # --- build + sanitize column names ---
        columns: list[str] = []
        for line in header_lines:
            text = line[1:].strip()  # remove '#'
            parts = text.split()

            # drop leading column index
            if parts and parts[0].isdigit():
                parts = parts[1:]

            col = " ".join(parts).strip()

            name = col.lower().replace("%", "percent")
            name = re.sub(r"[^\w]+", "_", name)
            name = re.sub(r"_+", "_", name).strip("_")

            columns.append(name)

        # --- parse data from in-memory buffer ---
        df = pd.read_csv(
            io.StringIO("".join(data_lines)),
            sep=r"\s+",
            header=None,
            names=columns if columns else None,
            engine="python",
        )

        # --- postprocess ---
        for col in ("time_step", "newton_iteration"):
            if col not in df.columns:
                continue

            s = df[col]
            if s.dtype == object and s.str.fullmatch(r"-?\d+").all():
                df[col] = s.astype("int64")

        return df



@dataclass(frozen=True)
class TextParser:
    """Generic fallback: returns the whole text."""
    def parse(self, meta: FileMeta) -> str:
        return meta.filepath.read_text(errors="replace")


# ----------------------------
# Selector (registry-based)
# ----------------------------

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


# ----------------------------
# Convenience: parse via selector
# ----------------------------

@dataclass
class ParserService:
    selector: ParserSelector

    def parse(self, meta: FileMeta) -> Any:
        return self.selector.select(meta).parse(meta)


# ----------------------------
# Example wiring
# ----------------------------

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


# ----------------------------
# Usage
# ----------------------------

if __name__ == "__main__":
    service = build_default_parser_service()

    meta = FileMeta(
        filepath=Path("converg.drop.000001"),
        filetype="converg.drop",
        filedate=datetime.now(),
        shot=1,
    )

    df = service.parse(meta)  # pandas DataFrame
    print(df.head())
