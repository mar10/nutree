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

For bookkeeping and lookups, every data object needs a _data_id_.
This value defaults to ``hash(data)``::

    user_obj = User(name="Slow Joe", age=32)
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

    user_obj = User(name="Slow Joe", age=32, guid="123-456")
    user_node = tree.add(user_obj, data_id=user_obj.guid)

    # Node lookup can be done by data_id
    assert tree.find(data_id="123-456") is user_node
    # The node wraps the object:
    assert user_node.data is user_obj
    assert user_node.data_id == "123-456"


Multiple Object Instances
-------------------------

Every tree node (i.e. `nutree.Node`) instance is unique within the tree and
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

In this case, a lookup using the indexing syntax (`tree[data]`) is not allowed. <br>
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
