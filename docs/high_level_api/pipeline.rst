Pipeline
========

A :class:`glacium.pipeline.Pipeline` is an ordered collection of
:class:`~glacium.pipeline.Run` objects.  It supports adding and removing
runs, generating Cartesian sweeps, filtering by tags and executing all
cases respecting dependency order.  ``Pipeline.execute`` collects a
:class:`~glacium.pipeline.RunResult` for each run.

Helper functions
----------------

``sweep(base, param, values, tag_format="{param}={value}")``
    Convenience wrapper around ``Pipeline().repeat`` that returns a list of runs.

``grid(airfoils=None, common=None, jobs=None, **param_axes)``
    Stand-alone variant of ``param_grid`` returning a new pipeline.

``load(path)``
    Shorthand for :meth:`Pipeline.load_layout`.

``run(layout, **execute_kwargs)``
    One-liner helper: load a layout file, preview it and execute.

Minimal example
---------------

The snippet below (taken from ``tasks.md`` lines 110–125) sweeps the
angle of attack over a single airfoil::

```python
from glacium.pipeline import Run, Pipeline

# AoA sweep around a single airfoil
template = (
    Run()
    .select_airfoil("NACA0012")
    .set_bulk({"CHORD_LENGTH": 0.45, "Re": 1.5e6})
    .jobs(["XFOIL_ANALYSIS"])
)

pipe = Pipeline().repeat(template, "AoA", [-2, 0, 2, 4, 6])
pipe.preview()
results = pipe.execute(concurrency=3)
pipe.save_layout("aoa_sweep.yaml")
```