-------------
(De)Serialize
-------------

.. py:currentmodule:: nutree


Serialization
-------------

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

We can serialize this tree in an efficient text format::

    with open(path, "w") as fp:
        tree.save(fp)

If more control is needed, we can call :meth:`~nutree.tree.Tree.to_list_iter` and
``json.dump()`` directly and pass 
additional arguments, or use ``yaml.dump()`` instead::

    with open(path, "w") as fp:
        json.dump(list(tree.to_list_iter()), fp)

The result will be written as a compact list of (parent-index, data) tuples. |br|
Note how the 2nd occurence of 'a11' only stores the index of the first 
instance::

    [
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


Deserialization
---------------

Reading is as simple as::

    with open(path, "r") as fp:
        tree = Tree.load(fp)

.. seealso :: This example tree only contains plain string data.
    Read :doc:`ug_objects` on how to (de)serialize arbitrary objects.


(De)Serialize as List of Dicts
------------------------------

:meth:`~nutree.tree.Tree.to_dict()` converts a tree to a list of 
- potentially nested - dicts. 
We can pass the result to `json.dump()`::

    with open(path, "w") as fp:
        json.dump(tree.to_dict(), fp)

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
