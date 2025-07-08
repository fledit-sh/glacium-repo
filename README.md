# Glacium

Glacium is a lightweight command line tool to manage small
simulation workflows. Projects are created inside the `runs/`
directory and consist of a global configuration, a set of jobs and
rendered templates.  The focus lies on easily defining new recipes and
executing jobs in dependency order.

## Installation

Install the package with `pip` (Python 3.12 or newer is required):

```bash
pip install .
```

This exposes a `glacium` command via the console script entry point.

## Usage

Below is a quick tour through the most important CLI commands. Each
command provides `--help` for additional options.

### Create a project

```bash
# create a new project from the default recipe
glacium new MyWing
```

The command prints the generated project UID. All projects live below
`./runs/<UID>`.

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

Use `--all` to remove every project under `./runs`.

### Sweep grid refinement

```bash
# create 3 projects doubling PWS_REFINEMENT starting from 8
glacium sweep 8 -n 3 -f 2
```

### External executables

Paths to third party programs can be configured in
`runs/<UID>/_cfg/global_config.yaml`.  Important keys include
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

