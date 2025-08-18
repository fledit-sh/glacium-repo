Postprocessing
==============

After running a project you may wish to inspect or convert its results.

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

Importer plug-ins
-----------------

Two helper classes interpret FENSAP output:
``FensapSingleImporter`` deals with ``run_FENSAP`` style folders while
``FensapMultiImporter`` reads ``run_MULTISHOT`` post-processing data.
Both are decorated with :meth:`~glacium.post.PostProcessor.register_importer`
and thus become available as soon as they are imported from
:mod:`glacium.post`.

Automatic jobs
--------------

``POSTPROCESS_SINGLE_FENSAP`` converts single-shot solver results and writes a
``manifest.json`` under the project root. It runs after the last available
solver: if ``DROP3D_RUN`` or ``ICE3D_RUN`` jobs exist they must finish first,
otherwise it executes immediately after ``FENSAP_RUN``. ``POSTPROCESS_MULTISHOT``
handles ``run_MULTISHOT`` in a similar fashion.
``FENSAP_ANALYSIS`` runs :func:`glacium.utils.postprocess_fensap.fensap_analysis`
to create slice screenshots for ``run_FENSAP/soln.dat``.
``MESH_ANALYSIS`` executes :func:`glacium.utils.mesh_analysis.mesh_analysis`
and produces a mesh quality report under ``analysis/MESH``.
``ANALYZE_MULTISHOT`` runs the analysis helpers afterwards and stores figures
under ``analysis/MULTISHOT``.
When a manifest is present ``PostProcessor`` loads the saved ``ArtifactIndex`` instantly::

   from glacium.post import PostProcessor
   pp = PostProcessor(project_path)  # auto-reads manifest

You can also add the jobs explicitly::

   from glacium.api import Project
   proj = Project.load("runs", "uid")
   proj.add_job("DROP3D_RUN")
   proj.add_job("ICE3D_RUN")
   proj.add_job("POSTPROCESS_SINGLE_FENSAP")  # waits for DROP3D_RUN and ICE3D_RUN
   proj.add_job("FENSAP_ANALYSIS")
   proj.add_job("MESH_ANALYSIS")
   proj.run()

Minimal example
---------------

The snippet below mirrors the workflow in §8 of ``specs_postprocessing.md``::

   # --- run solver(s) via Pipeline API ---------------------------------------
   pipe.execute()

   # --- optional automatic post-processing -----------------------------------
   # (if jobs were added, nothing else to do)

   # --- manual post-processing ----------------------------------------------
   from glacium.post import PostProcessor
   pp = PostProcessor("/sim/projects/20250715-130806-677407-CE0B",
                      importers=[FensapSingleImporter, FensapMultiImporter])

   pp.plot("Cl", next(iter(pp.index)))      # first run
   pp.export("/tmp/results.zip")

Analysis helpers
----------------

Small utilities for analysing Tecplot exports live in the
:mod:`glacium.post.analysis` package. They cover ice thickness extraction
and visualisation of STL ice contours.

Example usage::

   from glacium.post import analysis

   wall = analysis.read_wall_zone("wall.dat")
   proc, unit = analysis.process_wall_zone(wall, chord=1.0, unit="mm")
   analysis.plot_ice_thickness(proc, unit, "ice.png")

   contours = analysis.load_contours("contours/*.stl")
   analysis.animate_growth(contours, "growth.gif")


