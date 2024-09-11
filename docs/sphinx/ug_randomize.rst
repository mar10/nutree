.. _randomize:

---------------------
Generate Random Trees
---------------------

.. py:currentmodule:: nutree

.. admonition:: TL;DR

    Nutree can generate random tree structures from a structure definition.

Nutree can generate random tree structures from a structure definition.
This can be used to create hierarchical data for test, demo, or benchmarking of 
*nutree* itself.

The result can also be used as a source for creating fixtures for other targets 
in a following next step. |br|
See `Wundebaum demo <https://mar10.github.io/wunderbaum/demo/#demo-plain>`_ and the 
`fixture generator <https://github.com/mar10/wunderbaum/blob/main/test/generator/make_fixture.py>`_ 
for an example.

The structure is defined as Python dictionary that describes the
parent-child relationships to be created.
This definition is then passed to :meth:`tree.Tree.build_random_tree`::

    structure_def = {
        ...
        # Relations define the possible parent / child relationships between
        # node types and optionally override the default properties.
        "relations": {
            "__root__": {  # System root, i.e. we define the top nodes here
                "TYPE_1": {
                    # How many instances to create:
                    ":count": 10,  
                    # Attribute names and values for every instance:
                    "ATTR_1": "This is a top node",
                    "ATTR_2": True,
                    "ATTR_3": 42,
                },
            },
            "TYPE_1": {  # Potential child nodes of TYPE_1
                "TYPE_2": {
                    ":count": 3,
                    "title": "This is a child node of TYPE_1",
                },
            },
            "TYPE_2": {  # Potential child nodes of TYPE_2
                "TYPE_3": {
                    ":count": 3,
                    "title": "This is a child node of TYPE_2",
                },
                "TYPE_4": {
                    ":count": 3,
                    "title": "This is a also child node of TYPE_2",
                },
            },
        },
    }
    tree = Tree.build_random_tree(structure_def)

Example::

    structure_def = {
        #: Name of the new tree (str, optiona)
        "name": "fmea",
        #: Types define the default properties of the nodes
        "types": {
            #: Default properties for all node types
            "*": { ... },
            #: Specific default properties for each node type (optional)
            "TYPE_1": { ... },
            "TYPE_2": { ... },
            ...
        },
        #: Relations define the possible parent / child relationships between
        #: node types and optionally override the default properties.
        "relations": {
            "__root__": {
                "TYPE_1": {
                    ":count": 10,
                    "ATTR_1": "Function {hier_idx}",
                    "expanded": True,
                },
            },
            "function": {
                "failure": {
                    ":count": RangeRandomizer(1, 3),
                    "title": "Failure {hier_idx}",
                },
            },
            "failure": {
                "cause": {
                    ":count": RangeRandomizer(1, 3),
                    "title": "Cause {hier_idx}",
                },
                "effect": {
                    ":count": RangeRandomizer(1, 3),
                    "title": "Effect {hier_idx}",
                },
            },
        },
    }
    tree = Tree.build_random_tree(structure_def)
    tree.print()
    assert type(tree) is Tree
    assert tree.calc_height() == 3

Example::

    structure_def = {
        "name": "fmea",
        #: Types define the default properties of the nodes
        "types": {
            #: Default properties for all node types
            "*": {":factory": GenericNodeData},
            #: Specific default properties for each node type
            "function": {"icon": "bi bi-gear"},
            "failure": {"icon": "bi bi-exclamation-triangle"},
            "cause": {"icon": "bi bi-tools"},
            "effect": {"icon": "bi bi-lightning"},
        },
        #: Relations define the possible parent / child relationships between
        #: node types and optionally override the default properties.
        "relations": {
            "__root__": {
                "function": {
                    ":count": 10,
                    "title": "Function {hier_idx}",
                    "expanded": True,
                },
            },
            "function": {
                "failure": {
                    ":count": RangeRandomizer(1, 3),
                    "title": "Failure {hier_idx}",
                },
            },
            "failure": {
                "cause": {
                    ":count": RangeRandomizer(1, 3),
                    "title": "Cause {hier_idx}",
                },
                "effect": {
                    ":count": RangeRandomizer(1, 3),
                    "title": "Effect {hier_idx}",
                },
            },
        },
    }
    tree = Tree.build_random_tree(structure_def)
    tree.print()
    assert type(tree) is Tree
    assert tree.calc_height() == 3

    tree2 = TypedTree.build_random_tree(structure_def)
    tree2.print()
    assert type(tree2) is TypedTree
    assert tree2.calc_height() == 3

..  note:

    The 
