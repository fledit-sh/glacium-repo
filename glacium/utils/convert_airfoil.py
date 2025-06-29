# glacium/utils/convert_xfoil.py
from pathlib import Path

def xfoil_to_pointwise(cwd: Path, args: list[str]) -> None:
    """args[0] = Eingabe-Dateiname, args[1] = Ausgabe-Datei."""
    src = cwd / args[0]
    dst = cwd / args[1]

    lines = src.read_text().splitlines()
    name  = lines[0].strip()     # „AH 63-K-127/24“
    pts   = [l.strip().split() for l in lines[1:]]
    n     = len(pts)

    with dst.open("w") as f:
        f.write(f"{n}\n")      # Punktzahl
        for x, y, *_ in pts:     # XFOIL hat nur x,y
            f.write(f"{float(x):12.6f} {float(y):10.6f}  0.000000\n")
