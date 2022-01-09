==========
User Guide
==========

A :class:`~nutree.tree.Tree` object is a shallow wrapper around a single, 
invisible system root node. All visible toplevel nodes are direct children of
this root node. |br|
Trees expose methods to iterate, search, copy, filter, serialize, etc.

A :class:`~nutree.node.Node` represents a single element in the tree. |br|
It is a shallow wrapper around a user data instance, that adds navigation,
modification, and other functionality.

Main `Node` attributes are initialized on construction:

parent (`Node`, readonly)
  The direct ancestor.
  Use :meth:`~nutree.node.Node.move` to modify.
children (`List[Node]`, readonly)
  List of direct subnodes, may be empty.
  Children are added or removed using methods like
  :meth:`~nutree.tree.Tree.add`,
  :meth:`~nutree.node.Node.prepend_child`,
  :meth:`~nutree.node.Node.remove`,
  :meth:`~nutree.node.Node.remove_children`,
  :meth:`~nutree.node.Node.move`, etc.
data (`object|str`, readonly)
  The user data payload. 
  This may be a simple string or an arbitrary object instance. |br|
  Internally the tree maintains a map from `data_id` to the referencing `Nodes`.
  Use :meth:`~nutree.node.Node.set_data` to modify this value.
data_id (int, readonly):
  The unique key of a `data` instance. This value is calculated as ``hash(data)`` 
  by default, but can be set to a custom value. |br|
  Use :meth:`~nutree.node.Node.set_data` to modify this value.
node_id (int, readonly):
  The unique key of a `Node` instance. This value is calculated as ``hash(node)`` 
  by default, but can be set to a custom value in the constructor.
  It cannot be changed later.

`Nutree` tries hard to allow developers to focus on their `data` objects instead 
of nodes.
Simple strings or arbitrary object instances can be added and looked-up::

  team_node = tree.add("Team")
  jane = User("Jane")  
  team_node.add(jane)
  ...
  # Lookup by object
  assert tree["Team"] is team_node
  jane_node = tree[jane]  # similar to tree.find(jane)
  assert jane_node.data is jane

  # Lookup by name (assuming the string repesentation of the jane `User` is 'Jane'
  jane_node = tree.find(match="Jane")

It is also possible to lookup by custom keys if objects define them.
Read :doc:`ug_objects` for details.

`Nutree` also supports the case where multiple nodes reference the same `data` 
instance with mehods like
:meth:`~nutree.node.Node.find_all`,
:meth:`~nutree.node.Node.is_clone`, etc. |br|
Read :doc:`ug_clones` for more.


**Read the Details:**

.. toctree::

    ug_basics
    ug_pretty_print
    ug_search_and_navigate
    ug_mutation
    ug_clones
    ug_serialize
    ug_objects
    ug_advanced
