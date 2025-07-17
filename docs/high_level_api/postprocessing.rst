Postprocessing
==============

After executing a pipeline you may wish to inspect or convert the results of
:class:`~glacium.pipeline.RunResult` objects.

Artifacts
---------

``Artifact`` is a tiny dataclass describing one generated file together with its
``kind`` and optional metadata.  Several artifacts form an ``ArtifactSet``
(belonging to a single run) and multiple sets are stored in an ``ArtifactIndex``.
These utilities live in :mod:`glacium.post.artifact`.

PostProcessor
-------------

The :class:`~glacium.post.PostProcessor` walks a project directory and builds an
``ArtifactIndex`` using plug-in importers.  It offers helpers to map files,
retrieve artifacts, plot simple vectors and export the whole index as a zip
archive.

::

   from glacium.post import PostProcessor
   pp = PostProcessor(project_path)
   pp.plot("Cl", next(iter(pp.index)))
   pp.export("/tmp/results.zip")

Converters
----------

:mod:`glacium.post.convert` bundles light-weight wrappers around the
``nti2tecplot`` utility.  ``SingleShotConverter`` processes ``run_FENSAP``,
``run_DROP3D`` or ``run_ICE3D`` directories, while ``MultiShotConverter`` handles
the ``run_MULTISHOT`` folder in parallel.

Minimal example
---------------

The snippet below mirrors the workflow in §8 of ``specs_postprocessing.md``::

   pipe.execute()                                        # run solver(s)
   # optional automatic post-processing if jobs were added
   from glacium.post import PostProcessor
   pp = PostProcessor("/sim/projects/20250715-130806-677407-CE0B",
                      importers=[FensapSingleImporter, FensapMultiImporter])
   pp.plot("Cl", next(iter(pp.index)))                  # first run
   pp.export("/tmp/results.zip")


