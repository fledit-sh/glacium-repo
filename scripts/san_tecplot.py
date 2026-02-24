# sanitize_tecplot.py
from __future__ import annotations

import re
from pathlib import Path

# Token, das wie float aussieht und am Ende "+123" oder "-123" hat,
# aber KEIN "E" oder "D" enthält -> füge "E" ein.
_BAD_EXP = re.compile(
    r"""
    (?P<num>
        [+-]?                  # optional sign
        (?:\d+\.\d*|\d*\.\d+|\d+)  # mantissa
    )
    (?P<exp>[+-]\d{2,4})       # exponent without E/D
    \b
    """,
    re.VERBOSE,
)

def sanitize_tecplot(in_path: Path, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with in_path.open("r", errors="replace") as fin, out_path.open("w", newline="\n") as fout:
        for line in fin:
            # nur auf Zeilen anwenden, die numerisch sind (Performance + weniger False-Positives)
            # Heuristik: wenn Zeile ein E/D oder viele Ziffern enthält, versuchen wir es.
            if any(ch.isdigit() for ch in line):
                # ersetze nur dort, wo kein E/D im Token steckt:
                # wir machen das robust, indem wir zunächst Tokens ohne E/D fixen,
                # aber Tokens mit E/D unangetastet lassen.
                def repl(m: re.Match) -> str:
                    s = m.group(0)
                    # falls bereits E oder D vorkommt -> nicht anfassen
                    if "E" in s.upper() or "D" in s.upper():
                        return s
                    return f"{m.group('num')}E{m.group('exp')}"

                line = _BAD_EXP.sub(repl, line)

            fout.write(line)

if __name__ == "__main__":
    inp = Path("swimsol.ice.000020.dat")
    out = Path("swimsol.ice.000020.sanitized.dat")
    sanitize_tecplot(inp, out)
    print("Wrote:", out)