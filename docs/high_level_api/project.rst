Project
=======

:class:`glacium.api.Project` wraps a low level
:class:`glacium.models.project.Project` instance and exposes a small
convenience API.  It is returned by :meth:`glacium.api.Run.create` and
lets you execute jobs programmatically::

   from glacium.api import Run

   project = Run("runs").create()
   project.run()                # run all jobs
   project.run("XFOIL_REFINE")  # run a single job by name

The object forwards unknown attributes to the underlying dataclass so
``project.uid`` and ``project.paths`` work as before.

``run(*jobs)``
    Execute the given job names via the project's :class:`~glacium.managers.job_manager.JobManager`.
    When called without arguments all pending jobs are processed.
