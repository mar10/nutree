------
Graphs
------

.. py:currentmodule:: nutree

**Writing Digraphs**


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
    Reading and writing of DOT formats requires the 
    `pydot <https://github.com/pydot/pydot>`_ library to be available. |br|
    Rendering of output formats like `png`, `svg`, etc. requires an installation
    of `Graphwiz <https://www.graphviz.org>`_ in addition.


**Reading Digraphs**

Every tree is a digraph, however not every digraph can be directly displayed as 
tree.


  - `Simple directed graphs` are directed graphs that have no loops 
    (arrows that directly connect vertices to themselves) and no multiple arrows 
    with same source and target nodes.
    ->
    Multiple instances must not appear under the same parent node.

  - `acyclic`

  - `rooted`

  - `??` nodes may be the target of more than one edge.


