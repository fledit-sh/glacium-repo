#!/usr/bin/env bash
# -----------------------------
# run_xfoil.sh – Automatischer XFOIL-Lauf mit .in-Datei
# -----------------------------

set -euo pipefail

# Pfad zur xfoil.exe (anpassen falls nötig)
XFOIL="../../xfoil/xfoil.exe"

# Dein Eingabeskript
INPUT="increasepoints.in"
OUTPUT="${INPUT%.in}.out"

if [[ ! -f "$INPUT" ]]; then
    echo "▶ Eingabedatei $INPUT nicht gefunden."
    exit 1
fi

echo "▶ Starte XFOIL mit $INPUT ..."
"$XFOIL" < "$INPUT" > "$OUTPUT"
echo "▶ Fertig. Ausgabe in $OUTPUT"

# Dein Eingabeskript
INPUT="thickenTE.in"
OUTPUT="${INPUT%.in}.out"

if [[ ! -f "$INPUT" ]]; then
    echo "▶ Eingabedatei $INPUT nicht gefunden."
    exit 1
fi

echo "▶ Starte XFOIL mit $INPUT ..."
"$XFOIL" < "$INPUT" > "$OUTPUT"
echo "▶ Fertig. Ausgabe in $OUTPUT"