ConfigManager Guide
===================

This guide explains how to use :class:`glacium.managers.ConfigManager` to
read and write project configuration files.  The manager abstracts file
handling and caches loaded data so repeated operations are fast.

Basic usage
-----------

.. code-block:: python

   from pathlib import Path
   from glacium.managers.PathManager import PathBuilder
   from glacium.managers.ConfigManager import ConfigManager

   paths = PathBuilder(Path("runs/my_project")).build()
   cfg_mgr = ConfigManager(paths)
   cfg = cfg_mgr.load_global()
   cfg_mgr.set("PROJECT_NAME", "demo")
   cfg_mgr.dump_global()

After calling :meth:`~glacium.managers.ConfigManager.dump_global`, any
callbacks registered via :meth:`~glacium.managers.ConfigManager.add_observer`
are triggered.  The manager can also merge subset files into the global
configuration with :meth:`~glacium.managers.ConfigManager.merge_subsets` and
split the global state back into subsets with
:meth:`~glacium.managers.ConfigManager.split_all`.

Tips
----

* Keep the manager instance alive for the lifetime of your project.  It
  caches data internally and performs lazy loading on first access.
* Use :meth:`~glacium.managers.ConfigManager.get` and
  :meth:`~glacium.managers.ConfigManager.set` as convenience helpers for simple
  key/value modifications.

