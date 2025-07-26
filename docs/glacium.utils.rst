glacium.utils package
=====================

Submodules
----------

glacium.utils.job_index module
-----------------------------

.. automodule:: glacium.utils.job_index
   :members:
   :show-inheritance:
   :undoc-members:

glacium.utils.project_index module
---------------------------------

.. automodule:: glacium.utils.project_index
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
:func:`~glacium.utils.convergence.stats.cl_cd_stats` function reads
``converg.fensap.*`` files and returns the mean lift and drag coefficients for
each multishot index.  Values are averaged over the last ``n`` iterations and
can be saved to ``CSV`` using ``numpy.savetxt``.

The higher level :func:`~glacium.utils.convergence.analysis` helper performs the
aggregation, writes ``cl_cd_stats.csv`` and generates a plot of the coefficients.
It is executed automatically by
:class:`glacium.jobs.analysis.convergence_stats.ConvergenceStatsJob` after
:class:`~glacium.jobs.fensap.multishot_run.MultiShotRunJob` completes.  The repository
includes a small ``run_MULTISHOT`` directory with example data which can be
analysed manually:

.. code-block:: bash

    python -m glacium.utils.convergence analysis run_MULTISHOT analysis

If you see a warning about PyFPDF, uninstall the incompatible package:

.. code-block:: bash

   pip uninstall --yes pyfpdf

This command creates ``analysis/cl_cd_stats.csv`` and ``analysis/figures/cl_cd.png``.
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

* :class:`glacium.jobs.analysis.fensap_convergence_stats.FensapConvergenceStatsJob`
* :class:`glacium.jobs.analysis.drop3d_convergence_stats.Drop3dConvergenceStatsJob`
* :class:`glacium.jobs.analysis.ice3d_convergence_stats.Ice3dConvergenceStatsJob`
* :class:`glacium.jobs.analysis.analyze_multishot.AnalyzeMultishotJob`

You can run it manually with:

.. code-block:: bash

   python -m glacium.utils.convergence analysis_file run_FENSAP/converg analysis

Report creation
---------------

After generating the convergence statistics you can turn the results
into a PDF report using :mod:`glacium.utils.report_converg_fensap`.  The
command reads ``analysis/<solver>/stats.csv`` in the analysis directory and writes
``analysis/<solver>/report.pdf``.  If the required fonts are not found, set the
``FPDF_FONT_DIR`` environment variable to the directory containing the
fonts before running the helper.

.. code-block:: bash

   python -m glacium.utils.report_converg_fensap analysis

Module contents
---------------

.. automodule:: glacium.utils
   :members:
   :show-inheritance:
   :undoc-members:
