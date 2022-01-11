--------
Mutation
--------

.. py:currentmodule:: nutree

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

    # del will call `remove()`
    del tree["A"]

Filtering and set-like operations usually return the result as a new tree
instance::

    def pred(node):
        # Return false to skip node and its children
        return "q" in node.data.age >= 18

    tree_2 = tree.copy(predicate=pred)

    assert tree_2.first_node is not tree.first_node        # different nodes...
    assert tree_2.first_node.data is tree.first_node.data  # ... reference the same data
    assert tree_2.first_node == tree.first_node            # and evaluate as 'equal'

