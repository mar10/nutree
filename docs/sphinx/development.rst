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
We need `Python 3.7+ <https://www.python.org/downloads/>`_,
and `pipenv <https://github.com/kennethreitz/pipenv>`_ on our system.

If you want to run tests on *all* supported platforms, install Python 
3.8, 3.9, 3.10, 3.11, and 3.12.

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

    $ pytest --benchmarks


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
        `travis <https://app.travis-ci.com/github/mar10/nutree>`_,
        so run ``$ tox`` and ``$ tox -e format`` frequently and before
        you commit!


Create a Pull Request
=====================

.. todo::

    	TODO
