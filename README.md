# Glacium

Glacium is a lightweight command line tool to manage small
simulation workflows. Projects are created inside the `runs/`
directory of the current working directory and consist of a global configuration, a set of jobs and
rendered templates.  The focus lies on easily defining new recipes and
executing jobs in dependency order. Programmatic control is available
through a small API; see [docs/high_level_api/intro.rst](docs/high_level_api/intro.rst)
for an overview. A short demonstration is available in
`scripts/example_run.py`.

[![Publish to PyPI](https://github.com/fledit-sh/glacium-repo/actions/workflows/publish.yml/badge.svg?branch=dev)](https://github.com/fledit-sh/glacium-repo/actions/workflows/publish.yml)

## Installation

Install the package with `pip` (Python 3.12 or newer is required):

```bash
pip install .
```

**Warning**: make sure the old `pyfpdf` package is **not** installed alongside
`fpdf2`. The two libraries conflict and can lead to runtime errors. If you see a
warning about PyFPDF, run:

```bash
pip uninstall --yes pyfpdf
```

This exposes a `glacium` command via the console script entry point.

The DejaVuSans.ttf font used for PDF reports ships with the package.

## Usage

Below is a quick tour through the most important CLI commands. Each
command provides `--help` for additional options.

### Create a project

```bash
# create a new project from the default recipe
glacium new MyWing
```

The multishot recipe runs ten solver cycles by default. Override the count with
``--multishots``:

```bash
glacium new MyWing --multishots 5
```

The command prints the generated project UID. All projects live below
`./runs/<UID>` in the current working directory. ``glacium new`` and ``glacium init`` parse ``case.yaml`` and write ``global_config.yaml`` automatically.
When running multishot jobs the template files for each shot are generated
automatically. After editing ``case.yaml`` you can run ``glacium update`` to
regenerate the configuration.  Set ``CASE_MULTISHOT`` in ``case.yaml`` to a list
of icing times for each shot.

### Case sweep

```bash
glacium case-sweep --param CASE_AOA=0,4 --param CASE_VELOCITY=50,100
```

Use ``--multishots`` to change the number of solver cycles per project
(defaults to ``10``):

```bash
glacium case-sweep --param CASE_AOA=0,4 --multishots 20
```

One project is created for each parameter combination and
``global_config.yaml`` is generated from the project's ``case.yaml``.
The command prints the generated UIDs.

### List projects

```bash
glacium projects
```

### Select a project

```bash
# select by number from `glacium projects`
glacium select 1
```

The selected UID is stored in `~/.glacium_current` and used by other
commands. Projects can also be reopened programmatically with
``Run.load(uid)`` from the API. A minimal end-to-end example looks like::

   from glacium.api import Project

   uid = Project("runs").create().uid
   proj = Project.load("runs", uid)
   proj.add_job("POINTWISE_MESH2")
   proj.run()

### Run jobs

```bash
# run all pending jobs in the current project
glacium run
```

You can run specific jobs by name as well:

```bash
glacium run XFOIL_REFINE XFOIL_POLAR
```

### Show job status

```bash
glacium list
```
The table now includes an index column so you can refer to jobs by number.

### Manage individual jobs

```bash
# reset a job to PENDING
glacium job reset XFOIL_POLAR
glacium job reset 1  # via index
```
You can list all available job types with numbers:

```bash
glacium job --list
```

Select a job of the current project by its index:

```bash
glacium job select 1
```

Jobs can also be added or removed via their index:

```bash
glacium job add 1
glacium job remove 1
```

### Sync projects with recipes

```bash
# refresh the job list of the current project
glacium sync
```

### Update configuration

```bash
# rebuild global_config.yaml from case.yaml
glacium update
```

### Display project info

```bash
glacium info
```
Print the ``case.yaml`` parameters and a few values from
``global_config.yaml`` for the current project.

### Remove projects

```bash
# delete the selected project
glacium remove
```

Use `--all` to remove every project under `runs` in the current working directory.

### External executables

Paths to third party programs can be configured in
`runs/<UID>/_cfg/global_config.yaml` inside the current working directory.  Important keys include
`POINTWISE_BIN`, `FENSAP_BIN` and the newly added
`FLUENT2FENSAP_EXE` pointing to ``fluent2fensap.exe`` on Windows.

### Logging

Set ``GLACIUM_LOG_LEVEL`` to control the verbosity of the CLI. For example::

   export GLACIUM_LOG_LEVEL=DEBUG
## Project structure

When simulating, the projects render different files. After the simulation the results are being generated. After postprocessing the runs should contain the following files:
(the runs are listed explicitely)
```bash
20250716-111657-523721-3DA5/
├── _cfg/
├── _data/
├── _tmpl/
├── analysis/
├── mesh/
├── pointwise/
├── run_DROP3D/
├── run_FENSAP/
├── run_ICE3D/
├── run_MULTISHOT/
├── runs/
├── xfoil/
├── case.yaml
└── manifest.json

run_FENSAP/
├── .solvercmd
├── .solvercmd.out
├── converg
├── fensap.par
├── fensapstop.txt
├── files
├── gmres.out
├── hflux.dat
├── mesh.grid
├── out
├── soln
├── soln.dat
└── surface.dat

run_DROP3D/
├── .solvercmd
├── .solvercmd.out
├── converg
├── drop3d.par
├── droplet
├── droplet.dat
├── droplet.drop.dat
├── fensapstop.txt
├── files
├── gmres.out
├── mesh.grid
└── out

run_ICE3D/
├── .restart
├── .solvercmd
├── .solvercmd.out
├── cadImportXXXX.XXXX.log
├── custom_remeshing.sh
├── fluent-XXXX-XXXX-XXXX.trn
├── fluent_config.jou
├── fluentMeshing.log.grid
├── gmres.out
├── ice.grid
├── ice.par
├── ice.stl
├── ice.tin
├── ice3dstop.txt
├── iceconv.dat
├── map.grid
├── mesh.grid
├── meshingSizes.scm
├── newmesh.stl
├── remeshing.jou
├── roughness.dat
├── swim.log
├── swimsol
├── swimsol.ice.dat
└── timebc.dat
run_MULTISHOT/
├── .solvercmd
├── .solvercmd.out
├── cadImport1752767228.502887.log
├── cfdpost.fsp
├── cfdpost.ice.fsp
├── config.drop.000001
├── config.fensap.000001
├── config.par
├── config.par.000001
├── converg.drop.000001
├── converg.fensap.000001
├── create-2.5D-mesh.bin
├── custom_remeshing.sh
├── drop.par
├── droplet
├── droplet.drop.000001
├── droplet.drop.000001.disp
├── fensap.par
├── fensapstop.drop.000001
├── fensapstop.txt.fensap.000001
├── files
├── files.drop.000001
├── files.fensap.000001
├── fluent_config.jou
├── fluent-20250717-174659-776.trn
├── fluentMeshing.log.000001
├── gmres.out
├── gmres.out.drop.000001
├── grid.disp
├── grid.ice.000001
├── grid.ice.000002
├── hflux.dat.fensap.000001
├── ice.grid
├── ice.grid.ice.000001
├── ice.grid.ice.000001.3dtmp
├── ice.ice00001.stl
├── ice.ice00001.tin
├── ice.par
├── ice.view
├── ice3dstop.txt.ice.000001
├── iceconv.dat.ice.000001
├── lastrwap.msh.h5
├── lastrwap-remeshed.msh
├── lastrwap-remeshed.sf
├── map.grid.ice.000001
├── map.grid.ice.000001.3dtmp
├── meshingSizes.scm
├── newmesh.cas
├── newmesh.stl
├── out.drop.000001
├── out.fensap.000001
├── out.remesh.griddisp.000001
├── remeshing.jou
├── remeshing.wft
├── roughness.dat
├── roughness.dat.ice.000001
└── roughness.dat.ice.000001.disp
├── roughness.dat.map
├── shell.cas
├── soln
├── soln.fensap.000001
├── soln.fensap.000001.disp
├── surface.dat.fensap.000001
├── swim.log.ice.000001
├── swimsol
├── swimsol.ice.000001
├── timebc.dat.drop.000001
└── timebc.dat.ice.000001
```

## Grid dependency study

Create mesh refinement projects and analyse convergence using:

```bash
python scripts/full_power_creation.py
python scripts/full_power_gci.py
```

### Clean sweep

Run an angle-of-attack sweep on the recommended grid and plot the results:

```bash
python scripts/clean_sweep_creation.py
python scripts/clean_sweep_analysis.py
```
The analysis stores plots and ``polar_momentum.csv`` under
``aoa_sweep_results``.

### Iced sweep

Run an angle-of-attack sweep using the iced grid from the multishot project:

```bash
python scripts/iced_sweep_creation.py
python scripts/iced_sweep_analysis.py
```
The analysis stores plots and ``polar_momentum.csv`` under
``aoa_sweep_results_iced``.

The `scripts/full_power.py` helper runs both studies consecutively.

## Development

All tests can be run with:

```bash
pytest
```

To enable automatic version management install the plugin once:

```bash
poetry self add "poetry-dynamic-versioning[plugin]"
```

`poetry install` will pull `setuptools_scm` as specified in `pyproject.toml`.
Versions are taken from Git tags, e.g.:

```bash
git tag v1.2.0 -m "release"
```

