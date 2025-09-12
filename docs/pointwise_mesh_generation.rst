Pointwise mesh generation
=========================

.. index:: Pointwise mesh generation

Data path
---------

The configuration travels through a series of transformations::

   case.yaml → generate_global_defaults + global_default.yaml → global_config.yaml → PointwiseScriptJob template → output file

1. ``case.yaml`` supplies case-specific parameters.
2. :func:`~glacium.utils.case_to_global.generate_global_defaults` merges them with ``global_default.yaml`` to produce ``global_config.yaml``.
3. Subclasses of :class:`~glacium.engines.pointwise.PointwiseScriptJob` read ``global_config.yaml`` and render their Jinja templates.
4. Each template is written to the solver directory and executed to yield the final mesh files.

.. list-table:: Pointwise jobs, templates and outputs
   :header-rows: 1

   * - Job
     - Template
     - Output files
   * - :class:`~glacium.jobs.pointwise_jobs.PointwiseGCIJob`
     - ``POINTWISE.GCI.glf.j2``
     - ``PWS_PROJ_PATH`` / ``PWS_GRID_PATH``
   * - :class:`~glacium.jobs.pointwise_jobs.PointwiseMesh2Job`
     - ``POINTWISE.mesh2.glf.j2``
     - ``PWS_PROJ_PATH`` / ``PWS_GRID_PATH``

Variable derivations
--------------------

Key mesh parameters originate in :mod:`glacium.utils.case_to_global`:

.. literalinclude:: ../glacium/utils/case_to_global.py
   :lines: 46-74
   :linenos:

Pointwise script context
------------------------

Aliases and output mapping in :class:`~glacium.engines.pointwise.PointwiseScriptJob`:

.. literalinclude:: ../glacium/engines/pointwise.py
   :pyobject: PointwiseScriptJob.prepare
   :linenos:

.. literalinclude:: ../glacium/engines/pointwise.py
   :pyobject: PointwiseScriptJob._context
   :linenos:

Global configuration mapping
----------------------------

.. list-table:: Keys consumed by Pointwise templates
   :header-rows: 1

   * - Key
     - Source
     - Alias
   * - ``PWS_PROF_PATH``
     - Default config
     - -
   * - ``PWS_GRID_PATH``
     - Default config
     - -
   * - ``PWS_PROJ_PATH``
     - Default config
     - -
   * - ``PWS_CHORD_LENGTH``
     - Calculated
     - -
   * - ``PWS_SPLIT_PERCENTAGE``
     - Default config
     - -
   * - ``PWS_FF_FACTOR``
     - Default config
     - -
   * - ``PWS_FF_DIMENSION``
     - Default config
     - -
   * - ``PWS_DIM_BACK_CONNECTORS``
     - Default config
     - -
   * - ``PWS_UPPER_FRONT_DIM``
     - Default config
     - -
   * - ``PWS_UPPER_BACK_DIM``
     - Default config
     - -
   * - ``PWS_LOWER_FRONT_DIM``
     - Default config
     - -
   * - ``PWS_LOWER_BACK_DIM``
     - Default config
     - -
   * - ``PWS_TE_DIM``
     - Default config
     - -
   * - ``PWS_SPACING_1``
     - Default config
     - -
   * - ``PWS_SPACING_2``
     - Default config
     - -
   * - ``PWS_REFINEMENT``
     - case.yaml override
     - -
   * - ``PWS_TREX_FIRST_HEIGHT``
     - Calculated
     - -
   * - ``PWS_TREX_GROWTH_RATE_COND``
     - Default config
     - -
   * - ``PWS_TREX_MAX_LAYERS``
     - Default config
     - -
   * - ``PWS_TREX_FULL_LAYERS``
     - Default config
     - -
   * - ``PWS_TREX_GROWTH_RATE_ATTR``
     - Default config
     - -
   * - ``PWS_SIZE_FIELD_DECAY``
     - Default config
     - -
   * - ``PWS_EXTRUSION_Z_DISTANCE``
     - Calculated
     - -
   * - ``PWS_AIRFOIL_FILE``
     - Default config
     - ``AIRFOIL``
   * - ``PWS_PROFILE1``
     - Default config
     - ``PROFILE1``
   * - ``PWS_PROFILE2``
     - Default config
     - ``PROFILE2``
   * - ``PWS_POLAR_FILE``
     - Default config
     - ``POLARFILE``
   * - ``PWS_SUCTION_FILE``
     - Default config
     - ``SUCTIONFILE``
