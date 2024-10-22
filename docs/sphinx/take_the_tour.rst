Take the Tour
=============

*(The tour is auto-generated from*\ `this jupyter
notebook <https://github.com/mar10/nutree/blob/main/docs/jupyter/take_the_tour.ipynb>`__\ *.)*

Nutree organizes arbitrary object instances in an unobtrusive way. That
means, we can add existing objects without having to derive from a
common base class or implement a specific protocol.

.. code:: ipython3

    from nutree import Tree
    
    tree = Tree("Hello")
    tree.add("N").add("u").up(2).add("T").add("r").up().add("ee")
    tree.print()


.. parsed-literal::

    Tree<'Hello'>
    ├── 'N'
    │   ╰── 'u'
    ╰── 'T'
        ├── 'r'
        ╰── 'ee'


Strings can be added to a tree, but in a real-world scenario we want
need to handle ordinary objects:

Setup some sample classes and objects
-------------------------------------

Let’s define a simple class hierarchy

.. code:: ipython3

    import uuid
    
    
    class Department:
        def __init__(self, name: str):
            self.guid = uuid.uuid4()
            self.name = name
    
        def __str__(self):
            return f"Department<{self.name}>"
    
    
    class Person:
        def __init__(self, name: str, age: int):
            self.guid = uuid.uuid4()
            self.name = name
            self.age = age
    
        def __str__(self):
            return f"Person<{self.name} ({self.age})>"

and create some instances

.. code:: ipython3

    development_dep = Department("Development")
    test__dep = Department("Test")
    marketing_dep = Department("Marketing")
    
    alice = Person("Alice", 25)
    bob = Person("Bob", 35)
    claire = Person("Claire", 45)
    dave = Person("Dave", 55)

Now that we have a bunch of instances, let’s organize these objects in a
hierarchical structure using *nutree*:

.. code:: ipython3

    from nutree import Tree
    
    tree = Tree("Organization")
    
    dev_node = tree.add(development_dep)
    test_node = dev_node.add(test__dep)
    mkt_node = tree.add(marketing_dep)
    
    tree.add(alice)
    dev_node.add(bob)
    test_node.add(claire)
    mkt_node.add(dave)
    
    tree.print()


.. parsed-literal::

    Tree<'Organization'>
    ├── <__main__.Department object at 0x109247ad0>
    │   ├── <__main__.Department object at 0x1091cede0>
    │   │   ╰── <__main__.Person object at 0x109247770>
    │   ╰── <__main__.Person object at 0x109247b00>
    ├── <__main__.Department object at 0x109245820>
    │   ╰── <__main__.Person object at 0x109247e00>
    ╰── <__main__.Person object at 0x1092477a0>


Tree nodes store a reference to the object in the ``node.data``
attribute.

The nodes are formatted for display by the object’s ``__repr__``
implementation by default. We can overide this by passing an
`f-string <https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals>`__
as ``repr`` argument. For example ``"{node.data}"`` will use the data
instances ``__str__`` method instead:

.. code:: ipython3

    tree.print(repr="{node.data}")


.. parsed-literal::

    Tree<'Organization'>
    ├── Department<Development>
    │   ├── Department<Test>
    │   │   ╰── Person<Claire (45)>
    │   ╰── Person<Bob (35)>
    ├── Department<Marketing>
    │   ╰── Person<Dave (55)>
    ╰── Person<Alice (25)>


Access Nodes
------------

We can use the index syntax to get the node object for a given data
object:

.. code:: ipython3

    tree[alice]




.. parsed-literal::

    Node<'Person<Alice (25)>', data_id=278022010>



.. code:: ipython3

    assert tree[alice].data is alice, "nodes store objects in data attribute"

Iteration and Searching
-----------------------

There are multiple methods to iterate the tree.

.. code:: ipython3

    res = []
    for node in tree:  # depth-first, pre-orde traversal
        res.append(node.data.name)
    print(res)


.. parsed-literal::

    ['Development', 'Test', 'Claire', 'Bob', 'Marketing', 'Dave', 'Alice']


.. code:: ipython3

    from nutree import IterMethod
    
    res = []
    for node in tree.iterator(method=IterMethod.POST_ORDER):
        res.append(node.data.name)
    print(res)


.. parsed-literal::

    ['Claire', 'Test', 'Bob', 'Development', 'Dave', 'Marketing', 'Alice']


.. code:: ipython3

    tree.visit(lambda node, memo: print(node.data.name), method=IterMethod.LEVEL_ORDER)


.. parsed-literal::

    Development
    Marketing
    Alice
    Test
    Bob
    Dave
    Claire


The above traversal methods are also available for single nodes:

.. code:: ipython3

    res = [node.data.name for node in dev_node]
    print(res)


