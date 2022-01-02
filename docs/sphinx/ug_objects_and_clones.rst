------------------
Objects And Clones
------------------

..
    .. toctree::
    :hidden:


Working with Objects
--------------------

The initial example used plain strings as data objects. However, any Python
object can be stored, as long as it is _hashable_.

Assume we have the following Objects::

    class Person:
        def __init__(self, name, *, age, guid=None) -> None:
            self.name = name
            self.age = age
            self.guid = guid

        def __repr__(self) -> str:
            return f"Person<{self.name}, {self.age}>"


    class Department:
        def __init__(self, name, *, guid=None) -> None:
            self.name = name
            self.guid = guid

        def __repr__(self) -> str:
            return f"Department<{self.name}>"

We can add instances of these classes to our tree::

    dev = tree.add(Department("Development"))
    alice = Person("Alice", age=23, guid="{123-456}")
    dev.add(alice)
    ...

For bookkeeping, lookups, and serialization, every data object needs a `data_id`.
This value defaults to ``hash(data)``, which is good enough in many cases. |br|
However the hash value cannot always be calculated and also is not stable enough
to be useful for persistence. In our example, we already have object GUIDs, which
we want to use instead. This can be achieved by passing a callback to the tree::

    def _calc_id(node, data):
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


For bookkeeping and lookups, every data object needs a _data_id_.
This value defaults to ``hash(data)``::

    assert tree["{123-456}"].data.name is "Alice"

    user_obj = Person(name="Slow Joe", age=32, guid="{567-456}")
    user_node = tree.add(user_obj)

    # Node lookup can be done by object
    assert tree[user_obj] is user_node
    assert tree.find(user_obj) is user_node
    # The node wraps the object:
    assert user_node.data is user_obj
    assert user_node.data.age == 32
    assert user_node.data_id == hash(user_obj)

If a meaningful _data_id_ is known, we can explicitly use it instead of the
default::

    user_obj = Person(name="Slow Joe", age=32, guid="{123-456}")
    user_node = tree.add(user_obj, data_id=user_obj.guid)

    # Node lookup can be done by data_id
    assert tree.find(data_id="123-456") is user_node
    # The node wraps the object:
    assert user_node.data is user_obj
    assert user_node.data_id == "123-456"



Serialize
---------

In order to (de)serialize arbitrary data objects, we need to implement _mappers_::


    def serialize_mapper(node, data):
        if isinstance(node.data, fixture.Department):
            data["type"] = "dept"
            data["name"] = node.data.name
        elif isinstance(node.data, fixture.Person):
            data["type"] = "person"
            data["name"] = node.data.name
            data["age"] = node.data.age
        return data

    def deserialize_mapper(parent, data):
        node_type = data["type"]
        if node_type == "person":
            data = fixture.Person(name=data["name"], age=data["age"])
        elif node_type == "dept":
            data = fixture.Department(name=data["name"])
        return data

Te above tree would be serialized as::
 
    [
        [ 0, { "type": "dept", "name": "Development" } ],
        [ 1, { "type": "person", "name": "Alice", "age": 23 } ],
        [ 1, { "type": "person", "name": "Bob", "age": 32 } ],
        [ 1, { "type": "person", "name": "Charleen", "age": 43 } ],
        [ 0, { "type": "dept", "name": "Marketing" } ],
        [ 5, 4 ],
        [ 5, { "type": "person", "name": "Dave", "age": 54 } ]
    ]


Multiple Object Instances ('Clones')
------------------------------------

Every :class:`nutree.node.Node` instance is unique within the tree and
also has a unique `node.node_id` value.

However, one data object may be added multiple times to a tree at different
locations::

    Tree<'multi'>
    ├── 'A'
    │   ├── 'a1'
    │   ╰── 'a2'
    ╰── 'B'
        ├── 'b1'
        ╰── 'a2'  <- 2nd occurence

.. note:: Multiple instances must not appear under the same parent node.

In this case, a lookup using the indexing syntax (`tree[data]`) is not allowed. |br|
Use `tree.find_first()` or `tree.find_all()` instead.

`find_first()` will return the first match (or `None`)::

    print(tree.find("a2"))

::

    Node<'a2', data_id=-942131188891065821>

`find_all()` will return all matches (or an empty array `[]`)::

    res = tree.find_all("a2")
    assert res[0] is not res[1], "Node instances are NOT identical..."
    assert res[0] == res[1],     "... but evaluate as equal."
    assert res[0].parent.name == "A"
    assert res[1].parent.name == "B"
    assert res[0].data is res[1].data, "A single data object instance is referenced by both nodes"

    print(res)

::

    [Node<'a2', data_id=-942131188891065821>, Node<'a2', data_id=-942131188891065821>]
