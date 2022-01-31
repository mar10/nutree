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

we can create DOT format like so::

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

    tree.to_dotfile("graph.png", format="png")

.. image:: tree.gv.png

.. note::
    Writing of plain DOT formats is natively implemented by `nutree`. |br|
    Reading of DOT formats requires the 
    `pydot <https://github.com/pydot/pydot>`_ library to be installed. |br|
    Rendering of output formats like `png`, `svg`, etc. requires an installation
    of `pydot` and `Graphwiz <https://www.graphviz.org>`_.


.. rubric:: Reading Digraphs

.. note:: Reading of DOT files is not yet implemented.
    
Every tree is a digraph, however not every digraph can be directly displayed as 
tree, because arbitrary directed graphs 

  1. may contain closed circles (i.e. the graph is not 'acyclic')
  2. may have loops (arrows that directly connect nodes to themselves), which
     is a special case of 1.
  3. may have multiple arrows with same source and target nodes
  4. may not have an obvious root node (i.e. the graph is not 'rooted')
  5. may be the target of more than one arrow

As a consequence, 

  1. Circles would result in trees of infinite depth. We stop adding a
     child node if it already appears as its own parent.
  2. See 1.: we do not add a node as child of itself.
  3. We do not allow to add the same node a second time under one parent.
  4. We pick the first node, or search for a good candidate using heuristics.
  5. This node appears multiple times as child of different parents.
