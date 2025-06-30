Installation Guide
==================

This guide describes how to install ``glacium`` using ``pip``.
``glacium`` requires **Python 3.12 or newer**.

Basic installation
------------------

Install the package from a local checkout or a source archive:

.. code-block:: bash

   pip install .

After installation the :command:`glacium` entry point becomes available
on the command line.

Development setup
-----------------

For development you can install the package in editable mode and run the
unit tests.

.. code-block:: bash

   pip install -e .
   pytest

To enable automatic version management with poetry run once:

.. code-block:: bash

   poetry self add "poetry-dynamic-versioning[plugin]"

Then ``poetry install`` will fetch ``setuptools_scm`` as defined in
``pyproject.toml``.
