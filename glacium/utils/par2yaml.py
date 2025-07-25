#!/usr/bin/env python3
"""
Convert KEY DATA parameter files to YAML (KEY: DATA),
preserving comments, blank lines, and original order.

Usage:
    python param2yaml.py input.par > output.yaml
"""
import sys
from pathlib import Path

from .par_converter import YamlParConverter


converter = YamlParConverter()


def main():
    if len(sys.argv) < 2:
        print("Usage: python param2yaml.py <input-file>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    sys.stdout.write(converter.convert_file(path))


if __name__ == "__main__":
    main()
