Quick Start Guide
=================

This section walks you through the most common ``glacium`` commands.
Each command provides additional options via ``--help``.

Creating a project
------------------

.. code-block:: bash

   glacium new MyWing

The command prints a project UID and creates the new project under
``runs/<UID>``.

Listing projects
----------------

.. code-block:: bash

   glacium projects

Selecting a project
-------------------

.. code-block:: bash

   glacium select 1

The selected UID is stored in ``~/.glacium_current`` for other commands.

Running jobs
------------

.. code-block:: bash

   glacium run

You can also run specific jobs:

.. code-block:: bash

   glacium run XFOIL_REFINE XFOIL_POLAR

Hydra overrides are supported for parameter sweeps. Results will appear under
``runs/${now}`` according to ``hydra.run.dir``:

.. code-block:: bash

   glacium --multirun xfoil.thickness=[0.01,0.02]

Checking job status
-------------------

.. code-block:: bash

   glacium list

Managing jobs
-------------

Reset a job to ``PENDING`` or select/add/remove jobs by index:

.. code-block:: bash

   glacium job reset XFOIL_POLAR
   glacium job reset 1
   glacium job select 1
   glacium job add 1
   glacium job remove 1

Synchronising and removing projects
-----------------------------------

.. code-block:: bash

   glacium sync
   glacium remove

Use ``--all`` with ``glacium remove`` to delete every project under
``./runs``.
