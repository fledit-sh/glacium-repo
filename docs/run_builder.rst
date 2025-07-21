Run builder helper
==================

The :class:`glacium.api.Project` class offers a fluent interface to
configure and create projects programmatically. Each method returns the
instance itself so calls can be chained.

Fluent methods
--------------

``name(value)``
    Set the project name.

``select_airfoil(path)``
    Choose an airfoil data file for the project.

``set(key, value)``
    Store a configuration key/value pair.

``set_bulk(mapping)``
    Add multiple configuration entries at once.

``add_job(name)``
    Append a job by name to the job list.

``jobs(iterable)``
    Append multiple job names.

``tag(label)``
    Attach a tag to the project directory.

``get_mesh(project)``
    Return ``Path`` to ``mesh.grid`` inside ``project``.

``set_mesh(path, project)``
    Copy a mesh file into the project and update configuration keys.

``clone()``
    Return a copy of the builder with the same settings.

``preview()``
    Log the current configuration for inspection.

``create()``
    Build the project on disk and return a
    :class:`~glacium.models.project.Project` instance.

``load(uid)``
    Open an existing project from ``runs_root`` and return a
    :class:`~glacium.api.Project` object.

Only keys present in ``case.yaml`` or the generated
``global_config.yaml`` can be modified. Unknown keys cause
``Project.create()`` to raise a ``KeyError``.

Example usage
-------------

.. code-block:: python

   from glacium.api import Project

   project = (
       Project("runs")
       .name("demo")
       .set("RECIPE", "multishot")
       .set("MULTISHOT_COUNT", 3)
       .add_job("POINTWISE_MESH2")
       .preview()
       .create()
   )
   print("Created", project.root)

