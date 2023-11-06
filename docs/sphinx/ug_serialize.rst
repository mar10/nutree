.. _serialize:

-------------
(De)Serialize
-------------

.. py:currentmodule:: nutree


Native Format
-------------

Plain String Nodes
~~~~~~~~~~~~~~~~~~

Assuming we have a tree like this::

    Tree<'fixture'>
    ├── 'A'
    │   ├── 'a1'
    │   │   ├── 'a11'
    │   │   ╰── 'a12'
    │   ╰── 'a2'
    ╰── 'B'
        ├── 'a11'  <- a clone node here
        ╰── 'b1'
            ╰── 'b11'

We can serialize this tree in an efficient JSON based text format::

    tree.save(path)
    # or
    with open(path, "w") as fp:
        tree.save(fp)

Reading is as simple as::

    tree = Tree.load(path)
    # or
    with open(path, "r") as fp:
        tree = Tree.load(fp)

Additional data can be stored::

    meta = {"foo": "bar"}
    tree.save(path, meta=meta)

and retrieved like so::

    meta = {}
    tree = Tree.load(path, file_meta=meta)
    assert meta["foo"] == "bar"

The result will be written as a compact list of (parent-index, data) tuples. |br|
The parent index starts with #1, since #0 is reserved for the system root node. |br|
Note how the 2nd occurence of 'a11' only stores the index of the first 
instance::

    {
        "meta": {
            "$generator": "nutree/0.5.1",
            "$format_version": "1.0",
            "foo": "bar"
        },
        "nodes": [
            [0, "A"],
            [1, "a1"],
            [2, "a11"],
            [2, "a12"],
            [1, "a2"],
            [0, "B"],
            [6, 3],
            [6, "b1"],
            [8, "b11"]
        ]
    }


Arbitrary Objects
~~~~~~~~~~~~~~~~~

Assuming we have a tree with data objects like this::

    Tree<'company'>
    ├── Node<'Department<Development>', data_id=125578508105>
    │   ├── Node<'Person<Alice, 23>', data_id={123-456}>
    │   ├── Node<'Person<Bob, 32>', data_id={234-456}>
    │   ╰── Node<'Person<Charleen, 43>', data_id={345-456}>
    ╰── Node<'Department<Marketing>', data_id=125578508063>
        ├── Node<'Person<Charleen, 43>', data_id={345-456}>
        ╰── Node<'Person<Dave, 54>', data_id={456-456}>

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

    tree.save(path, mapper=serialize_mapper)

the above tree would be written as ::
 
    {
        "meta": {
            "$generator": "nutree/0.5.1",
            "$format_version": "1.0",
        },
        "nodes": [
            [0, { "type": "dept", "name": "Development" }],
            [1, { "type": "person", "name": "Alice", "age": 23, "guid": "{123-456}" }],
            [1, { "type": "person", "name": "Bob", "age": 32, "guid": "{234-456}" }],
            [1, { "type": "person", "name": "Charleen", "age": 43, "guid": "{345-456}" }],
            [0, { "type": "dept", "name": "Marketing" }],
            [5, 4],
            [5, { "type": "person", "name": "Dave", "age": 54, "guid": "{456-456}" }]
        ]
    }

Similarly load a tree from disk::

    tree = Tree.load(path, mapper=deserialize_mapper)

Compact Format
~~~~~~~~~~~~~~

.. todo:: Compact Format

(De)Serialize as List of Dicts
------------------------------

.. note :: While converting a tree to/from a dict is handy at times,
    for standard (de)serialization the :meth:`~nutree.tree.Tree.save()` /
    :meth:`~nutree.tree.Tree.load()` API is recommended.

:meth:`~nutree.tree.Tree.to_dict_list()` converts a tree to a list of 
- potentially nested - dicts. 
We can pass the result to `json.dump()`::

    with open(path, "w") as fp:
        json.dump(tree.to_dict_list(), fp)

The result will look similar to this::

    [
        {
            "data": "A",
            "children": [
            { "data": "a1", "children": [{ "data": "a11" }, { "data": "a12" }] },
            { "data": "a2" }
            ]
        },
        {
            "data": "B",
            "children": [{ "data": "b1", "children": [{ "data": "b11" }] }]
        }
    ]

Reading can then be implemnted using :meth:`~nutree.tree.Tree.from_dict()`::

    with open(path, "r") as fp:
        obj = json.load(fp)
    tree = Tree.from_dict(obj)

.. seealso :: This example tree only contains plain string data.
    Read :doc:`ug_objects` on how to (de)serialize arbitrary objects.
