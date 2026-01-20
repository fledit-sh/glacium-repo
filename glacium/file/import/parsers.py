from __future__ import annotations

from dataclasses import dataclass
import io
import re
import pandas as pd

from .abc import Parser
from .meta import FileMeta
from .result import ConvResult


@dataclass(frozen=True)
class ConvergParser(Parser):
    """
    Parses converg.* text files into a pandas DataFrame.
    - Header lines start with '#'
    - Data is whitespace-separated
    - Header lines often include leading column index, e.g. '#  1  time step'
    """

    def parse(self, content: bytes | str, meta: FileMeta) -> ConvResult:
        stream: io.TextIOBase
        if isinstance(content, bytes):
            stream = io.TextIOWrapper(io.BytesIO(content), errors="replace")
        else:
            stream = io.StringIO(content)

        header_lines: list[str] = []
        data_lines: list[str] = []

        # --- read file ONCE ---
        with stream as f:
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

        return ConvResult(kind="table", payload=df)


@dataclass(frozen=True)
class TextParser(Parser):
    """Generic fallback: returns the whole text."""

    def parse(self, content: bytes | str, meta: FileMeta) -> ConvResult:
        if isinstance(content, bytes):
            text = content.decode(errors="replace")
        else:
            text = content
        return ConvResult(kind="text", payload=text)
