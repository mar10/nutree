------
Graphs
------

.. py:currentmodule:: nutree

.. rubric:: Writing Digraphs


A tree is a `directed graph <https://en.wikipedia.org/wiki/Directed_graph>`_
(aka `digraph`). |br|
Accordingly every tree can be visualized in a graph diagram.

Nutree implements conversion to `DOT format <https://en.wikipedia.org/wiki/DOT_(graph_description_language)>`_.
Given this tree ::

    Tree<'Root'>
    ├── 'A'
    │   ├── 'a1'
    │   │   ├── 'a11'
    │   │   ╰── 'a12'
    │   ╰── 'a2'
    ╰── 'B'
        ╰── 'b1'
            ├── 'a11'  <- second occurence
            ╰── 'b11'

we can write a DOT formatted file like so::

    tree.to_dotfile("graph.gv")

::

    digraph Root {
        // Node definitions
        __root__ [label="Root" shape="box"]
        -2117698517398243110 [label="A"]
        8696834500465194416 [label="a1"]
        3848329043807418154 [label="a11"]
        -8723831530700312132 [label="a12"]
        -1180776893324476219 [label="a2"]
        8369695036033697218 [label="B"]
        1739272887205481547 [label="b1"]
        -1397849070657872512 [label="b11"]

        // Edge definitions
        __root__ -> -2117698517398243110
        -2117698517398243110 -> 8696834500465194416
        8696834500465194416 -> 3848329043807418154
        8696834500465194416 -> -8723831530700312132
        -2117698517398243110 -> -1180776893324476219
        __root__ -> 8369695036033697218
        8369695036033697218 -> 1739272887205481547
        1739272887205481547 -> 3848329043807418154
        1739272887205481547 -> -1397849070657872512
    }

This DOT graph may be rendered in different formats like so::

    tree.to_dotfile("tree_graph.png", format="png")

.. image:: tree_graph.png

Note that in the previous image, the `clone` tree node "a11" is represented 
as a single graph node.
Separate nodes can be created by passing the ``single_inst=False`` argument::

    tree.to_dotfile("graph.png", format="png", single_inst=False)

.. image:: tree_graph_single_inst.png

Pass the ``add_root=False`` argument to remove the root node::

    tree.to_dotfile("graph.png", format="png", add_root=False)

.. image:: tree_graph_no_root.png

The DOT output can be customized with default attribute definitions by passing 
the `graph_attrs`, `node_attrs`, and `edge_attrs` arguments. |br|
In addition, the default attributes can be overriden per node and edge by passing 
mapper callbacks.
See also `list of available attributes <https://graphviz.org/doc/info/attrs.html>`_.

Let's visualize the result of the :ref:`Diff and Merge` example::

    tree_2 = tree_0.diff(tree_1)

    def node_mapper(node: Node, attr_def: dict):
        dc = node.get_meta("dc")
        if dc == DiffClassification.ADDED:
            attr_def["color"] = "#00c000"
        elif dc == DiffClassification.REMOVED:
            attr_def["color"] = "#c00000"

    def edge_mapper(node: Node, attr_def: dict):
        dc = node.get_meta("dc")
        if dc in (DiffClassification.ADDED, DiffClassification.MOVED_HERE):
            attr_def["color"] = "#00C000"
        elif dc in (DiffClassification.REMOVED, DiffClassification.MOVED_TO):
            attr_def["style"] = "dashed"
            attr_def["color"] = "#C00000"

    tree_2.to_dotfile(
        "result.png",
        format="png",
        graph_attrs={},
        node_attrs={"style": "filled", "fillcolor": "#e0e0e0"},
        edge_attrs={},
        node_mapper=node_mapper,
        edge_mapper=edge_mapper,
    )

.. image:: tree_graph_diff.png

.. note::
    Writing of plain DOT formats is natively implemented by `nutree`. |br|
    Rendering of output formats like `png`, `svg`, etc. requires an installation
    of `pydot <https://github.com/pydot/pydot>`_ 
    and `Graphwiz <https://www.graphviz.org>`_.


..
    .. rubric:: Reading Digraphs

    .. note:: Reading of DOT files is not yet implemented.

    .. note::
        Writing of plain DOT formats is natively implemented by `nutree`. |br|
        Reading of DOT formats requires the 
        `pydot <https://github.com/pydot/pydot>`_ library to be installed. |br|

    Every tree is a digraph, however not every digraph can be directly represented 
    as tree, because arbitrary directed graphs 

    1. may contain closed circles (i.e. the graph is not 'acyclic')
    2. may have loops (arrows that directly connect nodes to themselves), which
        is a special case of 1.)
    3. may have multiple arrows with same source and target nodes
    4. may not have an obvious root node (i.e. the graph is not 'rooted')
    5. may be the target of more than one arrow
    6. may have other edge semantics as 'child of'

    As a consequence, 

    1. Circles would result in trees of infinite depth. We stop adding a
        child node if it already appears as its own parent.
    2. See 1.): we do not add a node as child of itself.
    3. We do not allow to add the same node a second time under one parent.
    4. We pick the first node, or search for a good candidate using heuristics.
    5. This node appears multiple times as child of different parents.
    6. TODO:
