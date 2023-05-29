-------------
(De)Serialize
-------------

.. py:currentmodule:: nutree


Native Format
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


.. seealso :: This example tree only contains plain string data.
    Read :doc:`ug_objects` on how to (de)serialize arbitrary objects.


(De)Serialize as List of Dicts
------------------------------

.. note :: While converting a tree to/from a dict is handy at times,
    for standard (de)serialization the :meth:`~nutree.tree.Tree.save()` /
    :meth:`~nutree.tree.Tree.load()` API is recommended.

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
