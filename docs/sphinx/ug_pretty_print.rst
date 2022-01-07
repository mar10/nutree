------------
Pretty Print
------------

.. py:currentmodule:: nutree

:meth:`~nutree.tree.Tree.format` produces a pretty formatted string
representation::

    tree.print()
    # ... is a shortcut for:
    print(tree.format())

::

    Tree<'Store'>
    ├── 'Records'
    │   ├── 'Let It Be'
    │   ╰── "Get Yer Ya-Ya's Out!"
    ╰── 'Books'
        ╰── 'The Little Prince'

Pass a formatting string to `repr=` to control how a single node is rendered 
display. For example ``repr="{node}"``, ``repr="{node.path}"``, ``repr="{node.data!r}"``, 
``repr="{node.data.name} (#{node.data_id})"``, etc.

The `style` argument selects the connector type. 
See :attr:`~nutree.common.CONNECTORS` for possible values. ::

    print(tree.format(repr="{node}", style="lines32", title="My Store"))

::

    My Store
    ├─ Node<'Records', data_id=-7187943508994743157>
    │  ├─ Node<'Let It Be', data_id=7970150601901581439>
    │  └─ Node<"Get Yer Ya-Ya's Out!", data_id=-3432395703643407922>
    └─ Node<'Books', data_id=-4949478653955058708>
       └─ Node<'The Little Prince', data_id=6520761245273801231>

Some more examples::

    tree.format(repr="{node.path}", style="list"))

::

    /A
    /A/a1
    /A/a1/a11
    /A/a1/a12
    /A/a2
    /B
    /B/b1
    /B/b1/b11

and::

    tree.format(repr="{node.path}", style="list", join=",")

::

    /A,/A/a1,/A/a1/a11,/A/a1/a12,/A/a2,/B,/B/b1,/B/b1/b11


..
    # Print the __repr__ of the data object:
    for s in tree.format_iter(repr="{node.data}"):
        print(s)
    # Print the __repr__ of the data object:
    for s in tree.format_iter(repr="{node._node_id}-{node.name}"):
        print(s)