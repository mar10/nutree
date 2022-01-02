-----------------------------
Multiple Instances ('Clones')
-----------------------------

.. py:currentmodule:: nutree

Every :class:`~nutree.node.Node` instance is unique within the tree and
also has a unique `node.node_id` value.

However, one data object may be added multiple times to a tree at different
locations::

    Tree<'multi'>
    ├── 'A'
    │   ├── 'a1'
    │   ╰── 'a2'
    ╰── 'B'
        ├── 'b1'
        ╰── 'a2'  <- 2nd occurence

.. note:: Multiple instances must not appear under the same parent node.

In this case, a lookup using the indexing syntax (`tree[data]`) is not allowed. |br|
Use :meth:`tree.Tree.find_first()` or :meth:`~tree.Tree.find_all()` instead.

`find_first()` will return the first match (or `None`). 
Note that :meth:`~tree.Tree.find()` is an alias for :meth:`~tree.Tree.find_first()`::

    print(tree.find("a2"))

::

    Node<'a2', data_id=-942131188891065821>

:meth:`~tree.Tree.find_all()` will return all matches (or an empty array `[]`)::

    res = tree.find_all("a2")
    assert res[0] is not res[1], "Node instances are NOT identical..."
    assert res[0] == res[1],     "... but evaluate as equal."
    assert res[0].parent.name == "A"
    assert res[1].parent.name == "B"
    assert res[0].data is res[1].data, "A single data object instance is referenced by both nodes"

    print(res)

::

    [Node<'a2', data_id=-942131188891065821>, Node<'a2', data_id=-942131188891065821>]
