Adding a Custom Engine
======================

This guide explains how to integrate an external executable with
``glacium`` by implementing a new engine and job.  Engines wrap
:mod:`subprocess` calls so jobs can launch third-party programs in a
portable manner.

1. Create the engine
--------------------

Create a new Python module under ``glacium/engines`` and subclass
:class:`~glacium.engines.base_engine.BaseEngine`.  The subclass should
provide a method that invokes :meth:`~glacium.engines.base_engine.BaseEngine.run`.

.. code-block:: python

   # glacium/engines/my_solver.py
   from pathlib import Path
   from glacium.engines.base_engine import BaseEngine

   class MySolverEngine(BaseEngine):
       def run_solver(self, exe: str, case: str, work: Path) -> None:
           self.run([exe, case], cwd=work)

2. Implement a job
------------------

Jobs collect configuration values and use engines to run the solver.
Create a :class:`~glacium.models.job.Job` subclass that uses the engine
defined above.

.. code-block:: python

   # glacium/engines/my_solver.py
   from glacium.models.job import Job

   class MySolverJob(Job):
       name = "MY_SOLVER_RUN"
       deps: tuple[str, ...] = ()

       def execute(self) -> None:
           cfg = self.project.config
           paths = self.project.paths
           work = paths.solver_dir("my_solver")

           exe = cfg.get("MY_SOLVER_EXE", "my_solver")
           case = cfg.get("MY_SOLVER_CASE", "input.cas")

           engine = MySolverEngine()
           engine.run_solver(exe, case, work)

3. Export the classes
---------------------

Expose the engine and job via ``glacium.engines.__init__`` so they can be
imported by recipes or other modules.

.. code-block:: python

   # glacium/engines/__init__.py
   from .my_solver import MySolverEngine, MySolverJob
   __all__ += ["MySolverEngine", "MySolverJob"]

4. Update configuration
-----------------------

Add the executable path and any required input files to your project’s
configuration, for example in ``runs/<UID>/_cfg/global_config.yaml``:

.. code-block:: yaml

   MY_SOLVER_EXE: /path/to/my_solver
   MY_SOLVER_CASE: my_case.cas

5. Use the job
--------------

Add ``MY_SOLVER_RUN`` to your recipe or run it manually with
:command:`glacium job add`.  The new job will launch your program via the
engine whenever it is executed.

