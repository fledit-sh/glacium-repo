#!/usr/bin/env python3
"""
Convert KEY DATA parameter files to a Jinja2 template:
KEY {{ KEY }}
Comments, blank lines, and order are preserved.

Usage:
    python param2j2.py input.par > template.j2
"""
import sys
from pathlib import Path

def convert_line(line: str) -> str:
    stripped = line.lstrip()

    # Pass through blank lines and pure comments
    if not stripped or stripped.startswith("#"):
        return line

    # Keep leading whitespace
    prefix_len = len(line) - len(stripped)
    prefix = line[:prefix_len]

    # Separate inline comment (if any)
    parts_before_comment = stripped.split("#", 1)
    main_part = parts_before_comment[0].rstrip()
    inline_comment = (" #" + parts_before_comment[1]) if len(parts_before_comment) == 2 else ""

    # KEY is first token
    key = main_part.split(None, 1)[0]

    # Emit Jinja2 placeholder with tight braces: {{ KEY }}
    return f"{prefix}{key} {{{{ {key} }}}}{inline_comment}\n"

def main():
    if len(sys.argv) < 2:
        print("Usage: python param2j2.py <input-file>", file=sys.stderr)
        sys.exit(1)

    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines(keepends=True):
        sys.stdout.write(convert_line(line))

if __name__ == "__main__":
    main()
