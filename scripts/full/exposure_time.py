import numpy as np
import matplotlib.pyplot as plt
import scienceplots

plt.style.use(['science', 'no-latex'])

# Constants
NM_TO_M = 1852  # meters per nautical mile
s_cont_m = 17.4 * NM_TO_M   # Continuous maximum, meters
s_int_m  = 2.6 * NM_TO_M    # Intermittent maximum, meters

# Speed range for curves (m/s)
V = np.linspace(10, 70, 400)

# Exposure time (minutes)
t_cont = (s_cont_m / V) / 60.0
t_int  = (s_int_m  / V) / 60.0

# Plot
plt.figure(figsize=(8, 5))
plt.plot(V, t_cont, label='Continuous Max 17.4 NM')
plt.plot(V, t_int, label='Intermittent Max 2.6 NM')

# Highlight the two requested speeds
for v in [20, 50]:
    plt.scatter(v, (s_cont_m / v) / 60.0, marker='o')
    plt.scatter(v, (s_int_m  / v) / 60.0, marker='s')

plt.xlabel('Horizontal Flight Speed V [m s⁻¹]')
plt.ylabel('Exposure Time t [min]')
plt.title('Exposure Time versus Horizontal Speed\n(Appendix C Standard Extents)')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
