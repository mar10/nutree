--------------
Diff and Merge
--------------

.. py:currentmodule:: nutree

The :meth:`~nutree.tree.Tree.diff` method compares a tree (`T0`) against another 
one (`T1`) and returns a merged, annotated copy.

The resulting tree contains a union of all nodes from both trees.
Additional metadata is added to the resulting nodes to classify changes
from the perspective of `T0`. For example a node that only exists
in `T1`, will have an ``ADDED`` marker.

If `ordered` is true, a different child order is also considered a change.

If `reduce` is true, unchanged nodes are removed from the result, leaving a 
compact tree with only the modifications.


Assuming we have two trees, **tree_0**::

    Tree<'T0'>
    ├── 'A'
    │   ├── 'a1'
    │   │   ├── 'a11'
    │   │   ╰── 'a12'
    │   ╰── 'a2'
    ╰── 'B'
        ╰── 'b1'
            ╰── 'b11'

and **tree_1**::

    Tree<'T1'>
    ├── 'A'
    │   ├── 'a1'
    │   │   ╰── 'a12'
    │   ╰── 'a2'
    │       ╰── 'a21'
    ├── 'B'
    ╰── 'C'
        ╰── 'b1'
            ╰── 'b11'

We can now call :meth:`~nutree.tree.Tree.diff` to calculate the changes 
(note that we use use a special `repr` handler to display the metadata
annotations)::

    from nutree import diff_node_formatter

    tree_0 = ...
    tree_1 = ...

    tree_2 = tree_0.diff(tree_1)

    tree_2.print(repr=diff_node_formatter)

::

    Tree<"diff('T0', 'T1')">
    ├── A
    │   ├── a1
    │   │   ├── a11 - [Removed]
    │   │   ╰── a12
    │   ╰── a2
    │       ╰── a21 - [Added]
    ├── B
    │   ╰── b1 - [Moved away]
    ╰── C - [Added]
        ╰── b1 - [Moved here]
            ╰── b11

Pass ``reduce=True`` to remove all unmodified nodes from the result::

    tree_2 = tree_0.diff(tree_1, reduce=True)

::

    Tree<"diff('T0', 'T1')">
    ├── A
    │   ├── a1
    │   │   ╰── a11 - [Removed]
    │   ╰── a2
    │       ╰── a21 - [Added]
    ├── B
    │   ╰── b1 - [Moved away]
    ╰── C - [Added]
        ╰── b1 - [Moved here]

Pass ``ordered=True`` to check for changes in child order as well::

    tree_2 = tree_0.diff(tree_1, ordered=True)

"a12" moved from index 1 to index 0 because "a11" was removed::

    Tree<"diff('T0', 'T1')">
    ├── A
    │   ├── a1 - [Renumbered]
    │   │   ├── a11 - [Removed]
    │   │   ╰── a12 - [Order -1]
    │   ╰── a2
    │       ╰── a21 - [Added]
    ├── B
    │   ╰── b1 - [Moved away]
    ╰── C - [Added]
        ╰── b1 - [Moved here]
            ╰── b11


Classification
--------------

..
    See :class:`~nutree.diff.DiffClassification` for possible values.

The diff tool uses the metadata API to add classification information to 
the generated result nodes.
The 'dc' key has optional values of `ADDED`, `REMOVED`, `MOVED_TO`, 
and `MOVED_HERE`.
When `ordered` is true, 'dc' may also be a 2-tuple of two integers, 
holding previous and new child index::

    from nutree import DiffClassification

    assert tree_2["A"].get_meta("dc") is None
    assert tree_2["a21"].get_meta("dc") == DiffClassification.ADDED
    assert tree_2["b1"].get_meta("dc") == DiffClassification.MOVED_TO
    assert tree_2["a12"].get_meta("dc") == (1, 0)



