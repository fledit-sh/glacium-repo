Quick Start Guide
=================

This tutorial walks you through the minimum steps required to create a
project and execute jobs with **glacium**.  It assumes Python 3.12 or
newer is installed and the command line is available.

Installation
------------

Install the package from the repository root using ``pip``:

.. code-block:: bash

   pip install .

After installation the ``glacium`` command becomes available.

Create a project
----------------

Projects live in the ``runs/`` directory of the current working directory.  The ``new`` command generates a
project from the default recipe and prints its unique identifier (UID):

.. code-block:: bash

   glacium new MyWing

The multishot recipe uses ten solver cycles by default. Override this number
with ``--multishots``:

.. code-block:: bash

   glacium new MyWing --multishots 5

To chain multiple recipes use ``+`` between their names, e.g.:

.. code-block:: bash

   glacium new MyWing -r prep+solver

The project will be created under ``runs/<UID>`` in the current working directory.  During ``glacium new``
and ``glacium init`` the ``case.yaml`` file is parsed and the resulting
``global_config.yaml`` is written automatically.  If you change
``case.yaml`` later you can run ``glacium update`` to rebuild the
configuration. When multishot jobs run, template files for each shot index are
created automatically before launching the solver. ``ICE_GUI_TOTAL_TIME``
defines the icing duration for cycles after the fixed ``10``‑second first shot.
Individual timings are no longer needed unless overriding that initial shot.

Case sweep
~~~~~~~~~~

Create multiple projects for all combinations of parameters:

.. code-block:: bash

   glacium case-sweep --param CASE_AOA=0,4 --param CASE_VELOCITY=50,100 \
       --param PWS_REFINEMENT=1,2

Pass ``--multishots`` to change the number of solver cycles per case. The
default is ``10``:

.. code-block:: bash

   glacium case-sweep --param CASE_AOA=0,4 --multishots 20

The command prints the generated UIDs and writes ``global_config.yaml``
for every new case.  Each configuration is derived from the case's
``case.yaml`` file just like ``glacium new`` and ``glacium init``.
Here ``PWS_REFINEMENT`` selects the Pointwise mesh refinement level for
each generated case.

You can list all projects at any time with:

.. code-block:: bash

   glacium projects

Passing ``--results`` prints additional solver statistics for each project.
Execution time is calculated by summing ``total simulation`` lines in
``.solvercmd.out`` while lift and drag coefficients are averaged from the last
15 entries of ``converg.fensap.*`` files.  The command then shows the mean and
standard deviation of these CL/CD values next to the total runtime.

Select a project
----------------

Operations such as running or resetting jobs operate on the "current"
project.  Select one by its number from ``glacium projects``:

.. code-block:: bash

   glacium select 1

The chosen UID is written to ``~/.glacium_current``.

Run jobs
--------

Each project contains a sequence of jobs defined by its recipe.  Execute
all pending jobs in the correct dependency order with:

.. code-block:: bash

   glacium run

Pass ``--all`` to process every project below ``runs``.  Jobs with the
status ``PENDING`` or ``FAILED`` are executed in dependency order:

.. code-block:: bash

   glacium run --all

You may restrict execution to specific jobs by name or index.  When
using ``--all`` with job names those jobs are first reset to ``PENDING``
on every project.  The ``list`` command shows the current status and
index of each job:

.. code-block:: bash

   glacium list

   glacium run XFOIL_REFINE XFOIL_POLAR

Managing jobs individually
--------------------------

Jobs can be reset to the ``PENDING`` state or removed and added again by
index.  Examples:

.. code-block:: bash

   glacium job reset 1
   glacium job remove 2
   glacium job add 2

Synchronise with recipes
------------------------

If you update a recipe or want to refresh the list of jobs for the
current project run:

.. code-block:: bash

   glacium sync

Remove projects
---------------

Delete the selected project with:

.. code-block:: bash

   glacium remove

Pass ``--all`` to remove every project under ``runs`` in the current working directory.

External executables
--------------------

Paths to third party programs are configured in
``runs/<UID>/_cfg/global_config.yaml`` inside the current working directory.  Important keys include
``POINTWISE_BIN``, ``FENSAP_BIN`` and ``FLUENT2FENSAP_EXE`` which should
point to the corresponding executables on your system.

Generate a configuration
------------------------

``glacium new`` and ``glacium init`` automatically create ``global_config.yaml`` from ``case.yaml``.  The ``generate`` command performs the same conversion on demand.  Provide the input file and optionally an output path:

.. code-block:: bash

   glacium generate case.yaml -o global_default.yaml

Omit ``-o`` to print the YAML to ``stdout`` instead of writing a file.

Update a project
----------------

Regenerate ``global_config.yaml`` after editing ``case.yaml`` of the
current project:

.. code-block:: bash

   glacium update

Display project info
--------------------

Show parameters of ``case.yaml`` and selected values from the project
configuration:

.. code-block:: bash

   glacium info
Programmatic example
--------------------

The API can create and run projects directly from Python (see :doc:`high_level_api/index`)::

   from glacium.api import Project

   uid = Project("runs").create().uid
   proj = Project.load("runs", uid)
   proj.add_job("POINTWISE_MESH2")
   proj.run()

Logging
-------

Set the environment variable ``GLACIUM_LOG_LEVEL`` to control command
verbosity, e.g. to enable debug logging:

.. code-block:: bash

   export GLACIUM_LOG_LEVEL=DEBUG

