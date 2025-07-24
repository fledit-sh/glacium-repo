import numpy as np
import matplotlib.pyplot as plt
import scienceplots
plt.style.use(['science', 'no-latex'])

# ---------- Load profile ----------
x, y = np.loadtxt("AH63K127.dat", skiprows=1).T

# ---------- Split upper & lower surfaces LE→TE ----------
idx_LE = np.argmin(x)
x_up, y_up = x[idx_LE::-1], y[idx_LE::-1]          # upper surface LE→TE
x_lo, y_lo = x[idx_LE:],  y[idx_LE:]               # lower surface LE→TE

# ---------- Smooth tanh transition only up to x_lin ----------
x_lin = 0.4        # transition chord length
k = 3.0            # steepness of tanh
f_base = 0.03      # base thickness scale

def tanh_leading_edge(x_s, x_lin=0.4, k=3):
    """
    Map x=0 → tanh=-1 (multiplier=1)
    and x=x_lin → tanh=+1 (multiplier=3)
    """
    xi = 2*(x_s/x_lin) - 1  # maps [0, x_lin] → [-1, +1]
    return 1 + (3-1)*0.5*(1 + np.tanh(k * xi))

def full_transition(x_s, x_lin=0.4, k=3):
    """
    For x <= x_lin: tanh transition from 1→3
    For x > x_lin: constant = 3
    """
    return np.where(x_s <= x_lin, tanh_leading_edge(x_s, x_lin, k), 3.0)

# Offsets for upper & lower surfaces
f_up = f_base * full_transition(x_up, x_lin, k)
f_lo = f_base * full_transition(x_lo, x_lin, k)

# ---------- Compute outward normals ----------
def normals(x_s, y_s):
    dx, dy = np.gradient(x_s), np.gradient(y_s)
    n = np.hypot(dx, dy)
    return -dy/n, dx/n

nx_up, ny_up = normals(x_up, y_up)
nx_lo, ny_lo = normals(x_lo, y_lo)

# Outward orientation correction
nx_up[ny_up < 0], ny_up[ny_up < 0] = -nx_up[ny_up < 0], -ny_up[ny_up < 0]
nx_lo[ny_lo > 0], ny_lo[ny_lo > 0] = -nx_lo[ny_lo > 0], -ny_lo[ny_lo > 0]

# ---------- Shifted contours ----------
x_up_s = x_up + f_up * nx_up
y_up_s = y_up + f_up * ny_up
x_lo_s = x_lo + f_lo * nx_lo
y_lo_s = y_lo + f_lo * ny_lo

# ---------- LE projected cap point ----------
# This is just straight forward in -x direction by base offset *1
x_proj_LE = -f_base  # move forward along x-axis
y_proj_LE = 0.0

# Prepend this cap point to the shifted curves
x_up_s_closed = np.insert(x_up_s, 0, x_proj_LE)
y_up_s_closed = np.insert(y_up_s, 0, y_proj_LE)
x_lo_s_closed = np.insert(x_lo_s, 0, x_proj_LE)
y_lo_s_closed = np.insert(y_lo_s, 0, y_proj_LE)

# ---------- Prepare a smooth chord for plotting tanh multiplier ----------
x_chord = np.linspace(0, 1.0, 200)
multiplier = full_transition(x_chord, x_lin, k)

# ---------- Plot with vertical alignment ----------
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# --- Top: Multiplier vs. chord ---
axes[0].plot(x_chord, multiplier, '-',color="crimson", linewidth=2, label="Spacing function")
axes[0].grid(True, linestyle=':')
axes[0].set_ylabel("Horizontal spacing multiplier")
axes[0].axvline(x_lin, color='grey', linestyle='--', label='Transition 40% c')
axes[0].legend(
    facecolor='white', framealpha=1.0, edgecolor='black', loc='upper left'
)
axes[0].tick_params(axis='both', which='both', direction='in', length=4)

# --- Bottom: Profile with shifted contours ---
axes[1].axis('equal')
axes[1].plot(x, y, 'k-', label='Profile')
axes[1].set_ylabel("y coordinate (-)")
axes[1].plot(x_up_s_closed, y_up_s_closed, 'r-', label='Upper spacing function')
axes[1].plot(x_lo_s_closed, y_lo_s_closed, 'b-', label='Lower spacing function')

# Grey connectors every N points
N = 1
for i in range(0, len(x_up), N):
    axes[1].plot([x_up[i], x_up_s[i]], [y_up[i], y_up_s[i]], color='dimgrey', alpha=0.6, linewidth=0.5)
for i in range(0, len(x_lo), N):
    axes[1].plot([x_lo[i], x_lo_s[i]], [y_lo[i], y_lo_s[i]], color='dimgrey', alpha=0.6, linewidth=0.5)

# Mark the projected LE point
# axes[1].plot(x_proj_LE, y_proj_LE, 'go', markersize=6, label='Projected LE')
axes[1].axvline(x_lin, color='grey', linestyle='--', label='Transition 40% c')

axes[1].grid(True, linestyle=':')
axes[1].legend(
    facecolor='white', framealpha=1.0, edgecolor='black', loc='upper left'
)
axes[1].set_xlabel("x/c (Chord)")
axes[1].tick_params(axis='both', which='both', direction='in', length=4)

plt.tight_layout()
plt.show()
plt.tight_layout()
fig.savefig("shifted_profile.png", dpi=300, bbox_inches="tight")
plt.show()