.. _objects:

--------------------
Working with Objects
--------------------

.. py:currentmodule:: nutree

The previous examples used plain strings as data objects. However, any Python
object can be stored, as long as it is `hashable`.

Assume we have the following Objects::

    class Person:
        def __init__(self, name, *, age, guid=None):
            self.name = name
            self.age = age
            self.guid = guid

        def __repr__(self):
            return f"Person<{self.name}, {self.age}>"


    class Department:
        def __init__(self, name, *, guid=None):
            self.name = name
            self.guid = guid

        def __repr__(self):
            return f"Department<{self.name}>"

We can add instances of these classes to our tree::

    dev = tree.add(Department("Development"))
    alice = Person("Alice", age=23, guid="{123-456}")
    dev.add(alice)
    ...

For bookkeeping, lookups, and serialization, every data object needs a `data_id`.
This value defaults to ``hash(data)``, which is good enough in many cases. :: 

    assert tree[alice].data_id == hash(alice)

However the hash value cannot always be calculated and also is not stable enough
to be useful for persistence. In our example, we already have object GUIDs, which
we want to use instead. This can be achieved by passing a callback to the tree::

    def _calc_id(tree, data):
        if isinstance(data, fixture.Person):
            return data.guid
        return hash(data)

    tree = Tree(calc_data_id=_calc_id)

As a result, persons now use the GUID as data_id::

    Tree<'2009255653136'>
    ├── Node<'Department<Development>', data_id=125578508105>
    │   ├── Node<'Person<Alice, 23>', data_id={123-456}>
    │   ├── Node<'Person<Bob, 32>', data_id={234-456}>
    │   ╰── Node<'Person<Charleen, 43>', data_id={345-456}>
    ╰── Node<'Department<Marketing>', data_id=125578508063>
        ├── Node<'Person<Charleen, 43>', data_id={345-456}>
        ╰── Node<'Person<Dave, 54>', data_id={456-456}>

Lookup works by `data` object or `data_id` as expected::

    assert tree[alice].data_id == "{123-456}"
    assert tree[alice].data.guid == "{123-456}"
    assert tree["{123-456}"].data.name == "Alice"

    assert tree.find(data_id="{123-456}").data is alice


.. _shadow-attributes:

Shadow Attributes (Attribute Aliasing)
--------------------------------------

When storing arbitrary objects within a tree node, all its attributes must be 
accessed through the ``node.data`` attribute. |br|
This can be simplified by using the ``shadow_attrs`` argument, which allows to
access ``node.data.age`` as ``node.age`` for example::

    tree = Tree("Persons", shadow_attrs=True)
    dev = tree.add(Department("Development"))
    alice = Person("Alice", age=23, guid="{123-456}")
    alice_node = dev.add(alice)

    # Standard access using `node.data`:
    assert alice_node.data is alice
    assert alice_node.data.guid == "{123-456}"
    assert alice_node.data.age == 23

    # Direct access using shadowing:
    assert alice_node.guid == "{123-456}"
    assert alice_node.age == 23
    
    # Note caveat: `node.name` is not shadowed, but a native property:
    assert alice.data.name == "Alice"
    assert alice.name == "Person<Alice, 23>"

    # Note also: shadow attributes are readonly:
    alice.age = 24       # ERROR: raises AttributeError
    alice.data.age = 24  # OK!

.. note::

    Aliasing only works for attribute names that are **not** part of the native 
    :class:`~nutree.node.Node` data model. So these attributes will always return
    the native values:
    `children`, `data_id`, `data`, `kind`, `meta`, `node_id`, `parent`, `tree`, 
    and all other methods and properties.

    Note also that shadow attributes are readonly.

.. _generic-node-data:

Generic Node Data
-----------------


.. _random-trees:

Generate Random Trees
---------------------

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
