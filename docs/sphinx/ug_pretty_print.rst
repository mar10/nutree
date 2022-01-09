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
``repr="{node.data.name} (#{node.data_id})"``, etc. |br|
Note that ``repr`` may also be a `function(node)` that returns a string for
display.

The `style` argument selects the connector type. 
See :attr:`~nutree.common.CONNECTORS` for possible values. ::

    tree.format(repr="{node}", style="lines32", title="My Store")

::

    My Store
    ├─ Node<'Records', data_id=-7187943508994743157>
    │  ├─ Node<'Let It Be', data_id=7970150601901581439>
    │  └─ Node<"Get Yer Ya-Ya's Out!", data_id=-3432395703643407922>
    └─ Node<'Books', data_id=-4949478653955058708>
       └─ Node<'The Little Prince', data_id=6520761245273801231>

Set `title` to false to remove the root from the display. ::

    tree.format(title=False)

::

    'Records'
    ├── 'Let It Be'
    ╰── "Get Yer Ya-Ya's Out!"
    'Books'
    ╰── 'The Little Prince'

:meth:`~nutree.node.Node.format` is also implemented for nodes::

    tree["Records"].format())

::

    'Records'
    ├── 'Let It Be'
    ╰── "Get Yer Ya-Ya's Out!"

The 'list' style does not generate connector prefixes::

    tree.format(repr="{node.path}", style="list"))

::

    /A
    /A/a1
    /A/a1/a11
    ...

`join` defaults to ``\n``, but may be changed::

    tree.format(repr="{node.path}", style="list", join=",")

::

    /A,/A/a1,/A/a1/a11,/A/a1/a12,/A/a2,/B,/B/b1,/B/b1/b11

.. note::
    It would also be easy to create custom formatting, for example::
    
        s = ",".join(n.data for n in tree)
        assert s == "A,a1,a11,a12,a2,B,b1,b11"

..
    # Print the __repr__ of the data object:
    for s in tree.format_iter(repr="{node.data}"):
        print(s)
    # Print the __repr__ of the data object:
    for s in tree.format_iter(repr="{node._node_id}-{node.name}"):
        print(s)