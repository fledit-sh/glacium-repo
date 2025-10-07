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

# --- Parameter ---
SC_DURATION = 10
MS_TOTAL = 480  # Gesamtvereisung nach SC für alle Multishots

def make_multishot(n_shots: int, label: str):
    shot_dur = MS_TOTAL / n_shots
    segs = [(0, SC_DURATION, "SC")]
    for i in range(n_shots):
        start = SC_DURATION + i * shot_dur
        segs.append((start, shot_dur, f"Shot {i+1}"))
    return label, segs

# --- Falldefinitionen ---
cases = {
    "S490": [(0, 490, "Main")],
    "SC10+S480": [(0, SC_DURATION, "SC"), (SC_DURATION, 480, "Main")],
}

# Multishot-Fälle
for name, segs in [
    make_multishot(2,  "SC10+MS2x240"),
    make_multishot(4,  "SC10+MS4x120"),
    make_multishot(8,  "SC10+MS8x60"),
]:
    cases[name] = segs

# --- Farben ---
colors = {
    "SC": "lightgray",
    "Main_S490": "#a6d8ff",
    "Main_SC10+S480": "#7ec3ff",
}
colormap = get_cmap("Blues")
ms_levels = {
    "SC10+MS2x240": 0.55,
    "SC10+MS4x120": 0.7,
    "SC10+MS8x60":  0.85,
}

# --- Plot-Größe ---
cm = 1 / 2.54
fig, ax = plt.subplots(figsize=(15 * cm, 8 * cm), constrained_layout=False)
fig.subplots_adjust(bottom=0.28)  # Platz für Legende unten

# --- Y-Achse ---
y_labels = list(cases.keys())

# --- Balkenplot ---
for idx, (label, segments) in enumerate(cases.items()):
    for start, duration, seg_label in segments:
        if seg_label == "SC":
            color = colors["SC"]
        elif label in ["S490", "SC10+S480"]:
            color = colors.get(f"Main_{label}", colormap(0.6))
        else:
            color = colormap(ms_levels[label])
        ax.barh(idx, duration, left=start, height=0.5,
                color=color, edgecolor="black")

# --- Achsen ---
max_time = max(start + duration for segs in cases.values() for start, duration, _ in segs)
xmax = int(np.ceil((max_time + 10) / 10) * 10)
ax.set_xlim(0, xmax)
ax.set_yticks(range(len(y_labels)))
ax.set_yticklabels(y_labels)

# X-Ticks: major 30 s, minor 10 s, Beschriftung alle 60 s
ax.xaxis.set_major_locator(MultipleLocator(30))
ax.xaxis.set_minor_locator(MultipleLocator(10))
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x)}" if x % 60 == 0 else ""))
ax.tick_params(axis='x', which='minor', length=3, color='black')

# Achsentitel & Diagrammtitel
ax.set_xlabel("Time [s]")
ax.set_title("Time Dependency Study")

# --- Legende unter dem Plot ---
legend_patches = [
    mpatches.Patch(facecolor=colors["SC"], edgecolor="black", label="SC (10 s)"),
    mpatches.Patch(facecolor=colors["Main_S490"], edgecolor="black", label="S490"),
    mpatches.Patch(facecolor=colors["Main_SC10+S480"], edgecolor="black", label="SC10+S480"),
    mpatches.Patch(facecolor=colormap(ms_levels["SC10+MS2x240"]), edgecolor="black", label="SC10+MS2x240"),
    mpatches.Patch(facecolor=colormap(ms_levels["SC10+MS4x120"]), edgecolor="black", label="SC10+MS4x120"),
    mpatches.Patch(facecolor=colormap(ms_levels["SC10+MS8x60"]),  edgecolor="black", label="SC10+MS8x60"),
]
# fig.legend(handles=legend_patches, loc="lower center", ncol=3, frameon=True, bbox_to_anchor=(0.5, 0.02))

# --- Speichern ---
from datetime import date
basename = f"fig_time_dependency_study_{date.today().isoformat()}"
plt.savefig(f"{basename}.pdf", format="pdf", bbox_inches='tight')
plt.savefig(f"{basename}.png", format="png", dpi=600, bbox_inches='tight', transparent=True)

plt.show()
