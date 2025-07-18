from glacium.pipeline import Run, Pipeline

# Base run shared by all cases
base = (
    Run()
    .select_airfoil("NACA0012")
    .set_bulk({"CHORD_LENGTH": 0.5, "Re": 2e6})
    .add_job("prep")
    .add_job("solver")
)

# Generate four runs sweeping angle of attack
pipe = Pipeline().repeat(base, "CASE_AOA", [-4, 0, 4, 8])

# Extra run using the multishot recipe
multi = (
    base.clone()
    .clear_jobs()
    .add_job("multishot")
    .set("CASE_MULTISHOT", [10, 300, 300])
    .tag("multishot")
)
pipe.add(multi)

# Preview and optionally execute the pipeline
print(pipe.preview())
# pipe.execute(dry_run=False)
