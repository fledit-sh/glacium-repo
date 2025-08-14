import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 500)
y = np.sin(x)

fig = plt.figure(figsize=(8, 6))

# Absolute axes position in figure fraction coordinates
ax = fig.add_axes([0.2, 0.2, 0.6, 0.6])
ax.set_xlim(0, 10)
ax.set_ylim(-1.5, 1.5)

# Add intentionally large labels and titles
ax.set_title("This is a REALLY LONG TITLE that might overlap", fontsize=14)
ax.set_xlabel("X-axis with absurdly long text to test layout independence", fontsize=12)
ax.set_ylabel("Y-axis with absurdly long text to test layout independence", fontsize=12)

ax.plot(x, y)

plt.show()
