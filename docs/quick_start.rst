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

Projects live in the ``runs/`` directory.  The ``new`` command generates a
project from the default recipe and prints its unique identifier (UID):

.. code-block:: bash

   glacium new MyWing

The project will be created under ``runs/<UID>``.  You can list all
projects at any time with:

.. code-block:: bash

   glacium projects

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

You may restrict execution to specific jobs by name or index.  The
``list`` command shows the current status and index of each job:

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

Pass ``--all`` to remove every project under ``runs``.

External executables
--------------------

Paths to third party programs are configured in
``runs/<UID>/_cfg/global_config.yaml``.  Important keys include
``POINTWISE_BIN``, ``FENSAP_BIN`` and ``FLUENT2FENSAP_EXE`` which should
point to the corresponding executables on your system.

Generate a configuration
-----------------------

The ``generate`` command creates a ``global_config`` dictionary from a
``case.yaml`` description.  Provide the input file and optionally an output
path:

.. code-block:: bash

   glacium generate case.yaml -o global_default.yaml

Omit ``-o`` to print the YAML to ``stdout`` instead of writing a file.

Update a project
----------------

Regenerate ``global_config.yaml`` after editing ``case.yaml`` of the
current project:

.. code-block:: bash

   glacium update

Logging
-------

Set the environment variable ``GLACIUM_LOG_LEVEL`` to control command
verbosity, e.g. to enable debug logging:

.. code-block:: bash

   export GLACIUM_LOG_LEVEL=DEBUG

