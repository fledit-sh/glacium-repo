Project
=======

:class:`glacium.api.Project` wraps a low level
:class:`glacium.models.project.Project` instance and exposes a small
convenience API.  It can be created programmatically::

   from glacium.api import Project

   project = Project("runs").create()
   project.run()                # run all jobs
   project.run("XFOIL_REFINE")  # run a single job by name

The object forwards unknown attributes to the underlying dataclass so
``project.uid`` and ``project.paths`` work as before.

``run(*jobs)``
    Execute the given job names via the project's :class:`~glacium.managers.job_manager.JobManager`.
    When called without arguments all pending jobs are processed.

``load(runs_root, uid)``
    Class method returning a project loaded from ``runs_root/uid``.

``add_job(name)``
    Append ``name`` and any missing dependencies.  The jobs configuration
    and recipe are updated on disk.  Returns a list of added job names.

``get_grid()``
    Return ``Path`` to ``mesh.grid`` inside the project.

``mesh_grid(path)``
    Copy a mesh file into the project and update configuration keys.

Example::

   from glacium.api import Project

   project = Project.load("runs", "my-id")
   project.add_job("POINTWISE_MESH2")
