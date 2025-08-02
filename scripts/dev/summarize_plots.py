import glob, os, re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import scienceplots
plt.style.use(['science', 'no-latex'])

# ────────────── anpassen falls nötig ──────────────
CSV_PATTERN   = "0000*.csv"   # oder z.B. "*.csv"
OUTPUT_PDF    = "summary.pdf"
XLIM          = (0.1, 0.3)               # gleich wie bisher

# ────────────── CSVs laden ──────────────
csv_files = sorted(glob.glob(CSV_PATTERN))
if not csv_files:
    raise RuntimeError(f"Keine Dateien passend zu '{CSV_PATTERN}' gefunden.")

dfs        = [pd.read_csv(f) for f in csv_files]
var_names  = dfs[0].columns[1:]     # erste Spalte ist "s [m]"

# ────────────── Plotten ──────────────
with PdfPages(OUTPUT_PDF) as pdf:
    for var in var_names:
        plt.figure(figsize=(8, 5))
        for f, df in zip(csv_files, dfs):
            label = os.path.splitext(os.path.basename(f))[0]
            # Sortieren nach s – falls die Daten nicht bereits sortiert sind
            order = np.argsort(df["s [m]"].values)
            plt.plot(df["s [m]"].values[order],
                     df[var].values[order],
                     label=label,
                     linewidth=1.0)

        plt.xlabel("s [m]")
        plt.ylabel(var)
        plt.xlim(*XLIM)
        plt.title(f"{var} vs s – alle Dateien")
        plt.legend(fontsize="x-small", ncol=2, frameon=False)
        plt.tight_layout()
        pdf.savefig()
        plt.close()

print(f"Gesammelte Kurven-PDF gespeichert: {OUTPUT_PDF}")
