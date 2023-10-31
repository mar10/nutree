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


.. _iteration-callbacks:

Iteration Callbacks
-------------------

In the following sections we cover :ref:`searching`, :ref:`traversal`, 
:ref:`mutation`, etc. in detail. |br|
Some methods described there, accept a `predicate` argument, for example
:meth:`~nutree.tree.Tree.copy`, :meth:`~nutree.tree.Tree.filter`, 
:meth:`~nutree.tree.Tree.find_all` ...

In all cases, the `predicate` callback is called with one single `node`
argument and should return control value:

.. note::
    The special values
    :data:`~nutree.common.StopTraversal`, :data:`~nutree.common.SkipBranch`,
    and :data:`~nutree.common.SelectBranch` can be returned as value or raised
    as exception.

:meth:`~nutree.tree.Tree.find`, 
:meth:`~nutree.tree.Tree.find_first`

    The `match` callback can return these values:

    - `False` or `None`: No match: skip the node and continue traversal.
    - `True`: Stop iteration and return this node as result.
    - :data:`~nutree.common.StopTraversal`:
      Stop iteration and return `None` as result.

:meth:`~nutree.tree.Tree.find_all`

    The `match` callback can return these values:

    - `False` or `None`: No match: skip the node and continue traversal.
    - `True`: Add node to results and continue traversal.
    - :data:`~nutree.common.SkipBranch`:
      Skip node and its descendants, but continue iteration with next sibling. |br|
      Return `SkipBranch(and_self=False)` to add the node to results, but skip
      descendants.
    - :data:`~nutree.common.StopTraversal`:
      Stop iteration and return current results.

:meth:`~nutree.tree.Tree.visit`

    The `callback` callback can return these values:

    - `False`:
      Stop iteration immediately.
    - :data:`~nutree.common.StopTraversal`:
      Stop iteration immediately. Return or raise `StopTraversal(value)` to
      specify a return value for the visit method.
    - :data:`~nutree.common.SkipBranch`:
      Skip descendants, but continue iteration with next sibling.
    - `True`, `None`, and all other values: 
      No action: continue traversal.

:meth:`~nutree.tree.Tree.copy`, 
:meth:`~nutree.tree.Tree.filter`, 
:meth:`~nutree.tree.Tree.filtered`,
:meth:`~nutree.node.Node.copy`

    The `predicate` callback can return these values:

    - `True`: Keep the node and visit children.
    - `False` or `None`: Visit children and keep this node if at least one 
      descendant is true.
    - :data:`~nutree.common.SkipBranch`:
      Skip node and its descendants, but continue iteration with next sibling. |br|
      Return `SkipBranch(and_self=False)` to keep the node, but skip descendants.
    - :data:`~nutree.common.SelectBranch`:
      Unconditionally accept node and all descendants (do not call `predicate()`).
      In other words: copy the whole branch.

:meth:`~nutree.tree.Tree.save`
:meth:`~nutree.tree.Tree.to_dict_list`,
:meth:`~nutree.tree.Tree.to_dot`,
:meth:`~nutree.tree.Tree.to_dotfile`,
:meth:`~nutree.tree.Tree.to_list_iter`

    The `mapper(node, data)` callback can modify the dict argument `data`
    in-place (and return `None`) or return a new dict istance.


Locking
-------

In multithreading scenarios, we can enforce critical sections like so::

    with tree:
        snapshot = tree.to_dict_list()


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
    Write `benchmarks <https://github.com/mar10/nutree/blob/main/tests/test_bench.py>`_ !

File System Helper
------------------

There is a simple helper that can be used to read a folder recursively::

    from nutree import load_tree_from_fs
    
    path = "/my/folder/path"
    tree = load_tree_from_fs(path)
    tree.print()

::

    Tree</my/folder/path>
    ├── 'file_1.txt', 13 bytes
    ╰── [folder_1]
        ╰── 'file_1_1.txt', 15 bytes
