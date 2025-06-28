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

### Manage individual jobs

```bash
# reset a job to PENDING
glacium job reset XFOIL_POLAR
```

### Sync projects with recipes

```bash
# refresh the job list of the current project
glacium sync
```

### Remove projects

```bash
# delete the selected project
glacium remove
```

Use `--all` to remove every project under `./runs`.

## Development

All tests can be run with:

```bash
pytest
```


