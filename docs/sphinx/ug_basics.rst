------
Basics
------

.. py:currentmodule:: nutree


Add Nodes
---------

Nodes are usually created by adding a new data instance to a parent ::

   from nutree import Tree, Node

   tree = Tree("Store")

   n = tree.add("Records")

   n.add("Let It Be")
   n.add("Get Yer Ya-Ya's Out!")

   n = tree.add("Books")
   n.add("The Little Prince")

   tree.print()

::

   Tree<'Store'>
   ├── 'Records'
   │   ├── 'Let It Be'
   │   ╰── "Get Yer Ya-Ya's Out!"
   ╰── 'Books'
       ╰── 'The Little Prince'


Info and Navigation
-------------------

::

    assert tree.count == 5
    assert tree.

    records_node = tree["Records"]
    assert tree.first_child is records_node

    assert len(records_node.children) == 2
    assert records_node.depth == 1

    assert tree.find("Records") is records_node
    assert tree.find("records") is None

    n = records_node.first_child
    assert records_node.find("Let It Be") is n

    assert n.name == "Let It Be"
    assert n.depth == 2
    assert n.parent is records_node
    assert n.prev_sibling is None
    assert n.next_sibling.name == "Get Yer Ya-Ya's Out!"
    assert not n.children

    res = tree.find_all(match=r"[GL]et.*")
    print(res)
    assert len(res) == 2

    res = tree.find_all(match=lambda n: "y" in n.name.lower())
    assert len(res) == 1

    res = tree.find_first(match=r"[GL]et.*")
    assert res.name == "Let It Be"


Iteration
---------

Iterators are available for the hole tree or by branch. Different travesal
methods are supported ::

    for node in tree:
        # Depth-first, pre-order by default
        ...

    for node in tree.iterator(method=IterMethod.POST_ORDER):
        ...

    # Walk a branch, starting at a distinct node
    res = list(node.iterator(add_self=True))
