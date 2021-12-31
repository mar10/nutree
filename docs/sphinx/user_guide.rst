==========
User Guide
==========

The :class:`~nutree.tree.Tree` is a shallow wrapper around a single, invisible 
system root node. All visible toplevel nodes are direct children of this
root node.

The :class:`~nutree.node.Node` represents a single element in the tree.

  * `parent`
  * `children`
  * `data`
  * `data_id`
  
.. toctree::

    ug_basics
    ug_pretty_print
    ug_search_and_navigate
    ug_mutation
    ug_objects_and_clones
    ug_serialize
    ug_advanced
