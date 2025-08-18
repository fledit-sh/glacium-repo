# Create a radar plot for Noel's case.yaml values with sensible mappings and ranges.
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import log10

# Raw case values from Noel
case = {
    "CASE_ROUGHNESS": 0.0004,            # m
    "CASE_CHARACTERISTIC_LENGTH": 0.200, # m
    "CASE_VELOCITY": 50,                 # m/s
    "CASE_ALTITUDE": 100,                # m
    "CASE_TEMPERATURE": 263.15,          # K
    "CASE_AOA": 4,                       # deg
    "CASE_MVD": 20,                      # µm (raw assumed to be µm? User's is 20 -> that's µm; keep as µm after conversion below)
    "CASE_LWC": 0.00052,                 # kg/m^3
    "CASE_YPLUS": 0.3,                   # -
    "PWS_REFINEMENT": 8                  # level
}

# Define mapping: unit conversion for readability + chosen ranges + scale type for normalization
# Ranges chosen to be broadly meaningful for AWE/icing predesign studies.
mapping = {
    "CASE_ROUGHNESS": {
        "label": "Surface roughness",
        "convert": lambda v: v * 1e6,  # m -> µm
        "unit": "µm",
        "min": 1,      # 1 µm (smooth paint)
        "max": 1000,   # 1000 µm (very rough ice/paint)
        "scale": "log"
    },
    "CASE_CHARACTERISTIC_LENGTH": {
        "label": "Characteristic length",
        "convert": lambda v: v,  # m
        "unit": "m",
        "min": 0.05,   # small section
        "max": 0.5,    # larger section
        "scale": "linear"
    },
    "CASE_VELOCITY": {
        "label": "Airspeed",
        "convert": lambda v: v,  # m/s
        "unit": "m/s",
        "min": 10,
        "max": 80,
        "scale": "linear"
    },
    "CASE_ALTITUDE": {
        "label": "Altitude (AGL)",
        "convert": lambda v: v,  # m
        "unit": "m",
        "min": 0,
        "max": 1000,
        "scale": "linear"
    },
    "CASE_TEMPERATURE": {
        "label": "Ambient temperature",
        "convert": lambda v: v - 273.15,  # K -> °C
        "unit": "°C",
        "min": -25,
        "max": 10,
        "scale": "linear"
    },
    "CASE_AOA": {
        "label": "Angle of attack",
        "convert": lambda v: v,  # deg
        "unit": "°",
        "min": -5,
        "max": 15,
        "scale": "linear"
    },
    "CASE_MVD": {
        "label": "MVD",
        "convert": lambda v: v,  # µm (already)
        "unit": "µm",
        "min": 5,
        "max": 50,
        "scale": "linear"
    },
    "CASE_LWC": {
        "label": "LWC",
        "convert": lambda v: v * 1000,  # kg/m^3 -> g/m^3
        "unit": "g/m³",
        "min": 0.05,
        "max": 1.5,
        "scale": "linear"
    },
    "CASE_YPLUS": {
        "label": "y+ (target)",
        "convert": lambda v: v,  # -
        "unit": "–",
        "min": 0.0,
        "max": 1.0,
        "scale": "linear"
    },
    "PWS_REFINEMENT": {
        "label": "PW mesh refinement",
        "convert": lambda v: v,  # level
        "unit": "lvl",
        "min": 0,
        "max": 10,
        "scale": "linear"
    },
}

def normalize(value, vmin, vmax, scale):
    # Clip to avoid issues
    if scale == "linear":
        if vmax == vmin:
            return 0.0
        return max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))
    elif scale == "log":
        # Ensure positive values
        value = max(value, 1e-12)
        vmin = max(vmin, 1e-12)
        vmax = max(vmax, vmin * (1 + 1e-6))
        return max(0.0, min(1.0, (math.log10(value) - math.log10(vmin)) / (math.log10(vmax) - math.log10(vmin))))
    else:
        return 0.0

# Build a dataframe of readable values and normalized values
rows = []
for key, cfg in mapping.items():
    raw = case.get(key, np.nan)
    disp = cfg["convert"](raw)
    norm = normalize(disp, cfg["min"], cfg["max"], cfg["scale"])
    rows.append({
        "Key": key,
        "Label": cfg["label"],
        "Value (display)": disp,
        "Unit": cfg["unit"],
        "Range min": cfg["min"],
        "Range max": cfg["max"],
        "Scale": cfg["scale"],
        "Normalized [0-1]": norm
    })

df = pd.DataFrame(rows)

# Show the dataframe to the user
from caas_jupyter_tools import display_dataframe_to_user
display_dataframe_to_user("Case parameters with mappings and normalization", df)

# Create radar plot from normalized values
labels = [r["label"] for r in rows]
values = [r["Normalized [0-1]"] for r in df.to_dict(orient="records")]

# Radar needs to be a closed loop
labels += [labels[0]]
values += [values[0]]

# Angles for each axis
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)

# Plot
fig = plt.figure(figsize=(7, 7))
ax = plt.subplot(111, polar=True)
ax.plot(angles, values, linewidth=2)
ax.fill(angles, values, alpha=0.25)
ax.set_thetagrids(angles * 180/np.pi, labels)

# Title with a brief note
ax.set_title("Radar plot of case parameters (normalized to chosen ranges)")

# Save figure
figpath = "/mnt/data/case_radar_plot.png"
plt.tight_layout()
plt.savefig(figpath, dpi=200)
figpath
