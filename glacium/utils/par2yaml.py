#!/usr/bin/env python3
"""
Convert KEY DATA parameter files to YAML (KEY: DATA),
preserving comments, blank lines, and original order.

Usage:
    python param2yaml.py input.par > output.yaml
"""
import sys
from pathlib import Path


def convert_line(line: str) -> str:
    stripped = line.lstrip()

    # Pass through blank lines and pure comment lines unchanged
    if not stripped or stripped.startswith("#"):
        return line

    # -------- parameter line --------------------------------------------------
    # KEY is everything up to the first whitespace; the rest is the value
    key_end = stripped.find(" ")
    if key_end == -1:                         # defensive fallback
        return stripped + "\n"

    key = stripped[:key_end]
    value = stripped[key_end + 1 :].lstrip()  # keep any inline comment

    # Emit key flush‑left (no leading prefix) ⇒ valid top‑level YAML
    return f"{key}: {value}\n"


def main():
    if len(sys.argv) < 2:
        print("Usage: python param2yaml.py <input-file>", file=sys.stderr)
        sys.exit(1)

    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines(keepends=True):
        sys.stdout.write(convert_line(line))


if __name__ == "__main__":
    main()
