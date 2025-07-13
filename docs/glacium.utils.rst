glacium.utils package
=====================

Submodules
----------

glacium.utils.JobIndex module
-----------------------------

.. automodule:: glacium.utils.JobIndex
   :members:
   :show-inheritance:
   :undoc-members:

glacium.utils.ProjectIndex module
---------------------------------

.. automodule:: glacium.utils.ProjectIndex
   :members:
   :show-inheritance:
   :undoc-members:

glacium.utils.current module
----------------------------

.. automodule:: glacium.utils.current
   :members:
   :show-inheritance:
   :undoc-members:

glacium.utils.logging module
----------------------------

.. automodule:: glacium.utils.logging
   :members:
   :show-inheritance:
   :undoc-members:

Convergence analysis helpers
----------------------------

Utilities for post-processing solver convergence files live in the
:mod:`glacium.utils.convergence` module.  The
:func:`~glacium.utils.convergence.cl_cd_stats` function reads
``converg.fensap.*`` files and returns the mean lift and drag coefficients for
each multishot index.  Values are averaged over the last ``n`` iterations and
can be saved to ``CSV`` using ``numpy.savetxt``.

The higher level :func:`~glacium.utils.convergence.analysis` helper performs the
aggregation, writes ``cl_cd_stats.csv`` and generates a plot of the coefficients.
It is executed automatically by
:class:`glacium.jobs.analysis_jobs.ConvergenceStatsJob` after
:class:`~glacium.jobs.fensap_jobs.MultiShotRunJob` completes.  The repository
includes a small ``run_MULTISHOT`` directory with example data which can be
analysed manually:

.. code-block:: bash

   python -m glacium.utils.convergence analysis run_MULTISHOT analysis

This command creates ``analysis/cl_cd_stats.csv`` and ``analysis/cl_cd.png``.
The CSV starts with headers ``index,CL,CD`` and might look like:

.. code-block:: text

   index,CL,CD
   1,3.0,4.0
   2,4.0,8.0

Single file analysis
--------------------

The :func:`~glacium.utils.convergence.analysis_file` helper performs the
same operations for a single solver output file.  It is invoked automatically
by the following job classes:

* :class:`glacium.jobs.analysis_jobs.FensapConvergenceStatsJob`
* :class:`glacium.jobs.analysis_jobs.Drop3dConvergenceStatsJob`
* :class:`glacium.jobs.analysis_jobs.Ice3dConvergenceStatsJob`

You can run it manually with:

.. code-block:: bash

   python -m glacium.utils.convergence analysis_file run_FENSAP/converg analysis

Module contents
---------------

.. automodule:: glacium.utils
   :members:
   :show-inheritance:
   :undoc-members:
