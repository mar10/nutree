Installation
============

Installation is straightforward::

  $ pip install nutree

**Note:** Run ``pip install "nutree[graph]"`` or ``pip install "nutree[all]"`` 
instead, in order to install additional graph support.

Installing `nutree` and its dependencies into a 'sandbox' will help to keep
your system Python clean, but requires to activate the virtual environment::

  $ cd /path/to/nutree
  $ pipenv shell
  (nutree) $ pipenv install nutree --upgrade
  ...

Now  the ``nutree`` package can be used in Python code::

  $ python
  >>> from nutree import __version__
  >>> __version__
  '0.0.1'

.. seealso::
   See :doc:`development` for directions for contributors.


Now :doc:`take_the_tour`...

.. Now read the :doc:`user_guide`.
.. `Take the Tour <take_the_tour.html>`_ ...
