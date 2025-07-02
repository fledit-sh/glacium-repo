#!/usr/bin/env python3
"""
fsp2yaml_flat.py – Macht aus FSP/CFG-Dateien eine *flache* YAML-Datei.
Nur einzelne numerische Tokens bleiben unquoted, alles andere wird als String
abgelegt. Kategorien? Haben wir gestern abgeschafft.

Autor: ChatGPT (TARS-Modus)
Lizenz: MIT
"""

import argparse
import shlex
import sys
from collections import OrderedDict  # wir benutzen es ja schon
from pathlib import Path

import yaml

# ---------------------------------------------------------------
from yaml import SafeDumper  # bereits installiert


def _represent_ordered_dict(dumper, data):
    # mapping-Tag + Erhalt der Einfügereihenfolge
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())


yaml.add_representer(OrderedDict, _represent_ordered_dict, Dumper=SafeDumper)
# ---------------------------------------------------------------

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML fehlt – `pip install pyyaml` und noch mal versuchen.")

# ---------------------------------------------------------------------------


def to_scalar(token: str):
    """Gibt int / float / string zurück – aber nur bei EINEM Token."""
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1]

    try:
        return int(token, 0)
    except ValueError:
        pass

    try:
        return float(token)
    except ValueError:
        return token


def parse_file(path: Path):
    """
    Liest die Datei in ein *flaches* OrderedDict: {key: value}
    Bei mehrfach vorkommenden Keys gewinnt die zuletzt gelesene Zeile.
    """
    data = OrderedDict()

    with path.open(encoding="utf-8") as fp:
        for line in fp:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                # Kommentare & leere Zeilen ignorieren
                continue

            parts = shlex.split(stripped, comments=False, posix=True)
            key, *raw_vals = parts

            if len(raw_vals) == 1:
                value = to_scalar(raw_vals[0])
            else:
                value = " ".join(raw_vals)

            data[key] = value

    return data


# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(
        description="Konvertiert FSP-Parameterdateien in flache YAML."
    )
    ap.add_argument("input", type=Path, help="Pfad zur Parameterdatei")
    ap.add_argument("-o", "--output", type=Path, help="Ziel-YAML (Default: *.yaml)")
    args = ap.parse_args()

    target = args.output or args.input.with_suffix(".yaml")
    data = parse_file(args.input)

    with target.open("w", encoding="utf-8") as out:
        yaml.safe_dump(
            data,
            out,
            sort_keys=False,
            allow_unicode=True,
            width=120,
            default_flow_style=False,
        )

    print(f"✅  Konvertiert: {args.input} → {target}")


if __name__ == "__main__":
    main()
