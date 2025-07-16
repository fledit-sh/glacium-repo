glacium.recipes package
=======================

Recipes bundle jobs into reusable workflows.  They may be combined with
the :mod:`glacium.cli.case_sweep` command to create multiple projects
from parameter sweeps.

Multiple recipes can be chained by joining their names with ``+`` when
creating a project.  For example ``prep+solver`` first runs the
``prep`` recipe and then ``solver``.

Submodules
----------

glacium.recipes.default\_aero module
------------------------------------

.. automodule:: glacium.recipes.default_aero
   :members:
   :show-inheritance:
   :undoc-members:

glacium.recipes.hello\_world module
-----------------------------------

.. automodule:: glacium.recipes.hello_world
   :members:
   :show-inheritance:
   :undoc-members:

glacium.recipes.pointwise module
--------------------------------

.. automodule:: glacium.recipes.pointwise
   :members:
   :show-inheritance:
   :undoc-members:

glacium.recipes.grid\_dependency module
---------------------------------------

.. automodule:: glacium.recipes.grid_dependency
   :members:
   :show-inheritance:
   :undoc-members:

Module contents
---------------

.. automodule:: glacium.recipes
   :members:
   :show-inheritance:
   :undoc-members:
