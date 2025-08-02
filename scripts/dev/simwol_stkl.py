import re, numpy as np, pandas as pd, matplotlib.pyplot as plt
from scipy.spatial import cKDTree
from matplotlib.backends.backend_pdf import PdfPages
import scienceplots
plt.style.use(['science', 'no-latex'])

# ──────────────── file paths ────────────────
DAT_FILE = "swimsol.ice.000020.dat"
STL_FILE = "ice.ice.000020.stl"
CSV_Z0  = "000020.csv"
PDF_Z0  = "000020.pdf"

# ─────────── helper functions ───────────
def _fix_fortran(tok: str) -> float:
    """
    Convert numbers missing the 'E' in Fortran sci-notation → float.
    Example: '-1.23-04' → -1.23E-04
    """
    if ('E' in tok) or ('e' in tok):
        return float(tok)
    m = re.match(r'([+-]?[0-9.]+)([+-][0-9]{2,4})', tok)
    return float(f"{m.group(1)}E{m.group(2)}") if m else float(tok)

def read_zone_by_title(dat_path: str, target_title: str = "WALL_2001"):
    """
    Return (variable names, numpy array) for the Tecplot ZONE whose
    header contains T="<target_title>".
    """
    with open(dat_path, 'r') as f:
        f.readline()                       # skip TITLE line
        var_line = f.readline()
        var_names = re.findall(r'"([^"]+)"', var_line)

        # locate the desired ZONE header
        for line in f:
            if line.startswith('ZONE') and f'T="{target_title}"' in line:
                N = int(re.search(r'N\s*=\s*(\d+)', line).group(1))
                break
        else:
            raise ValueError(f'ZONE with T="{target_title}" not found in {dat_path}')

        # read the node block for the located zone
        rows = []
        for _ in range(N):
            tokens = f.readline().strip().split()
            rows.append([_fix_fortran(tok) for tok in tokens])

    return var_names, np.asarray(rows)


def build_nn_path_s(stl_path: str):
    """Return STL vertices ordered by a nearest-neighbour path and cumulative arc length s."""
    verts = []
    with open(stl_path, 'r') as f:
        for line in f:
            if line.strip().startswith("vertex"):
                _, x, y, z = line.split()
                verts.append((float(x), float(y), float(z)))
    pts = np.unique(np.round(np.array(verts), 6), axis=0)

    N = len(pts)
    visited = np.zeros(N, bool)
    order = []
    idx = np.argmax(pts[:, 0])             # start at max X
    for _ in range(N):
        order.append(idx)
        visited[idx] = True
        if visited.all(): break
        remaining = np.where(~visited)[0]
        dists = np.linalg.norm(pts[remaining] - pts[idx], axis=1)
        idx = remaining[np.argmin(dists)]

    path   = pts[order]
    seglen = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s_vals = np.insert(np.cumsum(seglen), 0, 0.0)
    return path, s_vals


# ──────────── main processing ────────────
var_names, data_all = read_zone_by_title(DAT_FILE, target_title="WALL_2001")
path_pts, s_path    = build_nn_path_s(STL_FILE)

tree           = cKDTree(path_pts)
_, idx_nearest = tree.query(data_all[:, :3], k=1)
s_all          = s_path[idx_nearest]

mask_z0   = np.abs(data_all[:, 2]) < 1e-8
data      = data_all[mask_z0]
s_dat     = s_all[mask_z0]

df = pd.DataFrame(data, columns=var_names)
df.insert(0, "s [m]", s_dat)
df.to_csv(CSV_Z0, index=False)

order = np.argsort(s_dat)
with PdfPages(PDF_Z0) as pdf:
    for name in var_names:
        y = df[name].values
        plt.figure(figsize=(8, 5))
        plt.plot(s_dat[order], y[order])
        plt.xlabel("s [m]")
        plt.ylabel(name)
        plt.xlim(0.1, 0.3)
        plt.title(f"{name} vs s (Z ≈ 0)")
        plt.tight_layout()
        pdf.savefig()
        plt.close()

print(f"Filtered CSV saved: {CSV_Z0}")
print(f"Filtered plots PDF saved: {PDF_Z0}")
