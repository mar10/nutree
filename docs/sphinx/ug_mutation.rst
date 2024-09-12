.. _mutation:

--------
Mutation
--------

.. py:currentmodule:: nutree

.. admonition:: TL;DR

    Nutree provides methods to modify the tree structure in-place. |br|
    This includes adding, moving, and deleting nodes, as well as filtering and sorting.
    

Some in-place modifications are available::

    # Tree
    tree.add(data, ...)
    ...
    # Node
    node.add(data, ...)
    node.prepend_child(data, ...)
    ...
    node.move_to(new_parent, before)
    node.sort_children()

    # Delete nodes
    node.remove()
    node.remove_children()
    # del will call `remove()`
    del tree["A"]
    tree.clear()
    tree.filter(...)

    # Append a copy of branch 'b1' to 'a1'
    tree["a1"].add(tree["b1"])

Filtering, copy, and diff operations usually return the result as a new tree
instance::

    def pred(node):
        # Return true to include `node` and its children
        return node.data.age >= 18

    tree_2 = tree.copy(predicate=pred)

    assert tree_2.first_node is not tree.first_node        # different nodes...
    assert tree_2.first_node.data is tree.first_node.data  # ... reference the same data
    assert tree_2.first_node == tree.first_node            # and evaluate as 'equal'

.. seealso::
        Some methods accept callbacks to control node selection, for example
        :meth:`~nutree.tree.Tree.copy`, 
        :meth:`~nutree.tree.Tree.filter`,
        :meth:`~nutree.tree.Tree.find`, 
        :meth:`~nutree.tree.Tree.find_all`,
        :meth:`~nutree.tree.Tree.find_first`,
        :meth:`~nutree.tree.Tree.visit`, ...
        
        See :ref:`iteration-callbacks` for details.
