# Glacium

Glacium is a lightweight command line tool to manage small
simulation workflows. Projects are created inside the `runs/`
directory of the current working directory and consist of a global configuration, a set of jobs and
rendered templates.  The focus lies on easily defining new recipes and
executing jobs in dependency order.

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

### Pipeline

Run a grid convergence study and spawn follow-up projects::

   glacium pipeline --level 1 --level 2 --multishot "[10,300,300]"

The call executes the ``grid-convergence`` pipeline layout which
creates one project per grid level using the ``grid_dep`` recipe,
selects the mesh with the lowest drag and then generates and runs a
single-shot project and optional MULTISHOT case with the chosen grid.
Multishot projects use the ``multishot`` recipe. Use ``--layout`` to select
another workflow and ``--pdf`` to merge all report PDFs into a single
summary file.

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
commands.

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

