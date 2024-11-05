------
Basics
------

.. py:currentmodule:: nutree

.. admonition:: TL;DR

    Nutree is a Python library for managing hierarchical data structures.
    It stores arbitrary data objects in nodes and provides methods for
    navigation, searching, and iteration.


Data Model
----------

A :class:`~nutree.tree.Tree` object is a shallow wrapper around a single, 
invisible system root node. All visible toplevel nodes are direct children of
this root node. |br|
Trees expose methods to iterate, search, copy, filter, serialize, etc.

A :class:`~nutree.node.Node` represents a single element in the tree. |br|
It is a shallow wrapper around a user data instance, that adds navigation,
modification, and other functionality.

Main `Node` attributes are initialized on construction:

parent (`Node`, readonly)
  The direct ancestor (``node.parent`` is `None` for toplevel nodes).
  Use :meth:`~nutree.node.Node.move_to` to modify.

children (`List[Node]`, readonly)
  List of direct subnodes, may be empty.
  Children are added or removed using methods like
  :meth:`~nutree.tree.Tree.add`,
  :meth:`~nutree.node.Node.prepend_child`,
  :meth:`~nutree.node.Node.remove`,
  :meth:`~nutree.node.Node.remove_children`,
  :meth:`~nutree.node.Node.move_to`, etc.

data (`object|str`, readonly)
  The user data payload. 
  This may be a simple string or an arbitrary object instance. |br|
  Internally the tree maintains a map from `data_id` to the referencing `Nodes`.
  Use :meth:`~nutree.node.Node.set_data` to modify this value. |br|
  The same data instance may be referenced by multiple nodes. In this case we 
  call those nodes `clones`.

data_id (int, readonly):
  The unique key of a `data` instance. This value is calculated as ``hash(data)`` 
  by default, but can be set to a custom value. |br|
  Use :meth:`~nutree.node.Node.set_data` to modify this value.

meta (dict, readonly):
  :class:`~nutree.node.Node` uses 
  `__slots__ <https://docs.python.org/3/reference/datamodel.html?highlight=__slots__#slots>`_ 
  for memory efficiency.
  As a side effect, it is not possible to assign new attributes to a node instance. |br|
  The `meta` slot can be used to attach arbitrary key/value pairs to a node. |br|
  Use :meth:`~nutree.node.Node.get_meta`, :meth:`~nutree.node.Node.set_meta`, 
  :meth:`~nutree.node.Node.update_meta`, and :meth:`~nutree.node.Node.clear_meta`,  
  to modify this value.

node_id (int, readonly):
  The unique key of a `Node` instance. This value is calculated as ``id(node)`` 
  by default, but can be set to a custom value in the constructor.
  It cannot be changed later.

kind (str, readonly):
  Used by :class:`~nutree.typed_tree.TypedNode` (see :ref:`Typed child nodes <typed-tree>`).


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

Chaining
~~~~~~~~

Since `node.add()` return a Node object we can chain calls. 
The `node.up()` method allows to select an ancestor node and the `node.tree`
return the Tree instance::

    tree = Tree()
    tree.add("A").add("a1").up().add("a2").up(2).add("B")
    tree.print()

::
    
        Tree<>
        ├── 'A'
        │   ├── 'a1'
        │   ╰── 'a2'
        ╰── 'B'

or for friends of code golf::

    Tree().add("A").add("a1").up().add("a2").up(2).add("B").tree.print()

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
