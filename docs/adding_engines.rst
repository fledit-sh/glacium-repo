Adding new engines
==================

This guide explains how to extend Glacium with custom engine wrappers.
Engines are responsible for invoking external programs and are created
via :class:`~glacium.engines.engine_factory.EngineFactory`.

Implement a subclass
--------------------

Create a new class derived from :class:`glacium.core.EngineBase` and add
methods that run your solver or other tools.  Use
:meth:`~glacium.core.EngineBase.run` to execute commands.

.. code-block:: python

   from pathlib import Path
   from glacium.core import EngineBase

   class MyEngine(EngineBase):
       def run_my_solver(self, exe: str, work: Path) -> None:
           # call the executable inside ``work``
           self.run([exe, "--foo"], cwd=work)

Register the class
------------------

Decorate the engine with
:meth:`~glacium.engines.engine_factory.EngineFactory.register`.  The
registry maps class names to constructors so you can instantiate engines
by name.

.. code-block:: python

   from glacium.engines.engine_factory import EngineFactory

   @EngineFactory.register
   class MyEngine(EngineBase):
       ...

Later you can create an instance dynamically:

.. code-block:: python

   engine = EngineFactory.create("MyEngine")

Example
-------

The project includes :class:`~glacium.engines.base_engine.DummyEngine`
used in the test suite.  It simply sleeps for a few seconds and serves as
an easy reference implementation for a registered engine.

