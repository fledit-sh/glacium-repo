Full Power Study
================

The full power study drives a sequence of scripts to validate grid quality,
observe single- and multi-shot behaviour, run clean and iced angle-of-attack
sweeps and finally compare polar curves.  Each step uses
:class:`glacium.api.Project` and other helpers from the high level API.

Subscripts
----------

#. ``01_full_power_creation.py`` builds a grid refinement series and runs a
   basic FENSAP workflow.  It demonstrates the
   :doc:`grid dependency procedure <grid_dependency_study>` and uses jobs
   similar to the :mod:`glacium.recipes.grid_dependency` recipe.  Example::

      python scripts/01_full_power_creation.py

#. ``02_full_power_gci.py`` analyses the refinement runs, computes sliding
   Richardson extrapolation and produces plots and a PDF report.  Lift and drag
   statistics fall back to :func:`glacium.utils.convergence.project_cl_cd_stats`
   if they are missing from project variables.  Example::

      python scripts/02_full_power_gci.py

#. ``03_single_shot_creation.py`` creates a new grid and runs a single
   :math:`\text{DROP3D}`/ICE3D sequence on it.  Case variables can be supplied
   via ``case.yaml`` to drive jobs such as ``DROP3D_RUN`` and
   ``ICE3D_CONVERGENCE_STATS``.  Example::

      python scripts/03_single_shot_creation.py

#. ``04_single_shot_analysis.py`` post-processes the single-shot project using
   tools from :mod:`glacium.post.analysis` to extract and plot ice thickness.
   Results end up in ``04_single_shot_results``.  Example::

      python scripts/04_single_shot_analysis.py

#. ``05_multishot_creation.py`` reuses the single-shot mesh for several
   :mod:`glacium.recipes.multishot` timing scenarios and runs multishot jobs in
   sequence.  Example::

      python scripts/05_multishot_creation.py

#. ``06_multishot_analysis.py`` locates the multishot run with the longest
   ``CASE_MULTISHOT`` list and copies key artefacts such as the ice-growth
   animation into ``06_multishot_results``.  Example::

      python scripts/06_multishot_analysis.py

   These multishot scripts form a :doc:`time dependency study <time_dependency_study>`
   to assess temporal discretisation.

#. ``07_clean_sweep_creation.py`` sweeps angle of attack for the clean geometry
   using the grid from the single-shot run.  It relies on the FENSAP recipe and
   adds analysis jobs like ``FENSAP_ANALYSIS``.  Example::

      python scripts/07_clean_sweep_creation.py

#. ``08_clean_sweep_analysis.py`` gathers lift and drag coefficients from the
   clean sweep, stores them in ``polar.csv`` and plots basic polars.
   :func:`glacium.utils.convergence.project_cl_cd_stats` provides fallback
   values when variables are missing.  Example::

      python scripts/08_clean_sweep_analysis.py

#. ``09_iced_sweep_creation.py`` repeats the angle-of-attack sweep with the
   last iced mesh from the multishot project.  The helper
   :func:`glacium.utils.reuse_mesh` attaches the frozen grid to each run.
   Example::

      python scripts/09_iced_sweep_creation.py

#. ``10_iced_sweep_analysis.py`` mirrors the clean sweep analysis for the iced
   geometry and produces ``polar.csv`` in ``10_iced_sweep_results``.  Example::

      python scripts/10_iced_sweep_analysis.py

#. ``11_polar_compare.py`` reads the clean and iced ``polar.csv`` files and
   generates combined polar plots for quick visual comparison.  Example::

      python scripts/11_polar_compare.py

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
       03_single_shot/
       04_single_shot_results/
       05_multishot/
       06_multishot_results/
       07_clean_sweep/
       08_clean_sweep_results/
       09_iced_sweep/
       10_iced_sweep_results/
       11_polar_combined_results/

