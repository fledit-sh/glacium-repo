XFOIL variable flow
===================

Data path
---------

``case.yaml`` → :func:`generate_global_defaults` → :class:`~glacium.engines.xfoil_base.XfoilScriptJob`

Equations
---------

Ambient pressure
^^^^^^^^^^^^^^^^

.. math::
   p = 101325 \left(1 - 2.25577\times10^{-5} h\right)^{5.2559}

Density
^^^^^^^

.. math::
   \rho = \frac{p}{R T}

Dynamic viscosity
^^^^^^^^^^^^^^^^^

.. math::
   \mu = \rho\,\nu

Mach number
^^^^^^^^^^^

.. math::
   M = \frac{V}{\sqrt{\gamma R T}}

Reynolds number
^^^^^^^^^^^^^^^

.. math::
   Re = \frac{\rho V c}{\mu}

Trailing-edge gap
^^^^^^^^^^^^^^^^^

.. math::
   \text{gap} = \frac{0.001}{c}

First cell height
^^^^^^^^^^^^^^^^^

.. math::
   \begin{aligned}
   C_f &= 0.026\,Re^{-1/7} \\
   \tau_w &= \frac{1}{2} C_f V^2 \\
   u_\tau &= \sqrt{\tau_w} \\
   s &= \frac{y^+ \nu}{u_\tau}
   \end{aligned}

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
