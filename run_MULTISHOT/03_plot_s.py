import re, os, math, sys
import numpy as np
import matplotlib.pyplot as plt


# PDF export removed; exporting per-variable PNGs

def parse_variables(header_line: str):
    vars_ = re.findall(r'"([^"]+)"', header_line)
    return vars_ if vars_ else []


def read_tecplot_point_file(path: str):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.read().strip().splitlines()

    var_names = []
    for ln in lines:
        if ln.strip().upper().startswith("VARIABLES"):
            var_names = parse_variables(ln)
            break

    rows, max_cols = [], 0
    for ln in lines:
        nums = re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", ln.replace(",", " "))
        if len(nums) >= 3:
            vals = []
            for x in nums:
                if x.lower() == "nan":
                    vals.append(float("nan"))
                else:
                    try:
                        vals.append(float(x))
                    except Exception:
                        vals.append(float("nan"))
            rows.append(vals)
            max_cols = max(max_cols, len(vals))

    if not rows or max_cols < 3:
        raise RuntimeError("No numeric rows found.")

    arr = np.full((len(rows), max_cols), np.nan, dtype=float)
    for i, r in enumerate(rows):
        arr[i, :len(r)] = r

    if not var_names or len(var_names) != max_cols:
        var_names = [f"col{i}" for i in range(max_cols)]
        var_names[:3] = ["X", "Y", "Z"]
    return var_names, arr


def extract_curve_2d(arr, z_tol=1e-12):
    mask = np.isfinite(arr[:, 2]) & (np.abs(arr[:, 2]) < z_tol)
    return arr[mask, :]


def ensure_closed(curve, tol=1e-12):
    if curve.shape[0] == 0:
        return curve
    if np.linalg.norm(curve[0, :2] - curve[-1, :2]) > tol:
        curve = np.vstack([curve, curve[0]])
    return curve


def cut_at_max_x(curve):
    i = int(np.nanargmax(curve[:, 0]))
    return np.vstack([curve[i:], curve[:i]]), i


def cumulative_arclength(xy):
    diffs = np.diff(xy, axis=0)
    seg = np.sqrt((diffs ** 2).sum(axis=1))
    s = np.concatenate([[0.0], np.cumsum(seg)])
    return s


def first_crossing_s(xy, s, tol=0.0):
    y = xy[:, 1]
    # If any node lands on y=0, take its s directly
    for k in range(len(y)):
        if abs(y[k]) <= tol:
            return float(s[k])
    for k in range(1, len(y)):
        y0, y1 = y[k - 1], y[k]
        if (y0 < 0 and y1 > 0) or (y0 > 0 and y1 < 0):
            # Linear interpolation in s
            t = -y0 / (y1 - y0)
            return float(s[k - 1] + t * (s[k] - s[k - 1]))
    return None


