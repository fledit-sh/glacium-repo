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
    # Keep blank lines and pure comment lines unchanged
    stripped = line.lstrip()
    if not stripped or stripped.startswith("#"):
        return line

    # Preserve leading whitespace
    prefix_len = len(line) - len(stripped)
    prefix = line[:prefix_len]

    # Split once: key = first token, value = rest
    key_end = stripped.find(" ")
    if key_end == -1:               # Should not happen if format is KEY DATA
        return line
    key = stripped[:key_end]
    value = stripped[key_end + 1 :].lstrip()  # keep inline comment, if any

    return f"{prefix}{key}: {value}\n"

def main():
    if len(sys.argv) < 2:
        print("Usage: python param2yaml.py <input-file>", file=sys.stderr)
        sys.exit(1)

    for line in Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True):
        sys.stdout.write(convert_line(line))

if __name__ == "__main__":
    main()
