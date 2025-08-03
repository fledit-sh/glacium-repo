import subprocess
import re
import matplotlib.pyplot as plt
from pathlib import Path

def get_node_count(grid_file: Path, exe="convertgrid.exe") -> int:
    result = subprocess.run([exe, "-d", str(grid_file)], capture_output=True, text=True)
    output = result.stdout
    for line in output.splitlines():
        if match := re.search(r"Number of nodes\s*[:=]\s*(\d+)", line, re.IGNORECASE):
            return int(match.group(1))
    print(f"[WARN] Keine Knotenzahl gefunden in {grid_file.name}")
    return 0

def plot_nodes_per_shot(folder: Path):
    files = sorted(folder.glob("grid.ice.[0-9][0-9][0-9][0-9][0-9][0-9]"))

    shots = []
    node_counts = []

    for f in files:
        shot_number = int(f.name.split(".")[-1])
        count = get_node_count(f)
        print(f"{f.name}: {count} nodes")
        shots.append(shot_number)
        node_counts.append(count)

    if not shots or not node_counts:
        print("[ERROR] Keine gültigen Daten zum Plotten.")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(shots, node_counts, marker='o')
    plt.xlabel("Shot-Nummer")
    plt.ylabel("Anzahl Knoten")
    plt.title("Knotenzahl pro Shot")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Ausführung
plot_nodes_per_shot(Path(""))
