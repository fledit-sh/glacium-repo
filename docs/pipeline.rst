Pipeline Workflow
=================

The ``glacium pipeline`` command automates grid convergence studies and
prepares follow-up projects using the best mesh.  The workflow consists
of three steps:

1. **Grid convergence** – create one project per grid refinement level
   using the :mod:`glacium.recipes.grid_dependency` recipe and run all
   jobs.
2. **Evaluation** – collect lift and drag coefficients with
   :func:`glacium.utils.convergence.project_cl_cd_stats` and select the
   grid with the lowest drag (or highest lift).
3. **Follow-up projects** – create a single shot ``prep+solver`` project
   and optional MULTISHOT cases with the chosen refinement level.

Example::

   glacium pipeline --level 1 --level 2 --param CASE_AOA=4 \
       --multishot "[10,300,300]" --multishot "[10] + [30]*20"

The command prints the best grid level followed by the generated project
UIDs.
