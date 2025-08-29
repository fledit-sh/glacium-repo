Full Power Study
================

The full power study drives a sequence of scripts to validate grid quality,
observe multishot behaviour, run clean and iced angle-of-attack sweeps and
finally compare polar curves.  Each step uses
:class:`glacium.api.Project` and other helpers from the high level API.

Subscripts
----------

#. ``01_full_power_creation.py`` builds a grid refinement series and runs a
   basic FENSAP workflow that includes ``POSTPROCESS_SINGLE_FENSAP`` after
   ``FENSAP_RUN``.  It demonstrates the
   :doc:`grid dependency procedure <grid_dependency_study>` and uses jobs
   similar to the :mod:`glacium.recipes.grid_dependency` recipe.  Example::

      python scripts/01_full_power_creation.py

#. ``02_full_power_gci.py`` analyses the refinement runs, computes sliding
   Richardson extrapolation and produces plots and a PDF report.  Lift and drag
   statistics fall back to :func:`glacium.utils.convergence.project_cl_cd_stats`
   if they are missing from project variables.  Example::

      python scripts/02_full_power_gci.py

#. ``05_multishot_creation.py`` generates multishot projects for several
   :mod:`glacium.recipes.multishot` timing scenarios and runs multishot jobs in
   sequence.  Example::

      python scripts/05_multishot_creation.py

#. ``06_multishot_analysis.py`` locates the multishot run with the longest
   ``CASE_MULTISHOT`` list and copies key artefacts such as the ice-growth
   animation into ``06_multishot_results``.  Example::

      python scripts/06_multishot_analysis.py

   These multishot scripts form a :doc:`time dependency study <time_dependency_study>`
   to assess temporal discretisation.

#. ``07_aoa0_projects.py`` runs zero-angle-of-attack cases for clean and iced
   geometries. It reuses the most refined multishot mesh and stores the
   projects in ``07_clean_aoa0`` and ``07_iced_aoa0``. Example::

      python scripts/07_aoa0_projects.py

#. ``08_clean_sweep_creation.py`` sweeps angle of attack for the clean geometry
   using a pre-existing grid.  Run ``07_aoa0_projects.py`` beforehand to provide
   the AoA=0 baseline used in later plots.  It relies on the FENSAP recipe and
   adds analysis jobs like ``FENSAP_ANALYSIS`` (which normalises flow plots by
   the characteristic chord length).  Example::

      python scripts/08_clean_sweep_creation.py

#. ``09_clean_sweep_analysis.py`` gathers lift and drag coefficients from the
   clean sweep, stores them in ``polar.csv`` and plots basic polars.
   :func:`glacium.utils.convergence.project_cl_cd_stats` provides fallback
   values when variables are missing.  Example::

      python scripts/09_clean_sweep_analysis.py

#. ``10_iced_sweep_creation.py`` repeats the angle-of-attack sweep with the
   last iced mesh from the multishot project.  The helper
   :func:`glacium.utils.reuse_mesh` attaches the frozen grid to each run.
   Example::

      python scripts/10_iced_sweep_creation.py

#. ``11_iced_sweep_analysis.py`` mirrors the clean sweep analysis for the iced
   geometry and produces ``polar.csv`` in ``11_iced_sweep_results``.  Example::

      python scripts/11_iced_sweep_analysis.py

#. ``12_polar_compare.py`` reads the clean and iced ``polar.csv`` files and
   generates combined polar plots for quick visual comparison.  Example::

      python scripts/12_polar_compare.py

Command line interface
----------------------

The entire sequence can be executed with::

   python scripts/00_fullpower.py <study_name>

For example, to use a custom directory name::

   python scripts/00_fullpower.py my_study

Running the driver creates ``<study_name>/`` (default
``C02_V50_T2_L052``) and executes each subscript within that directory.
The resulting structure is::

   <study_name>/
       01_grid_dependency_study/
       02_grid_dependency_results/
       05_multishot/
       06_multishot_results/
       07_clean_aoa0/
       07_iced_aoa0/
       08_clean_sweep/
       09_clean_sweep_results/
       10_iced_sweep/
       11_iced_sweep_results/
       12_polar_combined_results/

