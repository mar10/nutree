--------
Mutation
--------

..
    .. toctree::
    :hidden:

Some in-place modifications are available::

    # Tree
    tree.add(data, ...)
    ...
    # Node
    node.add(data, ...)
    node.prepend_child(data, ...)
    ...
    node.copy_from(src_node, ...)
    node.move(new_parent, before)
    node.remove()
    node.remove_children()
    node.sort_children()

Filtering and set-like operations usually return the result as a new tree
instance::

    def pred(node):
        return "q" in node.data.name.lower()

    tree_2 = tree.copy(predicate=pred)

    assert tree_2.first_node is not tree.first_node        # different nodes...
    assert tree_2.first_node.data is tree.first_node.data  # ... reference the same data
    assert tree_2.first_node == tree.first_node            # and evaluate as 'equal'

Direkt modification of `node.node_id`, `node.data_id` would mess up the internal
bookkeeping.

.. note:: 
    If `node.data` is modified, this _may_ change the result of `hash(node.data)`.

.. todo::  Describe solutions.
