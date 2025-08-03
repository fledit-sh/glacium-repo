import re
from pathlib import Path

def parse_cas_ascii(filepath: str) -> dict:
    cell_counts = {
        "tet": 0,
        "pyramid": 0,
        "wedge": 0,
        "hex": 0,
        "polyhedron": 0,
        "total": 0
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    patterns = {
        "total": r"Total Number of Cells\s*:\s*(\d+)",
        "tet": r"Tet cells\s*:\s*(\d+)",
        "pyramid": r"Pyramid cells\s*:\s*(\d+)",
        "wedge": r"Wedge cells\s*:\s*(\d+)",
        "hex": r"Hex cells\s*:\s*(\d+)",
        "polyhedron": r"Polyhedron cells\s*:\s*(\d+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            cell_counts[key] = int(match.group(1))

    return cell_counts

# Beispielnutzung
path = "mesh.cas"
counts = parse_cas_ascii(path)

# Ausgabe
for typ, anz in counts.items():
    print(f"{typ:<10}: {anz}")
