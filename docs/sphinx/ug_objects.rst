.. _objects:

--------------------
Working with Objects
--------------------

.. py:currentmodule:: nutree

.. admonition:: TL;DR

    Nutree allows to store arbitrary objects in its nodes without the
    need to modify them or derive from a common base class. |br|
    It also supports shadow attributes for direct access to object attributes. |br|
    Some objects like *dicts* or *dataclasses* are unhashable and require special
    handling. 

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
This value defaults to ``hash(data)``, which is good enough in many cases:: 

    assert tree[alice].data_id == hash(alice)

However the hash value cannot always be calculated and also is not stable enough
to be useful for persistence. In our example, we already have object GUIDs, which
we want to use instead. This can be achieved by passing a callback to the tree::

    def _calc_id(tree, data):
        if isinstance(data, Person):
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
    alice = Person("Alice", age=23, guid="{123-456}")
    alice_node = tree.add(alice)

    # Standard access using `node.data`:
    assert alice_node.data is alice
    assert alice_node.data.guid == "{123-456}"
    assert alice_node.data.age == 23

    # Direct access using shadowing:
    assert alice_node.guid == "{123-456}"
    assert alice_node.age == 23
    
    # Note also: shadow attributes are readonly:
    alice_node.age = 24       # ERROR: raises AttributeError
    
    # But we can still modify the data object directly:
    alice_node.data.age = 24  # OK!

    # Note caveat: `node.name` is not shadowed, but a native property:
    assert alice.data.name == "Alice"
    assert alice.name == "Person<Alice, 23>"

.. warning::

    Aliasing only works for attribute names that are **not** part of the native 
    :class:`~nutree.node.Node` data model. So these attributes will always return
    the native values:
    `children`, `data_id`, `data`, `kind`, `meta`, `node_id`, `parent`, `tree`, 
    and all other methods and properties.

    Note also that shadow attributes are readonly.


.. _generic-node-data:

Dictionaries (GenericNodeData)
------------------------------

Python 
`dictionaries <https://docs.python.org/3/tutorial/datastructures.html#dictionaries>`_
are unhashable and cannot be used as node data objects::

    d = {"a": 1, "b": 2}
    tree.add(d)  # ERROR: raises `TypeError: unhashable type: 'dict'`

Adding Native Dictionaries
~~~~~~~~~~~~~~~~~~~~~~~~~~

We can handle this by explicitly setting the `data_id` when adding the dict::
    
    node = tree.add({d, data_id="{123-456}")

    assert node.data is d
    assert node.data["a"] == 1

Alternatively, we can implement a custom `calc_data_id` callback function that
returns a unique key for the data object::

    def _calc_id(tree, data):
        if isinstance(data, dict):
            return hash(data["guid"])
        return hash(data)

    tree = Tree(calc_data_id=_calc_id)

    d = {"a": 1, "b": 2, "guid": "{123-456}"}
    tree.add(d)

Wrapping Dictionaries
~~~~~~~~~~~~~~~~~~~~~

Finally, we can use the :class:`~nutree.common.GenericNodeData` which is a simple 
wrapper around a dictionary that 

- is hashable, so it can be added to the tree as ``node.data``
- stores a reference to the original dict internally as ``node.data._dict``
- allows readonly access to dict keys as shadow attributes, i.e. 
  ``node.data._dict["name"]`` can be accessed as ``node.data.name``. |br|
  If ``shadow_attrs=True`` is passed to the tree constructor, it can also be
  accessed as ``node.name``
- allows readonly access to dict keys by index, i.e. ``node.data["name"]`` 

Examples ::

    from nutree import Tree, GenericNodeData

    tree = Tree(shadow_attrs=True)

    d = {"a": 1, "b": 2}
    obj = GenericNodeData(d)
    node = tree.add_child(obj)

We can now access the dict keys as attributes::

    assert node.data._dict is d, "stored as reference"
    assert node.data._dict["a"] == 1

    assert node.data.a == 1, "accessible as data attribute"
    assert node.data["a"] == 1, "accessible by index"

    # Since we enabled shadow_attrs, this is also possible:
    assert node.a == 1, "accessible as node attribute"

    # Note: shadow attributes are readonly:
    node.a = 99          # ERROR: raises AttributeError
    node.data["a"] = 99  # ERROR: raises TypeError

    # We need to access the dict directly to modify it
    node.data._dict["a"] = 99
    assert node.a == 99, "should reflect changes in dict"


GenericNodeData can also be initialized with keyword args like this::

    obj = GenericNodeData(a=1, b=2)

.. warning::
    The :class:`~nutree.common.GenericNodeData` provides a hash value because
    any class that is hashable, so it can be used as a data object. However, the 
    hash value is NOT based on the internal dict but on the object itself. |br|
    This means that two instances of GenericNodeData with the same dict content
    will have different hash values.

.. warning::
    The `shadow_attrs` feature is readonly, so you cannot modify the dict
    through the shadow attributes. You need to access the dict directly for that.

Dataclasses
-----------

`Dataclasses <https://docs.python.org/3/library/dataclasses.html>`_ are a great way
to define simple classes that hold data. However, they are not hashable by default::

    from dataclasses import dataclass

    @dataclass
    class Person:
        name: str
        age: int
        guid: str = None

    alice = Person("Alice", age=23, guid="{123-456}")

    tree.add(alice)  # ERROR: raises `TypeError: unhashable type: 'dict'`

We can handle this in different ways byexplicitly set the `data_id` when adding 
the dataclass instance::

    tree.add(alice, data_id=alice.guid)

Alternatively, we can implement a custom `calc_data_id` callback function that
returns a unique key for the data object::

    def _calc_id(tree, data):
        if hasattr(data, "guid"):
            return hash(data.guid)
        return hash(data)

    tree = Tree(calc_data_id=_calc_id)

    tree.add(alice)

Finally, we can use a frozen dataclass instead, which is immutable and hashable by
default (or pass ``unsafe_hash=True``)::

    @dataclass(frozen=True)
    class Person:
        name: str
        age: int
        guid: str = None