.. parsed-literal::

    ['Test', 'Claire', 'Bob']


Filter
------

.. code:: ipython3

    tree_2 = tree.copy(predicate=lambda node: isinstance(node.data, Department))
    tree_2.print(repr="{node}")


.. parsed-literal::

    Tree<"Copy of Tree<'Organization'>">
    ├── Node<'Department<Development>', data_id=278022061>
    │   ├── Node<'Department<Development>', data_id=278022061>
    │   ╰── Node<'Department<Test>', data_id=277991134>
    │       ╰── Node<'Department<Test>', data_id=277991134>
    ╰── Node<'Department<Marketing>', data_id=278021506>
        ╰── Node<'Department<Marketing>', data_id=278021506>


Mutation
--------

.. code:: ipython3

    bob_node = tree[bob]
    # bob_node.move_to(marketing_dep_node)
    tree.print()


::


    ---------------------------------------------------------------------------

    AttributeError                            Traceback (most recent call last)

    Cell In[120], line 1
    ----> 1 bob.move_to()
          2 tree.print()


    AttributeError: 'Person' object has no attribute 'move_to'


Data IDs and Clones
-------------------

.. code:: ipython3

    tree.print(repr="{node}", title=False)


.. parsed-literal::

    Node<'Department<Development>', data_id=278005278>
    ├── Node<'Department<Test>', data_id=278005584>
    │   ╰── Node<'Person<Claire (45)>', data_id=278021425>
    ╰── Node<'Person<Bob (35)>', data_id=278021428>
    Node<'Department<Marketing>', data_id=277460240>
    ╰── Node<'Person<Dave (55)>', data_id=278021167>
    Node<'Person<Alice (25)>', data_id=277460774>


Special Data Types
------------------

Plain Strings
~~~~~~~~~~~~~

We can add simple string objects the same way as any other object

.. code:: ipython3

    tree_str = Tree()
    a = tree_str.add("A")
    a.add("a1")
    a.add("a2")
    tree_str.add("B")
    tree_str.print()


.. parsed-literal::

    Tree<'4448341168'>
    ├── 'A'
    │   ├── 'a1'
    │   ╰── 'a2'
    ╰── 'B'


Dictionaries
~~~~~~~~~~~~

We cannot add Python ``dict`` objects to a tree, because nutree cannot
derive a *data_id* for unhashable types. A a workaround, we can wrap it
inside ``DictWrapper`` objects:

.. code:: ipython3

    from nutree import DictWrapper, Tree
    
    d = {"title": "foo", "id": 1}
    
    tree = Tree()
    tree.add("A").up().add("B")
    tree["A"].add(DictWrapper(d))
    tree["B"].add(DictWrapper(d))
    tree.print(repr="{node}")
    # tree.find(d)


.. parsed-literal::

    Tree<'4448343424'>
    ├── Node<'A', data_id=-8659698137174932031>
    │   ╰── Node<"DictWrapper<{'title': 'foo', 'id': 1}>", data_id=4448332800>
    ╰── Node<'B', data_id=-1229858467403030929>
        ╰── Node<"DictWrapper<{'title': 'foo', 'id': 1}>", data_id=4448332800>


Serialization
-------------

.. code:: ipython3

    tree.to_dict_list()
    # tree.to_dict_list(mapper=lambda node, data: node.data.name)




.. parsed-literal::

    [{'data': 'A',
      'children': [{'data': "DictWrapper<{'title': 'foo', 'id': 1}>"}]},
     {'data': 'B',
      'children': [{'data': "DictWrapper<{'title': 'foo', 'id': 1}>"}]}]



.. code:: ipython3

    list(tree.to_list_iter())




.. parsed-literal::

    [(0, 'A'), (1, {}), (0, 'B'), (3, 2)]



.. code:: ipython3

    t = Tree._from_list([(0, "A"), (0, "B"), (1, "C"), (0, "D"), (3, "E")])
    print(t.format())


.. parsed-literal::

    Tree<'4448342032'>
    ├── 'A'
    │   ╰── 'C'
    │       ╰── 'E'
    ├── 'B'
    ╰── 'D'


.. code:: mermaid

   graph LR;
       A--> B & C & D;
       B--> A & E;
       C--> A & E;
       D--> A & E;
       E--> B & C & D;

Advanced
--------

Chaining
~~~~~~~~

Some methods return a node instance, so we can chain calls. This allows
for a more compact code and avoids some temporary variables:

.. code:: ipython3

    Tree().add("A").add("a1").up().add("a2").up(2).add("B").tree.print(title=False)


.. parsed-literal::

    'A'
    ├── 'a1'
    ╰── 'a2'
    'B'


