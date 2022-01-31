--------
Advanced
--------

..
    Events
    ------

    (Not Yet Implemented.)

    ::

        def on_change(tree, event):
            assert event.type == "change"

        tree.on("change", on_change)


Locking
-------

In multithreading scenarios, we can enforce critical sections like so::

    with tree:
        snapshot = tree.to_dict()


Debugging
---------

Call :meth:`~nutree.tree.Tree._self_check` to validate the internal data structures.
This is slow and should not be done in production::

    assert tree._self_check()


Performance
-----------

Most :class:`~nutree.node.Node` attributes are exposed as readonly properties.
The real attribute is prefixed by an underscore. |br|
In some situations, like close loops in critical algorithms it may be slightly 
faster to access attributes directly.

.. warning:: 
    Use with care. Accessing or even modifying internal attributes may break
    the internal data structures.

When optimizing: 

  1. Correctness before performance: |br|
     Write simple, error free code first and cover it with unit tests, 
     before starting to optimize.

  2. Do not guess or assume: |br|
     write `benchmarks <https://github.com/mar10/nutree/blob/main/tests/test_bench.py>`_ !

