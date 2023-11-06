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
This can be simplified by using the ``shadow_attrs`` argument, which allow to
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

