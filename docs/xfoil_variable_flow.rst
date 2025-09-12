XFOIL variable flow
===================

Data path
---------

The configuration travels through a series of transformations::

   case.yaml → generate_global_defaults + global_default.yaml → global_config.yaml → XfoilScriptJob template → output file

1. ``case.yaml`` supplies case-specific parameters.
2. :func:`~glacium.utils.case_to_global.generate_global_defaults` merges them with ``global_default.yaml`` to produce ``global_config.yaml``.
3. Subclasses of :class:`~glacium.engines.xfoil_base.XfoilScriptJob` read ``global_config.yaml`` and render their Jinja templates.
4. Each template is written to the solver directory and executed to yield the final output file.

.. list-table:: XFOIL jobs, templates and outputs
   :header-rows: 1

   * - Job
     - Template
     - Output file
   * - :class:`~glacium.jobs.xfoil_jobs.XfoilRefineJob`
     - ``XFOIL.increasepoints.in.j2``
     - ``refined.dat``
   * - :class:`~glacium.jobs.xfoil_jobs.XfoilThickenTEJob`
     - ``XFOIL.thickenTE.in.j2``
     - ``thick.dat``
   * - :class:`~glacium.jobs.xfoil_jobs.XfoilBoundaryLayerJob`
     - ``XFOIL.boundarylayer.in.j2``
     - ``bnd.dat``
   * - :class:`~glacium.jobs.xfoil_jobs.XfoilPolarsJob`
     - ``XFOIL.polars.in.j2``
     - ``polars.dat``
   * - :class:`~glacium.jobs.xfoil_jobs.XfoilSuctionCurveJob`
     - ``XFOIL.suctioncurve.in.j2``
     - ``psi.dat``

Equations
---------

Ambient pressure
^^^^^^^^^^^^^^^^

.. math::
   p = 101325 \left(1 - 2.25577\times10^{-5} h\right)^{5.2559}

.. literalinclude:: ../glacium/utils/case_to_global.py
   :lines: 20-22
   :linenos:

.. literalinclude:: ../glacium/utils/first_cellheight.py
   :lines: 14-17
   :linenos:

Density
^^^^^^^

.. math::
   \rho = \frac{p}{R T}

.. literalinclude:: ../glacium/utils/case_to_global.py
   :lines: 63-65
   :linenos:

.. literalinclude:: ../glacium/utils/first_cellheight.py
   :lines: 36-38
   :linenos:

Dynamic viscosity
^^^^^^^^^^^^^^^^^

.. math::
   \mu = \rho\,\nu

.. literalinclude:: ../glacium/utils/case_to_global.py
   :lines: 66
   :linenos:

.. literalinclude:: ../glacium/utils/first_cellheight.py
   :lines: 39
   :linenos:

.. literalinclude:: ../glacium/utils/first_cellheight.py
   :lines: 56-78
   :linenos:

Mach number
^^^^^^^^^^^

.. math::
   M = \frac{V}{\sqrt{\gamma R T}}

.. literalinclude:: ../glacium/utils/case_to_global.py
   :lines: 67-69
   :linenos:

.. list-table:: Source code references
   :header-rows: 1

   * - File
     - Lines
   * - ``glacium/utils/case_to_global.py``
     - 20-22, 63-65, 66, 67-70, 95
   * - ``glacium/utils/first_cellheight.py``
     - 14-17, 36-38, 39, 41, 43-46, 56-78

Reynolds number
^^^^^^^^^^^^^^^

.. math::
   Re = \frac{\rho V c}{\mu}

.. literalinclude:: ../glacium/utils/case_to_global.py
   :lines: 70
   :linenos:

.. literalinclude:: ../glacium/utils/first_cellheight.py
   :lines: 41
   :linenos:

Trailing-edge gap
^^^^^^^^^^^^^^^^^

.. math::
   \text{gap} = \frac{0.001}{c}

.. literalinclude:: ../glacium/utils/case_to_global.py
   :lines: 95
   :linenos:

First cell height
^^^^^^^^^^^^^^^^^

.. math::
   \begin{aligned}
   C_f &= 0.026\,Re^{-1/7} \\
   \tau_w &= \frac{1}{2} C_f V^2 \\
   u_\tau &= \sqrt{\tau_w} \\
   s &= \frac{y^+ \nu}{u_\tau}
   \end{aligned}

Implemented in ``glacium/utils/first_cellheight.py``:

.. literalinclude:: ../glacium/utils/first_cellheight.py
   :lines: 43-46
   :linenos:

Global configuration mapping
----------------------------

.. list-table:: Keys consumed by XFOIL templates
   :header-rows: 1

   * - Key
     - Templates
   * - ``PWS_AIRFOIL_FILE``
     - ``XFOIL.increasepoints.in.j2``, ``XFOIL.suctioncurve.in.j2``
   * - ``PWS_INI_NUM_PANELS``
     - ``XFOIL.increasepoints.in.j2``, ``XFOIL.thickenTE.in.j2``, ``XFOIL.boundarylayer.in.j2``
   * - ``PWS_PROFILE1``
     - ``XFOIL.increasepoints.in.j2``, ``XFOIL.thickenTE.in.j2``
   * - ``PWS_PROFILE2``
     - ``XFOIL.thickenTE.in.j2``, ``XFOIL.polars.in.j2``
   * - ``PWS_TE_GAP``
     - ``XFOIL.thickenTE.in.j2``
   * - ``PWS_TE_BLENDING``
     - ``XFOIL.thickenTE.in.j2``
   * - ``PWS_POL_REYNOLDS``
     - ``XFOIL.polars.in.j2``, ``XFOIL.suctioncurve.in.j2``
   * - ``PWS_POL_MACH``
     - ``XFOIL.polars.in.j2``, ``XFOIL.suctioncurve.in.j2``
   * - ``PWS_POL_ITER``
     - ``XFOIL.polars.in.j2``, ``XFOIL.suctioncurve.in.j2``
   * - ``PWS_POLAR_FILE``
     - ``XFOIL.polars.in.j2``
   * - ``PWS_POL_ALPHA_START`` / ``END`` / ``STEP``
     - ``XFOIL.polars.in.j2``, ``XFOIL.suctioncurve.in.j2``
   * - ``PWS_SUCTION_FILE``
     - ``XFOIL.suctioncurve.in.j2``
   * - ``PWS_PSI_ALPHA_START``
     - ``XFOIL.suctioncurve.in.j2``
