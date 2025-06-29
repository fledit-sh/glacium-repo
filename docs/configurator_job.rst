Configurator job
================

The :class:`glacium.engines.configurator.ReynoldsConfigJob` updates
Reynolds number fields in the active project.  It is available under the
job name ``CONFIG_REYNOLDS``.

When run, the job loads the global configuration and checks for a master
key ``REYNOLDS_NUMBER``.  If the key is missing, the value is computed
using :mod:`lambda_explorer.tools.aero_formulas.ReynoldsNumber` based on
freestream parameters.  The result is propagated to multiple keys such
as ``PWS_POL_REYNOLDS`` and ``FSP_REYNOLDS_NUMBER`` and written back to
``global_config.yaml``.

Execute the job manually with::

   glacium run CONFIG_REYNOLDS

