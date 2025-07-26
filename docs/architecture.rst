Architecture Overview
=====================

This section summarises the overall design of **glacium** with a focus on the
core packages and how data flows from the command line to job execution.

Package layout
--------------

The project is organised into a set of top level packages:

* ``glacium`` – root package exposing the public API
* ``glacium/cli`` – ``click`` based command line interface
* ``glacium/engines`` – wrappers around external programs
* ``glacium/jobs`` – concrete job implementations
* ``glacium/core`` – minimal base classes shared by jobs and engines
* ``glacium/managers`` – high level helpers coordinating projects
* ``glacium/recipes`` – collections of jobs bundled under a name
* ``glacium/models`` – dataclasses used across the code base
* ``glacium/utils`` – assorted utilities

Data flow
---------

CLI commands create or load projects via :class:`glacium.managers.project_manager.ProjectManager`.
A :class:`~glacium.managers.path_manager.PathManager` is built for each project to provide
consistent directory access.  Configuration files are handled through
:class:`~glacium.managers.config_manager.ConfigManager` which keeps the global
state cached.  Recipes use :class:`glacium.utils.job_index.JobFactory` to create
job objects from their registered names.  The resulting
:class:`~glacium.managers.job_manager.JobManager` executes jobs in dependency
order and persists their status.

Managers
--------

``PathManager`` defines all project paths and creates directories on demand.
``ConfigManager`` loads and saves ``global_config.yaml`` and optional subsets,
triggering observer callbacks on writes. ``JobManager`` maintains ``jobs.yaml``,
allows running selected jobs and notifies observers about execution events.

Factories
---------

``EngineFactory`` and ``JobFactory`` implement simple registries.  Engines and
jobs register themselves via class decorators.  Recipes or job classes can then
instantiate them by name without direct imports.

Core layer
----------

``glacium.core`` sits at the bottom of the layered model.  It defines
:class:`~glacium.core.JobBase` and :class:`~glacium.core.EngineBase` which
provide the minimal interfaces used throughout the domain layer.  Higher levels
build on these abstractions while remaining independent from concrete
implementations.
