Adding Custom Jobs
==================

This guide explains how to implement a new job class and add it to a project.
Jobs are Python classes deriving from :class:`glacium.models.job.Job` or one of
its specialised subclasses.  They are automatically discovered via
:mod:`glacium.utils.JobIndex`.

Implementing a job
------------------

1. **Create the class** inside a module under ``glacium/engines`` or
   ``glacium/recipes``.  Assign a unique ``name`` attribute and implement
   :meth:`~glacium.models.job.Job.execute`::

   from glacium.models.job import Job

   class MyJob(Job):
       name = "MY_JOB"
       deps: tuple[str, ...] = ()

       def execute(self):
           from glacium.utils.logging import log
           log.info("Running custom logic")

2. **Declare dependencies** via ``deps`` so jobs are executed in order.
   Dependencies are listed by job name.

3. **Use helpers** like :class:`glacium.managers.TemplateManager` or
   engine base classes (e.g. :class:`glacium.engines.XfoilBase.XfoilScriptJob`)
   to render templates or run external programs.

Adding jobs to a project
------------------------

Jobs can be bundled in a recipe or added individually.

* **Via a recipe** – create a :class:`glacium.managers.RecipeManager.BaseRecipe`
  subclass that returns your job instances in :meth:`build`.  Register the
  recipe with :func:`~glacium.managers.RecipeManager.register` and use it when
  creating a project with ``glacium new -r <recipe>``.

* **Manually** – select an existing project and run::

     glacium job add MY_JOB

  The CLI resolves dependencies automatically and updates ``jobs.yaml``.

After adding the job run ``glacium run`` to execute it.  Status information is
stored in ``_cfg/jobs.yaml`` within the project directory.

