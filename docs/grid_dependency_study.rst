Grid Dependency Study
=====================

A grid dependency or mesh convergence study quantifies the impact of the
spatial discretisation on simulation results.  By repeatedly solving the
same case on successively finer grids one can estimate the numerical
order of accuracy and extrapolate a grid independent solution.

Theory
------

Consider a sequence of grids ``1`` (coarse), ``2`` (medium) and ``3``
(fine) with refinement ratio ``r`` between successive levels.  Let
``\phi_i`` be a result quantity, for example the lift coefficient,
obtained on grid ``i``.  Assuming monotonic convergence, the observed
order ``p`` can be estimated by `Richardson extrapolation`_ using::

   p = \frac{\ln|\phi_3 - \phi_2| - \ln|\phi_2 - \phi_1|}{\ln r}

where ``r = h_2 / h_1 = h_3 / h_2`` and ``h_i`` is the characteristic grid
spacing.  The discretisation error on the finest grid can then be
approximated with the *grid convergence index* (GCI)::

   \mathrm{GCI}_{12} = F_s \frac{|\phi_2 - \phi_1|}{|\phi_1| (r^p - 1)} \times 100\%

using a safety factor ``F_s`` (commonly ``1.25``).  A low GCI indicates
that further grid refinement has little effect on ``\phi``.

.. _Richardson extrapolation: https://en.wikipedia.org/wiki/Richardson_extrapolation

Workflow with glacium
---------------------

The :mod:`glacium.recipes.grid_dependency` recipe automates the
preparation of multiple grid levels and runs ``POINTWISE_GCI`` followed
by solver execution.  The best grid level can be selected based on
lift or drag after the runs have finished.

After completion you can inspect the coefficients with
:func:`glacium.utils.convergence.stats.project_cl_cd_stats`.  The
``grid-convergence`` layout automatically runs a follow-up
``prep+solver`` project and any provided ``--multishot`` sequences.  When
sequences are present the ``multishot`` recipe is used and the results
are stored in solver specific ``analysis/<solver>`` folders alongside the
generated reports.

