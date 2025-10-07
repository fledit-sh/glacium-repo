# Task stubs

## Multishot convergence annotations

* Identify the solver convergence job – `CONVERGENCE_STATS` delegates to
  :class:`glacium.jobs.analysis_jobs.ConvergenceStatsJob`, which in turn uses the
  utilities from :mod:`glacium.utils.convergence`.
* Reuse `glacium.utils.convergence.last_n_labeled_stats` to extract the mean and
  variance of the last 15 entries from both `converg.fensap.XXXXXX` and
  `converg.drop.XXXXXX` histories.
* When populating the multishot dataset, probe the possible locations for these
  histories: the analysed shot directory, any nested `run_MULTISHOT` folder, and
  the top-level `run_MULTISHOT` solver directory.
* Attach the computed statistics as JSON-serialised attributes on each shot
  group inside the HDF5 dataset so downstream tooling can access the values
  without re-reading the raw convergence files.
