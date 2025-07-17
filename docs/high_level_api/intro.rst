Introduction
=============
   Module: glacium.pipeline
   Primary classes: Run, Pipeline
   Purpose: Declarative, chainable DSL for defining and executing aerodynamic
            simulation cases and study suites without exposing low-level managers.
   All methods return self (or a new object) to enable fluent chaining,
   except for pure accessors such as `preview`, `execute`, `to_dict`, etc.

This section provides an overview of the available classes and helper
functions.  See the following pages for details:

- :doc:`run`
- :doc:`pipeline`
- :doc:`postprocessing`