def scale_by_divider(s, s_cross):
    """Piecewise map s to [-1,0] on [s_min,s_cross] and [0,1] on [s_cross,s_max]."""
    smin, smax = float(np.min(s)), float(np.max(s))
    out = np.empty_like(s, dtype=float)
    # Left half
    left_den = (s_cross - smin) if (s_cross - smin) != 0 else 1.0
    # Right half
    right_den = (smax - s_cross) if (smax - s_cross) != 0 else 1.0
    for i, si in enumerate(s):
        if si <= s_cross:
            out[i] = -1.0 + (si - smin) / left_den
        else:
            out[i] = 0.0 + (si - s_cross) / right_den
    # Clip for numerical safety
    out = np.clip(out, -1.0, 1.0)
    return out


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python 03_plot_s.py <input_file> <output_path> [z_tol]\n  - <output_path> may be a PDF-like path; script will derive folder & stem for PNGs.")
        sys.exit(1)
    in_file = sys.argv[1]
    out_pdf = sys.argv[2]

    z_tol = float(sys.argv[3]) if len(sys.argv) > 3 else 1e-12

    var_names, arr = read_tecplot_point_file(in_file)
    curve = extract_curve_2d(arr, z_tol=z_tol)
    if curve.shape[0] < 3:
        print("Not enough points detected on Z≈0 curve.")
        sys.exit(2)

    # Ensure closed, cut at max X, ensure closed again after rotation
    curve = ensure_closed(curve)
    cut_curve, idx = cut_at_max_x(curve)
    cut_curve = ensure_closed(cut_curve)

    # Arc length and h (using unscaled s)
    s = cumulative_arclength(cut_curve[:, :2])
    n_nodes = cut_curve.shape[0] - 1 if np.allclose(cut_curve[0, :2], cut_curve[-1, :2]) else cut_curve.shape[0]
    s_total = float(s[-1])
    h_val = s_total / n_nodes if n_nodes > 0 else float("nan")

    # Find first Y=0 crossing in original s
    s_cross = first_crossing_s(cut_curve[:, :2], s, tol=0.0)

    if s_cross is None:
        # Fallback: simple linear scaling to [-1,1] if no crossing found
        smin, smax = float(np.nanmin(s)), float(np.nanmax(s))
        if not np.isfinite(smin) or not np.isfinite(smax) or smax == smin:
            # Degenerate case: use indices to create a uniform mapping
            s_scaled = np.linspace(-1.0, 1.0, num=len(s))
        else:
            s_scaled = 2.0 * (s - smin) / (smax - smin) - 1.0
        divider_at = None
    else:
        s_scaled = scale_by_divider(s, s_cross)
        divider_at = 0.0  # by design
    # Clip strictly to [-1, 1] for numerical safety
    s_scaled = np.clip(s_scaled, -1.0, 1.0)

    # Determine which columns to plot (beyond X,Y,Z) with some variability
    cols_to_plot = []
    for j in range(3, cut_curve.shape[1]):
        col = cut_curve[:, j]
        finite = np.isfinite(col)
        if finite.sum() >= 2:
            vmin = np.nanmin(col[finite])
            vmax = np.nanmax(col[finite])
            if math.isfinite(vmin) and math.isfinite(vmax) and abs(vmax - vmin) > 0:
                cols_to_plot.append(j)

    # Plot each variable vs scaled s


# Derive output directory and stem from out_pdf path
out_pdf_path = Path(out_pdf)
out_dir = out_pdf_path.parent
out_dir.mkdir(parents=True, exist_ok=True)
stem = out_pdf_path.stem if out_pdf_path.stem else "curve_s"


# Helper to sanitize variable names for filenames
def _safe_name(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9_\-]+', '_', name.strip())[:80] or "var"


# Plot each variable vs scaled s as individual PNGs
for j in cols_to_plot:
    y = cut_curve[:, j]
    name = var_names[j] if j < len(var_names) else f"col{j}"
    # Mask non-finite pairs
    mask = np.isfinite(s_scaled) & np.isfinite(y)
    if mask.sum() < 2:
        continue
    ss = s_scaled[mask]
    yy = y[mask]

    plt.figure()
    plt.plot(ss, yy, label=f"{name}   h={h_val:.6g}")
    if divider_at is not None:
        plt.axvline(divider_at, linestyle="--", label="Y=0 crossing")
    plt.xlim(-1.0, 1.0)
    plt.xlabel("Piecewise-scaled arc length s ∈ [-1, 1] (divider at 0)")
    plt.ylabel(name)
    plt.title(f"{name} vs scaled s (cut @ max X)")
    plt.legend()

    out_png = out_dir / f"{stem}_{_safe_name(name)}.png"
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()

    # Save CSV including s, s_scaled, and all original columns
    out_csv = os.path.splitext(out_pdf)[0] + "_curve.csv"
    header = "s,s_scaled," + ",".join(var_names)
    data_to_save = np.column_stack([s, s_scaled, cut_curve])
    np.savetxt(out_csv, data_to_save, delimiter=",", header=header, comments="")

    # Write a summary
    out_txt = os.path.splitext(out_pdf)[0] + "_summary.txt"
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(f"Points (unique): {n_nodes}\n")
        f.write(f"s_total: {s_total}\n")
        f.write(f"h: {h_val}\n")
        f.write(f"Cut index (argmax X in original Z\\approx 0 subset): {idx}\n")
        f.write(f"First Y=0 crossing at s (unscaled): {s_cross}\n")

    print(f"Saved: {out_pdf}")
    print(f"Saved: {out_csv}")
    print(f"Saved: {out_txt}")

if __name__ == "__main__":
    main()
