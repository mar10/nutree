-------------------
Search and Navigate
-------------------

.. py:currentmodule:: nutree


Navigate
--------

::

    assert tree.count == 5

    records_node = tree["Records"]
    assert tree.first_child() is records_node

    assert len(records_node.children) == 2
    assert records_node.depth() == 1

    n = records_node.first_child()
    assert records_node.find("Let It Be") is n

    assert n.name == "Let It Be"
    assert n.depth() == 2
    assert n.parent is records_node
    assert n.prev_sibling() is None
    assert n.next_sibling().name == "Get Yer Ya-Ya's Out!"
    assert not n.children


Search
------

::
    # Case sensitive:
    assert tree.find("Records") is records_node
    assert tree.find("records") is None

    # 'Smart' search:
    assert tree["Records"] is records_node

    # Regular expressions
    res = tree.find_all(match=r"[GL]et.*")
    print(res)
    assert len(res) == 2

    res = tree.find_all(match=lambda n: "y" in n.name.lower())
    assert len(res) == 1

    res = tree.find_first(match=r"[GL]et.*")
    assert res.name == "Let It Be"

.. note::
  ``tree[term]`` performs a 'smart' search:

  1. If `term` is an integer, we look for the ``node_id``,
  2. else if `term` is a string or integer, we look for the ``data_id``,
  3. else if we search for ``calc_data_id(node.data) == term``.
  4. If the search return more than one match, raise ``AmbiguousMatchError``
  
  Using :meth:`~nutree.tree.Tree.find_first` or :meth:`~nutree.tree.Tree.find_all`
  may be more explicit (and faster).
    
.. note::
  ``tree.find("123")`` will search for ``calc_data_id(node.data) == "123"``.
  If a node was created with an explicit ``data_id``, this will not work.
  Instead, use ``tree.find(data_id="123")`` to search by key::
  
    tree.add("A", data_id="123")
    assert tree.find("A") is None # not found
    assert tree.find("123") is None # not found
    assert tree.find(data_id="123") is not None # works
    

Traversal
---------

.. rubric:: Iteration

Iterators are the most performant and memory efficient way to traverse the tree.

Iterators are available for the whole tree or by branch (i.e. starting at a node). 
Different travesal methods are supported. ::

    for node in tree:
        # Depth-first, pre-order by default
        ...

    for node in tree.iterator(method=IterMethod.POST_ORDER):
        ...

    # Walk a branch (not including the root node)
    for n in node:
        ...

    # Walk a branch (including the root node)
    for n in node.iterator(add_self=True):
        ...

    # Keep in mind that iterators are generators, so at times we may need 
    to materialize:
    res = list(node.iterator(add_self=True))


.. rubric:: Visit

The :meth:`~nutree.tree.Tree.visit` method is an alternative way to traverse tree 
structures with a little bit more control. 
In this case, a callback function is invoked for every node.

The callback may return (or raise) :class:`~nutree.common.SkipBranch` to 
prevent visiting of the descendant nodes. |br|
The callback may return (or raise) :class:`~nutree.common.StopTraversal` to 
stop traversal immediately. An optional return value may be passed to the 
constructor. 

::

    from nutree import Tree, SkipBranch, StopTraversal

    def callback(node, memo):
        if node.name == "secret":
            # Prevent visiting the child nodes:
            return SkipBranch
        if node.data.foobar == 17:
            raise StopTraversal("found it")

    # `res` contains the value passed to the `StopTraversal` constructor
    res = tree.visit(callback)  # res == "found it"

The `memo` argument contains an empty dict by default, which is discarded after
traversal. This may be handy to cache and pass along some calculated values 
during iteration. |br|
It is also possible to pass-in the `memo` argument, in order to access the data
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
