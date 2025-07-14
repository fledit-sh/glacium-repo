Pipeline Workflows
==================

``glacium`` provides predefined **pipeline layouts** that bundle common
project sequences.  Layouts are managed through
``glacium.pipelines.PipelineManager`` and can be selected on the command
line via ``--layout``.  The built in ``grid-convergence`` layout performs
the following steps:

1. **Grid convergence** – for each ``--level`` a project is created using
   the :mod:`glacium.recipes.grid_dependency` recipe and all jobs are run.
2. **Evaluation** – the lift and drag coefficients of the generated
   projects are collected with
   :func:`glacium.utils.convergence.project_cl_cd_stats`.  The grid with
   the lowest drag (or highest lift) is selected.
3. **Follow-up projects** – using the best grid, a single-shot
   ``prep+solver`` project and optional ``MULTISHOT`` cases are spawned.

Example::

   glacium pipeline --layout grid-convergence --level 1 --level 2 \
       --multishot "[10,300,300]"

The command prints the best grid level followed by the generated project
UIDs.  Additional layouts can be registered by placing modules in the
``glacium.pipelines`` package and are selected with ``--layout``.

Meta Report Generation
----------------------

Passing ``--pdf`` merges the ``analysis/report.pdf`` files of all
pipeline projects into a single document.  A summary page with lift and
drag statistics is prepended to the merged PDF which is written to
``<runs>_summary.pdf`` in the parent directory of the runs root.  Use
``--no-pdf`` to disable this behaviour.
