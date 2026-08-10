===========
Development
===========

Install for Development
=======================

First off, thanks for taking the time to contribute!

This small guideline may help taking the first steps.

Happy hacking :)


Fork the Repository
-------------------

Clone nutree to a local folder and checkout the branch you want to work on::

    $ git clone git@github.com:mar10/nutree.git
    $ cd nutree
    $ git checkout my_branch


Work in a Virtual Environment
-----------------------------

Install Python
^^^^^^^^^^^^^^
We need `Python 3 <https://www.python.org/downloads/>`_,
and `pipenv <https://github.com/kennethreitz/pipenv>`_ on our system.

If you want to run tests on *all* supported platforms, install all Python 
versions in parallel.

Create and Activate the Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install dependencies for debugging::

    $ cd /path/to/nutree
    $ pipenv shell
    (nutree) $ pipenv install --dev
    (nutree) $

The development requirements already contain the nutree source folder, so
``pipenv install -e .`` is not required.

The test suite should run ::

    $ tox

Build Sphinx documentation to target: `<nutree>/docs/sphinx-build/index.html`) ::

    $ tox -e docs


Run Tests
=========

Run all tests with coverage report. Results are written to <nutree>/htmlcov/index.html::

    $ tox

Run selective tests::

    $ tox -e py312
    $ tox -e py312 -- -k test_core


Run Benchmarks
==============

Benchmarks are unit tests that execute small variants of code and measure the
elapsed time.
See `here <https://github.com/mar10/nutree/blob/main/tests/test_bench.py>`_ 
for some examples.

Since this takes some time, benchmarks are not run with the default test suite, 
but has to be enabled like so::

    $ tox -e benchmarks


Code
====

The tests also check for `eslint <https://eslint.org>`_,
`flake8 <http://flake8.pycqa.org/>`_,
`black <https://black.readthedocs.io/>`_,
and `isort <https://github.com/timothycrosley/isort>`_ standards.

Format code using the editor's formatting options or like so::

    $ tox -e format


.. note::

    	Follow the Style Guide, basically
        `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_.

        Failing tests or not follwing PEP 8 will break builds on
        `GitHub <https://github.com/mar10/fabulist/actions/workflows/tests.yml>`_,
        so run ``$ tox`` and ``$ tox -e format`` frequently and before
        you commit!


Create a Pull Request
=====================

.. todo::

    	TODO


Release Process
===============

The authoritative release mechanism is the tag-driven GitHub Actions workflow
(`.github/workflows/release.yml`). Pushing a version tag to GitHub triggers
the full pipeline automatically.

Release Steps
-------------

1. **Prepare changelog**

   Edit ``CHANGELOG.md``: move items from *Unreleased* into a new section
   with the target version and today's date::

       ## 1.2.0 (2026-06-29)
       ...

2. **Set the release version**

   Update ``pyproject.toml`` (``[project].version``) to the release version
   (PEP 440, no ``-`` separators), for example using ``uv version``::

       $ uv version 1.2.0      # final release
       $ uv version 1.2.0rc1   # release candidate (optional)

     ``uv`` bump shortcuts are context-sensitive. Use them like this:

     - Current version is pre-release (for example ``1.1.1a1``):
         ``uv version --bump stable`` -> ``1.1.1``
     - Current version is development (for example ``1.1.1.dev1``):
         ``uv version --bump stable`` -> ``1.1.1``
     - Current version is final (for example ``1.1.1``):
         ``uv version --bump patch`` -> ``1.1.2``

     .. note::

            Do **not** use ``uv version --bump patch`` when cutting a stable release
            from ``1.1.1a1`` or ``1.1.1.dev1``: it would jump to ``1.1.2``.

   Version format rules:

   - Pre-release: ``1.2.0a1``, ``1.2.0b1``, ``1.2.0rc1``
   - Final:       ``1.2.0``
   - Development: ``1.2.1.dev1``  (never publish ``dev`` builds to PyPI)

3. **Run quality checks locally** (optional but recommended)::

    $ tox -e lint,ty
    $ tox

4. **Commit and tag**

    Create and push a ``v``-prefixed tag whose numeric part matches
    ``[project].version`` exactly (for example ``v1.2.0`` for version
    ``1.2.0``)::

       $ git add CHANGELOG.md pyproject.toml
       $ git commit -m "Release 1.2.0"
       $ git tag v1.2.0
       $ git push origin main --tags

5. **Monitor the workflow**

   Open *Actions → Release* on GitHub and watch the jobs:

   - ``validate``        – checks tag/version match, runs lint + tests
   - ``build``           – builds ``sdist`` and ``wheel``
   - ``github-release``  – attaches artifacts to the GitHub Release
   - ``pypi-publish``    – publishes to PyPI via Trusted Publisher
   - ``post-release-bump`` – opens a PR bumping source to next ``.dev1``

6. **Merge the post-release bump PR**

   After the release is confirmed, merge the automated PR (e.g.
   ``post-release/v1.2.1.dev1``) that was opened against ``main``.

PyPI Trusted Publisher Setup
-----------------------------

The workflow uses `OIDC Trusted Publisher
<https://docs.pypi.org/trusted-publishers/>`_ — no API token is needed.
The trust relationship must be configured **once** on pypi.org:

.. code-block:: text

   Publisher:       GitHub Actions
   Owner:           mar10
   Repository:      nutree
   Workflow file:   release.yml
   Environment:     pypi

Local / Manual Releases
-----------------------

``yabs`` is kept as an optional local tool for experimentation. It no longer
represents the authoritative release path. Run it only when you need a quick
local dry-run of the version-bump sequence::

    $ yabs run --inc patch --dry-run
