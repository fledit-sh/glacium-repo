Adding Custom Recipes
=====================

This guide explains how to extend ``glacium`` with your own job recipes.
Recipes bundle a list of jobs so they can be reused across projects.

Recipe structure
----------------

A recipe is a small class derived from
``glacium.managers.RecipeManager.BaseRecipe``.  It must define a unique
``name`` and short ``description`` and implement ``build()`` which
returns the jobs for a project.  To make the recipe available it needs to
be registered with :func:`glacium.managers.RecipeManager.register`.

.. code-block:: python

   from glacium.managers.RecipeManager import RecipeManager, BaseRecipe
   from glacium.engines.XfoilJobs import XfoilRefineJob
   from glacium.engines.PointwiseJobs import PointwiseGCIJob

   @RecipeManager.register
   class MyRecipe(BaseRecipe):
       name = "my_recipe"
       description = "Example workflow"

       def build(self, project):
           jobs = [
               XfoilRefineJob(project),
               PointwiseGCIJob(project),
           ]
           jobs[1].deps = (jobs[0].name,)
           return jobs

Recipes inside ``glacium.recipes`` are discovered automatically.  If you
store your recipe elsewhere make sure to import the module before calling
:func:`RecipeManager.create` so the decorator can register it.

Using your recipe
-----------------

Specify ``--recipe`` when creating a project:

.. code-block:: bash

   glacium new MyProject --recipe my_recipe

To append all jobs from the recipe to an existing project run:

.. code-block:: bash

   glacium job add --recipe my_recipe

You can list registered recipes programmatically:

.. code-block:: python

   from glacium.managers.RecipeManager import RecipeManager
   print(RecipeManager.list())
