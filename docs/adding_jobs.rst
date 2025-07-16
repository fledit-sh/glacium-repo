Adding Jobs
===========

This guide explains how to implement new :class:`glacium.models.job.Job` classes
and integrate them with the rest of the framework.

Extending ``Job``
-----------------

Create a subclass of :class:`glacium.models.job.Job` and override
:meth:`~glacium.models.job.Job.execute`.  Each job must define a unique
``name`` used for discovery and an optional ``deps`` sequence listing the names
of jobs that need to finish before it may run.

.. code-block:: python

   from glacium.models.job import Job

   class HelloJob(Job):
       name = "HELLO"
       deps = ()

       def execute(self):
           from glacium.utils.logging import log
           log.info("Hello from the job")

Registering with ``JobFactory``
-------------------------------

``JobFactory`` keeps a registry of available jobs.  Subclasses of
:class:`~glacium.models.job.Job` are automatically registered via the
``__init_subclass__`` hook when their module is imported.  If you create a job
class dynamically or outside the standard packages you can register it
manually:

.. code-block:: python

   from glacium.utils.JobIndex import JobFactory

   @JobFactory.register
   class CustomJob(Job):
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
   from glacium.utils.JobIndex import JobFactory

   @RecipeManager.register
   class HelloRecipe(BaseRecipe):
       name = "hello"
       description = "single hello job"

       def build(self, project):
           return [JobFactory.create("HELLO", project)]
