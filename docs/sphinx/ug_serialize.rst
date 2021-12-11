-------------
(De)Serialize
-------------

..
    .. toctree::
    :hidden:


Serialization
-------------

Use `tree.to_dict()` to serialize as nested structure ::

    with open(path, "w") as fp:
        json.dump(tree.to_dict(), fp)

::

    [
    {
        "data": "A",
        "children": [
        { "data": "a1", "children": [{ "data": "a21" }, { "data": "a22" }] },
        { "data": "a2" }
        ]
    },
    {
        "data": "B",
        "children": [{ "data": "b1", "children": [{ "data": "b11" }] }]
    }
    ]

Use `tree.to_list_iter()` to serialize as flat, parent-referencing list ::

    with open(path, "w") as fp:
        json.dump(list(tree.to_list_iter()), fp)

::

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

will be written as a compact list of (parent-index, data) tuples. |br|
Note how the 2nd occurence of 'a11' only stores the iindex of the first 
instance ::

    [
    [0, "A"],
    [1, "a1"],
    [2, "a11"],
    [2, "a12"],
    [1, "a2"],
    [0, "B"],
    [6, 3],
    [6, "a11"],
    [6, "b1"],
    [8, "b11"]
    ]

.. todo :: Describe mapper callback.

Deserialization
---------------

.. todo :: Describe 
