Adding Jobs
===========

This guide explains how to implement new :class:`glacium.core.JobBase`
classes and integrate them with the rest of the framework.

Extending ``Job``
-----------------

Create a subclass of :class:`glacium.core.JobBase` and override
:meth:`~glacium.core.JobBase.execute`.  Each job must define a unique ``name``
and an optional ``deps`` sequence listing the names of jobs that need to finish
before it may run.

.. code-block:: python

   from glacium.core import JobBase

   class HelloJob(JobBase):
       name = "HELLO"
       deps = ()

       def execute(self):
           from glacium.utils.logging import log
           log.info("Hello from the job")

Job layout
----------

Job classes now live in dedicated modules under ``glacium/jobs``.  Related jobs
share a subpackage so ``ConvergenceStatsJob`` resides in
``glacium/jobs/analysis/convergence_stats.py`` while ``XfoilRefineJob`` lives in
``glacium/jobs/xfoil/refine.py``.  The :mod:`glacium.jobs.base` module defines
abstract helpers :class:`~glacium.jobs.base.ScriptJob` and
:class:`~glacium.jobs.base.PythonJob` which most concrete jobs derive from.

Registering with ``JobFactory``
-------------------------------

``JobFactory`` keeps a registry of available jobs.  ``Job`` subclasses from
:mod:`glacium.models.job` register automatically when imported.  If you derive
directly from :class:`glacium.core.JobBase` or create the class dynamically you
can register it manually:

.. code-block:: python

   from glacium.utils.job_index import JobFactory

   @JobFactory.register
   class CustomJob(JobBase):
       name = "CUSTOM"
       def execute(self):
           ...

Dependencies and configuration
------------------------------

The :attr:`~glacium.models.job.Job.deps` attribute declares job dependencies.
Use these names to ensure execution order within :class:`glacium.managers.job_manager.JobManager`.
Access project configuration through ``self.project.cfg`` and define any custom
keys in your recipe's configuration subsets so they can be modified by users.

Integrating with a recipe
-------------------------

Recipes build a list of jobs for a project.  After implementing and registering
your job, instantiate it inside the recipe's :meth:`~glacium.managers.recipe_manager.BaseRecipe.build`
method using :func:`JobFactory.create`:

.. code-block:: python

   from glacium.managers.recipe_manager import RecipeManager, BaseRecipe
   from glacium.utils.job_index import JobFactory

   @RecipeManager.register
   class HelloRecipe(BaseRecipe):
       name = "hello"
       description = "single hello job"

       def build(self, project):
           return [JobFactory.create("HELLO", project)]
