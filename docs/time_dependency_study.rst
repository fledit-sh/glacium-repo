Time Dependency Study
=====================

A time dependency or time-step convergence study quantifies the impact of the
temporal discretisation on simulation results.  By repeatedly solving the same
case with successively smaller time steps one can estimate the numerical order
of accuracy and extrapolate a time-step independent solution.

Theory
------

Consider a sequence of time steps ``1`` (coarse), ``2`` (medium) and ``3``
(fine) with refinement ratio ``r`` between successive levels.  Let
``\phi_i`` be a result quantity, for example the lift coefficient, obtained
with time step ``i``.  Assuming monotonic convergence, the observed
order ``p`` can be estimated by `Richardson extrapolation`_ using::

   p = \frac{\ln|\phi_3 - \phi_2| - \ln|\phi_2 - \phi_1|}{\ln r}

where ``r = \Delta t_2 / \Delta t_1 = \Delta t_3 / \Delta t_2`` and
``\Delta t_i`` is the time step size.  The discretisation error on the
finest step can then be approximated with the *time-step convergence index*
(TCI)::

   \mathrm{TCI}_{12} = F_s \frac{|\phi_2 - \phi_1|}{|\phi_1| (r^p - 1)} \times 100\%

using a safety factor ``F_s`` (commonly ``1.25``).  A low TCI indicates that
further reduction of ``\Delta t`` has little effect on ``\phi``.  The efficiency
index combines error and runtime::

   E = \mathrm{TCI} \times t

where ``t`` is the wall-clock time for the finest time step.

.. _Richardson extrapolation: https://en.wikipedia.org/wiki/Richardson_extrapolation

Workflow with multishot projects
--------------------------------

The :mod:`glacium.recipes.multishot` recipe automates the preparation of
multiple time-step sequences and runs them in order.  The scripts
``05_multishot_creation.py`` and ``06_multishot_analysis.py`` from the full power
study demonstrate this workflow.

``05_multishot_creation.py`` reuses a single-shot mesh and creates a multishot
project with progressively smaller ``shot_times``.  Each sequence executes the
necessary ``prep`` and solver jobs and stores the results in
``05_multishot/analysis/<solver>``.  After the runs have completed,
``06_multishot_analysis.py`` locates the longest ``CASE_MULTISHOT`` list and
copies key artefacts such as the ice-growth animation into
``06_multishot_results``.  The analysis script also gathers lift and drag
coefficients via :func:`glacium.utils.convergence.project_cl_cd_stats`.

Example commands and interpretation of results
---------------------------------------------

To perform a time dependency study using these scripts::

   python scripts/05_multishot_creation.py
   python scripts/06_multishot_analysis.py

``05_multishot_creation.py`` produces the multishot runs while
``06_multishot_analysis.py`` collates the coefficients for each time step.  The
script reports the observed order ``p``, the time-step convergence index and the
run time for each window of three sequences.  The recommended time step is the
one with the lowest efficiency index ``E`` for lift (``CL``); drag results are
reported for reference only.
