Introduction
=============
   Module: glacium.api
   Primary class: Project
   Purpose: Declarative, chainable DSL for defining and creating aerodynamic
            simulation cases without exposing low-level managers.  Projects can
            be executed programmatically via their ``run`` method.
   All methods return self (or a new object) to enable fluent chaining,
   except for pure accessors such as `preview`, `to_dict`, etc.

This section provides an overview of the available classes and helper
functions.  See the following pages for details:

- :doc:`run`
- :doc:`project`
- :doc:`postprocessing`