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

from .par_converter import JinjaParConverter

converter = JinjaParConverter()

def main():
    if len(sys.argv) < 2:
        print("Usage: python param2j2.py <input-file>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    sys.stdout.write(converter.convert_file(path))

if __name__ == "__main__":
    main()
