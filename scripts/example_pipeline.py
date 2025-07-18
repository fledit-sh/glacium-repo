"""
generate_single_project.py
--------------------------
• three profiles, each bound to ONE chord length
• temps = [‑15, ‑2]
• lwcs  = [0.2, 0.5]

The script chooses the FIRST tuple in the product of
(profile, temp, lwc) and produces all 38 runs for that
single project, wiring the dependencies exactly as before.

You will then prune the YAML manually to keep only the
cases you really want to run.
"""

from pathlib import Path
from itertools import product
import yaml

from glacium.api.run import Run

# ----- fixed study dimensions -------------------------------------------- #
PROFILE_CHORDS = {                    # Profile  : single chord [m]
    "NACA0010": 0.30,
    "NACA2412": 0.40,
    "S809":     0.50,
}
TEMPS  = [-15, -2]                    # °C
LWCS   = [0.2, 0.5]                   # g/m³

AOA_SWEEP   = list(range(-4, 22, 2))
GRID_LEVELS = range(1, 9)
MULTI_SHOTS = [10, 15, 30]

# ----- job strings used in your repo ------------------------------------ #
JOB_SOLVE            = "SOLVE"
JOB_POST             = "POSTPROCESS"
JOB_ANALYZE          = "ANALYZE"
JOB_SELECT_GRID      = "SELECT_OPTIMAL_GRID"
JOB_EXTRACT_GRID     = "EXTRACT_REFINED_GRID"
JOB_SINGLESHOT_SOLVE = "SOLVE_SINGLESHOT"
JOB_MULTISHOT_SOLVE  = "SOLVE_MULTISHOT"

OUT = Path("pipelines"); OUT.mkdir(exist_ok=True)

# ----- helper to build the 38‑run pipeline ------------------------------ #
def build_pipeline(profile, chord, temp, lwc):
    tag_project = f"{profile}_T{temp:+d}_LWC{lwc:.1f}"
    pipe = Pipeline()

    # Grid study
    grid_runs = []
    for lvl in GRID_LEVELS:
        r = (Run()
             .select_airfoil(profile)
             .set_bulk({"TEMPERATURE": temp, "CHORD": chord,
                        "LWC": lwc, "GRID_LEVEL": lvl})
             .jobs([JOB_SOLVE, JOB_POST])
             .tag("grid-study").tag(tag_project))
        pipe.add(r); grid_runs.append(r)

    select_grid = (Run()
                   .select_airfoil(profile)
                   .set("ACTION", "SELECT").add_job(JOB_SELECT_GRID)
                   .tag("grid-select").tag(tag_project))
    for r in grid_runs: select_grid.depends_on(r)
    pipe.add(select_grid)

    # Base‑grid AOA sweep
    for aoa in AOA_SWEEP:
        pipe.add(
            Run().select_airfoil(profile)
                .set_bulk({"TEMPERATURE": temp, "CHORD": chord,
                           "LWC": lwc, "AoA": aoa, "GRID": "optimal"})
                .jobs([JOB_SOLVE, JOB_POST, JOB_ANALYZE])
                .tag("aoa-base").tag(tag_project)
                .depends_on(select_grid)
        )

    # Single‑shot
    pipe.add(
        Run().select_airfoil(profile)
            .set_bulk({"TEMPERATURE": temp, "CHORD": chord,
                       "LWC": lwc, "SHOT_MODE": "single"})
            .add_job(JOB_SINGLESHOT_SOLVE)
            .tag("single-shot").tag(tag_project)
            .depends_on(select_grid)
    )

    # Multishots
    ms_runs = []
    for n in MULTI_SHOTS:
        r = (Run().select_airfoil(profile)
                .set_bulk({"TEMPERATURE": temp, "CHORD": chord,
                           "LWC": lwc, "NSHOT": n})
                .add_job(JOB_MULTISHOT_SOLVE)
                .tag(f"multishot-{n}").tag(tag_project)
                .depends_on(select_grid))
        pipe.add(r); ms_runs.append(r)

    # Extract refined grid from 30‑shot
    extract = (Run()
               .select_airfoil(profile)
               .set("ACTION", "EXTRACT_GRID")
               .add_job(JOB_EXTRACT_GRID)
               .tag("grid-extract").tag(tag_project)
               .depends_on([r for r in ms_runs
                            if r.parameters["NSHOT"] == 30][0]))
    pipe.add(extract)

    # Refined‑grid AOA sweep
    for aoa in AOA_SWEEP:
        pipe.add(
            Run().select_airfoil(profile)
                .set_bulk({"TEMPERATURE": temp, "CHORD": chord,
                           "LWC": lwc, "AoA": aoa, "GRID": "refined"})
                .jobs([JOB_SOLVE, JOB_POST, JOB_ANALYZE])
                .tag("aoa-refined").tag(tag_project)
                .depends_on(extract)
        )
    return pipe


# ----- build a single project ------------------------------------------- #
def main():
    # choose first combo; change indexing if you want another
    # profile, temp, lwc = next(product(PROFILE_CHORDS.keys(), TEMPS, LWCS))
    # chord = PROFILE_CHORDS[profile]
    #
    # proj_pipe = build_pipeline(profile, chord, temp, lwc)
    # fname = OUT / f"{profile}_T{temp:+d}_LWC{lwc:.1f}.yaml"
    # proj_pipe.save_layout(fname)
    #
    # print("Created:", fname)
    # print("Run count:", proj_pipe.size())
    # print(proj_pipe.preview(max_rows=10))
    # print("\nEdit the YAML to keep only the cases you want.")
    run = Run("")
    run.select_airfoil("NACA0008.dat")
    run.set("CASE_ROUGHNESS", 50)
    run.set("CASE_CHARACTERISTIC_LENGTH", 0.431)
    run.set("CASE_VELOCITY", 50)
    run.set("CASE_ALTITUDE", 100)
    run.set("CASE_TEMPERATURE", -2)
    run.set("CASE_AOA", 0)
    run.set("CASE_MVD", 20)
    run.set("CASE_YPLUS", 0.3)
    run.set("PWS_REFINEMENT", 8)
    run.create()


if __name__ == "__main__":
    main()
