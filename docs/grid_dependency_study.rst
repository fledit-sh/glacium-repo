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
by solver execution.  The :command:`glacium pipeline` command orchestrates
a complete study and selects the best grid level based on lift or drag.

Create a three level study::

   glacium pipeline --level 1 --level 2 --level 3

After completion you can inspect the coefficients with
:func:`glacium.utils.convergence.project_cl_cd_stats` or simply use the
UID reported by :command:`glacium pipeline` to launch follow-up
``prep+solver`` projects.

