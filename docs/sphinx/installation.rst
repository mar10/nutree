Installation
============

**Run From a Virtual Environment**

Installing `nutree` and its dependencies into a 'sandbox' will help to keep
your system Python clean, but requires to activate the virtual environment::

  $ cd /path/to/nutree
  $ pipenv shell
  (nutree) $ pipenv install nutree --upgrade
  ...

.. seealso::
   See :doc:`development` for directions for contributors.

Now  the ``nutree`` package can be used in Python code::

  $ python
  >>> from nutree import __version__
  >>> __version__
  '0.0.1'
