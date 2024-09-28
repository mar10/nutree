.. _randomize:

---------------------
Generate Random Trees
---------------------

.. py:currentmodule:: nutree

.. admonition:: TL;DR

    Nutree can generate random tree structures from a structure definition.

.. warning::

    This feature is experimental and may change in future versions.

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
                    # How many instances to create:
                    ":count": 3,
                    # Attribute names and values for every instance:
                    "title": "This is a child node of TYPE_1",
                },
            },
        },
    }

    tree = Tree.build_random_tree(structure_def)

Example::

    structure_def = {
        # Name of the generated tree (optional)
        "name": "fmea",
        # Types define the default properties of the gernated nodes
        "types": {
            # '*' Defines default properties for all node types (optional)
            "*": {
                ":factory": GenericNodeData,  # Default node class (optional)
            },
            # Specific default properties for each node type
            "function": {"icon": "gear"},
            "failure": {"icon": "exclamation"},
            "cause": {"icon": "tools"},
            "effect": {"icon": "lightning"},
        },
        # Relations define the possible parent / child relationships between
        # node types and optionally override the default properties.
        "relations": {
            "__root__": {
                "function": {
                    ":count": 3,
                    "title": TextRandomizer(("{idx}: Provide $(Noun:plural)",)),
                    "details": BlindTextRandomizer(dialect="ipsum"),
                    "expanded": True,
                },
            },
            "function": {
                "failure": {
                    ":count": RangeRandomizer(1, 3),
                    "title": TextRandomizer("$(Noun:plural) not provided"),
                },
            },
            "failure": {
                "cause": {
                    ":count": RangeRandomizer(1, 3),
                    "title": TextRandomizer("$(Noun:plural) not provided"),
                },
                "effect": {
                    ":count": RangeRandomizer(1, 3),
                    "title": TextRandomizer("$(Noun:plural) not provided"),
                },
            },
        },
    }
    
    tree = TypedTree.build_random_tree(structure_def)
    
    assert isinstance(tree, TypedTree)
    assert tree.calc_height() == 3
    
    tree.print()

May produce::

    TypedTree<'fmea'>
    ├── function → GenericNodeData<{'icon': 'gear', 'title': '1: Provide Seniors', 'details': 'Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat. Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat.', 'expanded': True}>
    │   ├── failure → GenericNodeData<{'icon': 'exclamation', 'title': 'Streets not provided'}>
    │   │   ├── cause → GenericNodeData<{'icon': 'tools', 'title': 'Decisions not provided'}>
    │   │   ├── effect → GenericNodeData<{'icon': 'lightning', 'title': 'Spaces not provided'}>
    │   │   ╰── effect → GenericNodeData<{'icon': 'lightning', 'title': 'Kings not provided'}>
    │   ╰── failure → GenericNodeData<{'icon': 'exclamation', 'title': 'Entertainments not provided'}>
    │       ├── cause → GenericNodeData<{'icon': 'tools', 'title': 'Programs not provided'}>
    │       ├── effect → GenericNodeData<{'icon': 'lightning', 'title': 'Dirts not provided'}>
    │       ╰── effect → GenericNodeData<{'icon': 'lightning', 'title': 'Dimensions not provided'}>
    ├── function → GenericNodeData<{'icon': 'gear', 'title': '2: Provide Shots', 'details': 'Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Nam liber tempor cum soluta nobis eleifend option congue nihil imperdiet doming id quod mazim placerat facer possim assum.', 'expanded': True}>
    │   ├── failure → GenericNodeData<{'icon': 'exclamation', 'title': 'Trainers not provided'}>
    │   │   ├── cause → GenericNodeData<{'icon': 'tools', 'title': 'Girlfriends not provided'}>
    │   │   ├── cause → GenericNodeData<{'icon': 'tools', 'title': 'Noses not provided'}>
    │   │   ├── effect → GenericNodeData<{'icon': 'lightning', 'title': 'Closets not provided'}>
    │   │   ╰── effect → GenericNodeData<{'icon': 'lightning', 'title': 'Potentials not provided'}>
    │   ╰── failure → GenericNodeData<{'icon': 'exclamation', 'title': 'Punches not provided'}>
    │       ├── cause → GenericNodeData<{'icon': 'tools', 'title': 'Inevitables not provided'}>
    │       ├── cause → GenericNodeData<{'icon': 'tools', 'title': 'Fronts not provided'}>
    │       ╰── effect → GenericNodeData<{'icon': 'lightning', 'title': 'Worths not provided'}>
    ╰── function → GenericNodeData<{'icon': 'gear', 'title': '3: Provide Shots', 'details': 'Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.', 'expanded': True}>
        ╰── failure → GenericNodeData<{'icon': 'exclamation', 'title': 'Recovers not provided'}>
            ├── cause → GenericNodeData<{'icon': 'tools', 'title': 'Viruses not provided'}>
            ├── effect → GenericNodeData<{'icon': 'lightning', 'title': 'Dirts not provided'}>
            ╰── effect → GenericNodeData<{'icon': 'lightning', 'title': 'Readings not provided'}>    


**A few things to note**

- The generated tree contains nodes :class:`~common.GenericNodeData` as ``node.data``
  value..

- Every ``node.data`` contains items from the structure definition except for
  the ones starting with a colon, for example ``":count"``. |br|
  The node items are merged with the default properties defined in the `types` 
  section.

- Randomizers are used to generate random data for each instance.
  They derive from the :class:`~tree_generator.Randomizer` base class.

- The :class:`~tree_generator.TextRandomizer` and 
  :class:`~tree_generator.BlindTextRandomizer` classes are used to generate 
  random text using the `Fabulist <https://fabulist.readthedocs.io/>`_ library. 

- :meth:`tree.Tree.build_random_tree` creates instances of :class:`~tree.Tree`, while
  :meth:`typed_tree.TypedTree.build_random_tree` creates instances of 
  :class:`~typed_tree.TypedTree`.

- The generated tree contains instances of the :class:`~common.GenericNodeData` 
  class by default, but can be overridden for each node type by adding a 
  ``":factory": CLASS`` entry.

.. note::

    The random text generator is based on the `Fabulist <https://fabulist.readthedocs.io/>`_ 
    library and can use any of its providers to generate random data. |br|
    Make sure to install the `fabulist` package to use the text randomizers
    :class:`~tree_generator.TextRandomizer` and :class:`~tree_generator.BlindTextRandomizer`.
    Either install `fabulist` separately or install nutree with extras: 
    ``pip install "nutree[random]"`` or ``pip install "nutree[all]"``.
