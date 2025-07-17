import numpy as np
import matplotlib.pyplot as plt

# ---------- Load profile ----------
x, y = np.loadtxt("/mnt/data/AH63K127.dat", skiprows=1).T

# ---------- Split upper & lower surfaces LE→TE ----------
idx_LE = np.argmin(x)
x_up, y_up = x[idx_LE::-1], y[idx_LE::-1]          # upper
x_lo, y_lo = x[idx_LE:],  y[idx_LE:]               # lower

# ---------- Piece‑wise linear‑constant function ----------
f_max = 0.03
x_lin = 0.4
f_up = np.where(x_up <= x_lin, f_max * x_up / x_lin, f_max)
f_lo = np.where(x_lo <= x_lin, f_max * x_lo / x_lin, f_max)

# ---------- Normals ----------
def normals(x_s, y_s):
    dx, dy = np.gradient(x_s), np.gradient(y_s)
    n = np.hypot(dx, dy)
    return -dy/n, dx/n

nx_up, ny_up = normals(x_up, y_up)
nx_lo, ny_lo = normals(x_lo, y_lo)

# Outward orientation
nx_up[ny_up < 0],  ny_up[ny_up < 0]  = -nx_up[ny_up < 0],  -ny_up[ny_up < 0]
nx_lo[ny_lo > 0],  ny_lo[ny_lo > 0]  = -nx_lo[ny_lo > 0],  -ny_lo[ny_lo > 0]

# ---------- Shifted contours ----------
x_up_s = x_up + f_up*nx_up;   y_up_s = y_up + f_up*ny_up
x_lo_s = x_lo + f_lo*nx_lo;   y_lo_s = y_lo + f_lo*ny_lo

# ---------- Plot ----------
plt.figure(figsize=(10,4))
plt.axis('equal')

# original profile
plt.plot(x, y, 'k-', label='Profil')

# shifted contours
plt.plot(x_up_s, y_up_s, 'r-', label='Oberseite')
plt.plot(x_lo_s, y_lo_s, 'b-', label='Unterseite')

# grey connectors every N points for clarity
N = 3
for i in range(0, len(x_up), N):
    plt.plot([x_up[i], x_up_s[i]], [y_up[i], y_up_s[i]], color='grey', alpha=0.3, linewidth=0.5)
for i in range(0, len(x_lo), N):
    plt.plot([x_lo[i], x_lo_s[i]], [y_lo[i], y_lo_s[i]], color='grey', alpha=0.3, linewidth=0.5)

plt.legend()
plt.title("Funktion (linear bis 40 % c, dann konstant) + Normal‑Verbindungen")
plt.show()
