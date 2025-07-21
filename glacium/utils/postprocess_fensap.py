import pyvista as pv
import numpy as np
from pathlib import Path

"""
Automatischer Slice‑Plotter für Tecplot‑Dateien
------------------------------------------------
* Erstellt für Noel (AWE‑Vereisung) 2025‑07‑18
* Liest eine Tecplot‑Datei, erzeugt einen Z‑Slice und legt für **alle** Punkt‑Variablen
  jeweils zwei Bilder ab:
  1. Gesamter Slice (mit rotem Rahmen für den Zoom‑Ausschnitt)
  2. Zoom‑Ausschnitt exakt auf das angegebene Bounding‑Box‑Fenster

Ändere `FILE` und `ZOOM_BOUNDS`, wenn du an anderen Fällen arbeitest.
"""

FILE = "soln.dat"  # Tecplot‑Datei
OUTDIR = Path("plots")
OUTDIR.mkdir(exist_ok=True)

# -----------------------------
# Tecplot laden
# -----------------------------
reader = pv.TecplotReader(FILE)
mesh = reader.read()
grid = mesh[0] if isinstance(mesh, pv.MultiBlock) else mesh

# -----------------------------
# Problematische Namen bereinigen & Zusatzfelder erzeugen
# -----------------------------
RENAME_MAP = {
    "V1-velocity [m_s]; Velocity": "Vx",
    "V2-velocity [m_s]": "Vy",
    "V3-velocity [m_s]": "Vz",
    "Pressure [Pa]": "p",
}
for old, new in RENAME_MAP.items():
    if old in grid.point_data and new not in grid.point_data:
        grid.rename_array(old, new)

# Geschwindigkeitsbetrag nachträglich anlegen (falls Komponenten vorhanden)
if all(k in grid.point_data for k in ("Vx", "Vy", "Vz")) and "VelMag" not in grid.point_data:
    v = np.column_stack([grid["Vx"], grid["Vy"], grid["Vz"]])
    grid["VelMag"] = np.linalg.norm(v, axis=1)

# -----------------------------
# Slice & Zoom‑Fenster vorbereiten
# -----------------------------
SLICE_NORMAL = "z"
slc = grid.slice(normal=SLICE_NORMAL)

# --- Zoom‑Fenster (anpassen, falls nötig) ---
ZOOM_BOUNDS = (
    -0.5,   # xmin
    0.8,   # xmax
   -0.5,   # ymin
    0.5,   # ymax
    slc.bounds[4],  # zmin (Slice‑Ebene)
    slc.bounds[5],  # zmax (Slice‑Ebene)
)
zoom_box = pv.Box(bounds=ZOOM_BOUNDS)
slc_zoom = slc.clip_box(ZOOM_BOUNDS, invert=False)  # hält nur den Inneren Teil

# -----------------------------
# Kamera‑Utility
# -----------------------------

def make_topdown(bounds):
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2
    cz = (zmin + zmax) / 2
    width = xmax - xmin
    height = ymax - ymin
    cam = pv.Camera()
    cam.position = (cx, cy, cz + 10.0)
    cam.focal_point = (cx, cy, cz)
    cam.view_up = (0, 1, 0)
    cam.parallel_projection = True
    # exakt auf das größere Seitenverhältnis begrenzen
    cam.parallel_scale = max(width, height) / 2.0
    return cam

# -----------------------------
# Plot‑Funktion
# -----------------------------

def plot_slice(dataset, bounds, var_name, is_zoom, cmap="plasma"):
    arr = dataset[var_name]
    vmin, vmax = float(np.nanmin(arr)), float(np.nanmax(arr))

    bar = dict(
        title=f"{var_name}",
        fmt="%.2g",
        n_labels=4,
        title_font_size=14,
        label_font_size=12,
        vertical=False,
        position_x=0.25,
        position_y=0.02,
        width=0.5,
        height=0.08,
        color="black",
    )

    p = pv.Plotter(off_screen=True, window_size=(1600, 1200))
    p.add_mesh(dataset, scalars=var_name, cmap=cmap, clim=[vmin, vmax], scalar_bar_args=bar)

    if not is_zoom:
        # roten Rahmen nur bei Gesamtansicht
        p.add_mesh(zoom_box, color="red", style="wireframe", line_width=4)

    p.camera = make_topdown(bounds)
    return p

# -----------------------------
# Haupt‑Loop: alle Punkt‑Variablen
# -----------------------------
print("\n=== Verfügbare Punkt‑Variablen ===")
for vname in grid.point_data.keys():
    print("  •", vname)
print()

for var in grid.point_data.keys():
    # Vollbild
    full_plot = plot_slice(slc, slc.bounds, var, is_zoom=False)
    full_file = OUTDIR / f"{var}_full.png"
    full_plot.show(screenshot=str(full_file))
    print(f"✔ {full_file.name} gespeichert")

    # Zoom‑Bild
    zoom_plot = plot_slice(slc_zoom, ZOOM_BOUNDS, var, is_zoom=True)
    zoom_file = OUTDIR / f"{var}_zoom.png"
    zoom_plot.show(screenshot=str(zoom_file))
    print(f"✔ {zoom_file.name} gespeichert")

print(f"\nAlle Plots wurden in {OUTDIR.resolve()} abgelegt.")
