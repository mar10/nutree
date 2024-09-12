------
Basics
------

.. py:currentmodule:: nutree

.. admonition:: TL;DR

    Nutree is a Python library for managing hierarchical data structures.
    It stores arbitrary data objects in nodes and provides methods for
    navigation, searching, and iteration.


Adding Nodes
------------

Nodes are usually created by adding a new data instance to a parent::

   from nutree import Tree, Node

   tree = Tree("Store")

   n = tree.add("Records")

   n.add("Let It Be")
   n.add("Get Yer Ya-Ya's Out!")

   n = tree.add("Books")
   n.add("The Little Prince")

   tree.print()

::

   Tree<'Store'>
   ├── 'Records'
   │   ├── 'Let It Be'
   │   ╰── "Get Yer Ya-Ya's Out!"
   ╰── 'Books'
       ╰── 'The Little Prince'

.. seealso::

    See :doc:`ug_objects` for details on how to manage arbitrary objects, dicts,
    etc. instead of plain strings.


Info and Navigation
-------------------

Tree statistics and related nodes are accessible like so::

    assert tree.count == 5

    records_node = tree["Records"]
    assert tree.first_child() is records_node

    assert len(records_node.children) == 2
    assert records_node.depth() == 1

    assert tree.find("Records") is records_node
    assert tree.find("records") is None  # case-sensitive

    n = records_node.first_child()
    assert records_node.find("Let It Be") is n

    assert n.name == "Let It Be"
    assert n.depth() == 2
    assert n.parent is records_node
    assert n.prev_sibling() is None
    assert n.next_sibling().name == "Get Yer Ya-Ya's Out!"
    assert not n.children

.. seealso::

    See :doc:`ug_search_and_navigate` for details on how to find nodes.


Iteration
---------

Iterators are available for the hole tree or by branch. Different traversal
methods are supported::

    for node in tree:
        # Depth-first, pre-order by default
        ...

    # Alternatively use `visit` with a callback:

    def callback(node, memo):
        if node.name == "secret":
            # Prevent visiting the child nodes:
            return SkipBranch
        if node.data.foobar == 17:
            raise StopTraversal("found it")

    # `res` contains the value passed to the `StopTraversal` constructor
    res = tree.visit(callback)  # res == "found it"

.. seealso::

    See :doc:`ug_search_and_navigate` for details on traversal.
