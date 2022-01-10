-------------------
Search and Navigate
-------------------

.. py:currentmodule:: nutree


Navigate
--------

::

    assert tree.count == 5

    records_node = tree["Records"]
    assert tree.first_child is records_node

    assert len(records_node.children) == 2
    assert records_node.depth == 1

    n = records_node.first_child
    assert records_node.find("Let It Be") is n

    assert n.name == "Let It Be"
    assert n.depth == 2
    assert n.parent is records_node
    assert n.prev_sibling is None
    assert n.next_sibling.name == "Get Yer Ya-Ya's Out!"
    assert not n.children

Search
------

::

    assert tree.find("Records") is records_node
    assert tree.find("records") is None

    res = tree.find_all(match=r"[GL]et.*")
    print(res)
    assert len(res) == 2

    res = tree.find_all(match=lambda n: "y" in n.name.lower())
    assert len(res) == 1

    res = tree.find_first(match=r"[GL]et.*")
    assert res.name == "Let It Be"


Traversal
---------

**Iteration**

Iterators are the most performant and memory efficient way to traverse the tree.

Iterators are available for the whole tree or by branch (i.e. starting at a node). 
Different travesal methods are supported. ::

    for node in tree:
        # Depth-first, pre-order by default
        ...

    for node in tree.iterator(method=IterMethod.POST_ORDER):
        ...

    # Walk a branch, starting at a distinct node
    res = list(node.iterator(add_self=True))


**Visit**

The :meth:`~nutree.tree.Tree.visit` method is an alternative way to traverse tree 
structures with a little bit more control. 
In this case, a callback function is invoked for every node.

The callback may return (or raise) :class:`~nutree.common.SkipChildren` to 
prevent visiting of the descendant nodes. |br|
The callback may return (or raise) :class:`~nutree.common.StopTraversal` to 
stop traversal immediately. An optional return value may be passed to the 
constructor. 

::

    from nutree import Tree, SkipChildren, StopTraversal

    def callback(node, memo):
        if node.name == "secret":
            # Prevent visiting the child nodes:
            return SkipChildren
        if node.data.foobar == 17:
            raise StopTraversal("found it")

    # `res` contains the value passed to the `StopTraversal` constructor
    res = tree.visit(callback)  # res == "found it"

The `memo` argument contains an empty dict by default, which is discarded after
traversal. This may be handy to cache some calculated values during iteration
for example. |br|
It is also possible to pass in the `memo` argument, in order to access the data
after the call::

    def callback(node, memo):
        if node.data.foobar > 10:
            memo.append(node)

    hits = []
    tree.visit(callback, memo=hits)

We could achieve the same using a closure if the callback is defined in the 
same scope as the `visit()` call::

    hits = []
    def callback(node, memo):
        if node.data.foobar > 10:
            hits.append(node)

    tree.visit(callback)
