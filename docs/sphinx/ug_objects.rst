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


Serialize
---------

In order to (de)serialize arbitrary data objects, we need to implement 
`mappers`::

    def serialize_mapper(node, data):
        if isinstance(node.data, Department):
            data["type"] = "dept"
            data["name"] = node.data.name
        elif isinstance(node.data, Person):
            data["type"] = "person"
            data["name"] = node.data.name
            data["age"] = node.data.age
            data["guid"] = node.data.guid
        return data

    def deserialize_mapper(parent, data):
        node_type = data["type"]
        if node_type == "person":
            data = Person(name=data["name"], age=data["age"], guid=data["guid"])
        elif node_type == "dept":
            data = Department(name=data["name"])
        return data

When we call ::

    with open(path, "w") as fp:
        tree.save(fp, mapper=serialize_mapper)

the above tree would be written as ::
 
  [
    [0, { "type": "dept", "name": "Development" }],
    [1, { "type": "person", "name": "Alice", "age": 23, "guid": "{123-456}" }],
    [1, { "type": "person", "name": "Bob", "age": 32, "guid": "{234-456}" }],
    [1, { "type": "person", "name": "Charleen", "age": 43, "guid": "{345-456}" }],
    [0, { "type": "dept", "name": "Marketing" }],
    [5, 4],
    [5, { "type": "person", "name": "Dave", "age": 54, "guid": "{456-456}" }]
  ]

Similarly load a tree from disk::

    with open(path, "r") as fp:
        tree = Tree.load(fp, mapper=deserialize_mapper)
