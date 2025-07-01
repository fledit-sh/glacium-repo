Template Configuration Mapping
==============================

``glacium`` ships a collection of Jinja2 templates under
``glacium/templates/``.  When a project is created these templates are
rendered into ``runs/<UID>/_tmpl`` using values from the project's
configuration files located in ``runs/<UID>/_cfg``.

The default values for each template are stored in
``glacium/conf/templates/*.yaml``.  On project creation all of these
files are merged into ``global_config.yaml`` so that subsequent renders
use project specific values.  After a project has been created any
changes must be made inside ``runs/<UID>/_cfg``.  Editing the files in
``glacium/conf/templates`` has no effect on existing projects.

After modifying a configuration file rerun the corresponding job with
:command:`glacium run` to regenerate the output files.

Important templates
-------------------

The following table lists commonly used templates and the configuration
file controlling them.  Each subset lives under ``runs/<UID>/_cfg`` and
is merged into ``global_config.yaml`` when jobs are executed.

+------------------------------+------------------------------+
| Template                     | Configuration subset/key     |
+==============================+==============================+
| ``FENSAP.ICE3D.par.j2``      | ``FENSAP.ICE3D.par.yaml``     |
| ``FENSAP.DROP3D.par.j2``     | ``FENSAP.DROP3D.par.yaml``    |
| ``FENSAP.FENSAP.par.j2``     | ``FENSAP.FENSAP.par.yaml``    |
| ``FENSAP.ICE3D.files.j2``    | ``FENSAP.ICE3D.files.yaml``   |
| ``FENSAP.DROP3D.files.j2``   | ``FENSAP.DROP3D.files.yaml``  |
| ``POINTWISE.run_pointwise.sh.j2`` | ``POINTWISE.run_pointwise.sh.yaml`` |
| ``XFOIL.polars.in.j2``       | ``XFOIL.polars.in.yaml``      |
| ``XFOIL.run_xfoil.sh.j2``    | ``XFOIL.run_xfoil.sh.yaml``   |
+------------------------------+------------------------------+

Other templates follow the same convention: a ``*.j2`` file is rendered
using values from the subset with the same base name.
