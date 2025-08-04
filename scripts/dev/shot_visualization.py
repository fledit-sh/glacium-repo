import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import matplotlib as mpl
from matplotlib.ticker import MultipleLocator, FuncFormatter
from matplotlib.cm import get_cmap
import scienceplots

# --- Stil & Font ---
plt.style.use(['science', 'ieee'])
mpl.rcParams.update({
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "text.usetex": True
})

# --- Falldefinitionen ---
cases = {
    "S370": [(0, 370, "Main")],
    "SC10+S360": [(0, 10, "SC"), (10, 360, "Main")],
    "SC10+MS3x120": [(0, 10, "SC")] + [(10 + i * 120, 120, f"Shot {i + 1}") for i in range(3)],
    "SC10+MS6x60": [(0, 10, "SC")] + [(10 + i * 60, 60, f"Shot {i + 1}") for i in range(6)],
    "SC10+MS12x30": [(0, 10, "SC")] + [(10 + i * 30, 30, f"Shot {i + 1}") for i in range(12)],
}

# --- Farben ---
colors = {
    "SC": "lightgray",
    "Main_S370": "skyblue",
    "Main_SC10+S360": "skyblue",
}
colormap = get_cmap("Blues")
case_color_levels = {
    "SC10+MS3x120": 0.5,
    "SC10+MS6x60": 0.65,
    "SC10+MS12x30": 0.8,
}

# --- Plot-Größe ---
cm = 1 / 2.54
fig, ax = plt.subplots(figsize=(15 * cm, 8 * cm), constrained_layout=True)

# --- Y-Achsenbeschriftungen ---
y_labels = list(cases.keys())

# --- Balkenplot ---
for idx, (label, segments) in enumerate(cases.items()):
    for start, duration, seg_label in segments:
        if seg_label == "SC":
            color = colors["SC"]
        elif label in ["S370", "SC10+S360"]:
            color = colors[f"Main_{label}"]
        else:
            color = colormap(case_color_levels[label])

        ax.barh(idx, duration, left=start, height=0.5,
                color=color, edgecolor="black")

# --- Achsen ---
ax.set_xlim(0, 380)
ax.set_yticks(range(len(y_labels)))
ax.set_yticklabels(y_labels)

# X-Ticks: major alle 30 s, minor alle 10 s, Beschriftung alle 60 s
ax.xaxis.set_major_locator(MultipleLocator(30))
ax.xaxis.set_minor_locator(MultipleLocator(10))
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x)}" if x % 60 == 0 else ""))
ax.tick_params(axis='x', which='minor', length=3, color='black')

# Achsentitel & Diagrammtitel
ax.set_xlabel("Time [s]")
ax.set_title("Time Dependency Study")

# --- Speichern ---
from datetime import date

basename = f"fig_time_dependency_study_{date.today().isoformat()}"
plt.savefig(f"{basename}.pdf", format="pdf", bbox_inches='tight')
plt.savefig(f"{basename}.png", format="png", dpi=600, bbox_inches='tight', transparent=True)

plt.show()
