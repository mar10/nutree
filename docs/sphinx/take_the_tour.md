# Take the Tour

_(The tour is auto-generated from 
[this jupyter notebook](https://github.com/mar10/nutree/blob/main/docs/jupyter/take_the_tour.ipynb).)_

Nutree organizes arbitrary object instances in an unobtrusive way. <br>
That means, we can add existing objects without having to derive from a common 
base class or implement a specific protocol.


```python
from nutree import Tree

tree = Tree("Hello")
tree.add("N").add("u").up(2).add("T").add("r").up().add("ee")
tree.print()
```

    Tree<'Hello'>
    ├── 'N'
    │   ╰── 'u'
    ╰── 'T'
        ├── 'r'
        ╰── 'ee'


Strings can be directly added to a tree, but in a real-world scenario we want to 
handle ordinary objects:

## Set up some sample classes and objects
Let's define a simple class hierarchy


```python
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
```

and create some instances


```python
development_dep = Department("Development")
test__dep = Department("Test")
marketing_dep = Department("Marketing")

alice = Person("Alice", 25)
bob = Person("Bob", 35)
claire = Person("Claire", 45)
dave = Person("Dave", 55)
```

Now that we have a bunch of instances, let's organize these objects in a 
hierarchical structure using _nutree_:


```python
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
```

    Tree<'Organization'>
    ├── <__main__.Department object at 0x107bd3cb0>
    │   ├── <__main__.Department object at 0x1078ea0f0>
    │   │   ╰── <__main__.Person object at 0x107902180>
    │   ╰── <__main__.Person object at 0x1079015b0>
    ├── <__main__.Department object at 0x1078eb560>
    │   ╰── <__main__.Person object at 0x109ab25a0>
    ╰── <__main__.Person object at 0x107900980>


Tree nodes store a reference to the object in the `node.data` attribute.

The nodes are formatted for display by the object's  `__repr__` implementation 
by default. <br>
We can overide this by passing an 
[f-string](https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals) 
as `repr` argument. <br>
For example `"{node.data}"` will use the data instances `__str__` method instead:


```python
tree.print(repr="{node.data}")
```

    Tree<'Organization'>
    ├── Department<Development>
    │   ├── Department<Test>
    │   │   ╰── Person<Claire (45)>
    │   ╰── Person<Bob (35)>
    ├── Department<Marketing>
    │   ╰── Person<Dave (55)>
    ╰── Person<Alice (25)>


## Access Nodes
We can use the index syntax to get the node object for a given data object:


```python
tree[alice]
```




    Node<'Person<Alice (25)>', data_id=276365464>



Note that we passed `alice` as index, which is an instance of `Person`, and received an instance of the `Node` container:


```python
from nutree import Node

assert isinstance(tree[alice], Node)
assert tree[alice].data is alice, "nodes store objects in data attribute"
```

There are other other search methods as well


```python
tree.find_all(match=lambda node: "i" in node.data.name)
```




    [Node<'Person<Claire (45)>', data_id=276365848>,
     Node<'Department<Marketing>', data_id=276360022>,
     Node<'Person<Alice (25)>', data_id=276365464>]



### Control the `data_id`

If the object instances have a natural attribute that identifies them, we can use
it instead of the default `hash()`. <br>
This improves readability and helps to (de)serialize:


```python
tree_2 = Tree("Organization", calc_data_id=lambda tree, data: str(data.guid))
dep_node_2 = tree_2.add(development_dep)
dep_node_2.add(bob)
tree_2.print(repr="{node}")
```

    Tree<'Organization'>
    ╰── Node<'Department<Development>', data_id=571ace0b-1a49-44d4-ab52-97320e945d69>
        ╰── Node<'Person<Bob (35)>', data_id=b4cbb694-a18d-420b-ad03-cda9fd0bf7f9>


now we could also search by the guid, for example


```python
tree_2.find(data_id=str(bob.guid))
```




    Node<'Person<Bob (35)>', data_id=b4cbb694-a18d-420b-ad03-cda9fd0bf7f9>



## Iteration and Searching

There are multiple methods to iterate the tree.


```python
res = []
for node in tree:  # depth-first, pre-orde traversal
    res.append(node.data.name)
print(res)
```

    ['Development', 'Test', 'Claire', 'Bob', 'Marketing', 'Dave', 'Alice']



```python
from nutree import IterMethod

res = []
for node in tree.iterator(method=IterMethod.POST_ORDER):
    res.append(node.data.name)
print(res)
```

    ['Claire', 'Test', 'Bob', 'Development', 'Dave', 'Marketing', 'Alice']



```python
def callback(node, memo):
    print(node.data.name, end=", ")


tree.visit(callback, method=IterMethod.LEVEL_ORDER)
```

    Development, Marketing, Alice, Test, Bob, Dave, Claire, 

The above traversal methods are also available for single nodes:


```python
res = [node.data.name for node in dev_node]
print(res)
```

    ['Test', 'Claire', 'Bob']


## Filter

We can create a filtered copy like so:


```python
tree_copy = tree.filtered(lambda node: isinstance(node.data, Department))
tree_copy.print(repr="{node}")
```

    Tree<"Copy of Tree<'Organization'>">
    ├── Node<'Department<Development>', data_id=276550603>
    │   ╰── Node<'Department<Test>', data_id=276359695>
    ╰── Node<'Department<Marketing>', data_id=276360022>


In-place filtering is also available:


```python
tree_copy.filter(lambda node: "m" in node.data.name.lower())
tree_copy.print(repr="{node}")
```

    Tree<"Copy of Tree<'Organization'>">
    ├── Node<'Department<Development>', data_id=276550603>
    ╰── Node<'Department<Marketing>', data_id=276360022>


## Mutation

We can add, copy, move, remove, sort, etc.

For example:


```python
alice_node = tree[alice]
bob_node = tree[bob]

bob_node.move_to(mkt_node)
alice_node.copy_to(dev_node)

tree.print(repr="{node.data}")
```

    Tree<'Organization'>
    ├── Department<Development>
    │   ├── Department<Test>
    │   │   ╰── Person<Claire (45)>
    │   ╰── Person<Alice (25)>
    ├── Department<Marketing>
    │   ├── Person<Dave (55)>
    │   ╰── Person<Bob (35)>
    ╰── Person<Alice (25)>


Read the user guide for more.

## Data IDs and Clones

In the example above, we duplicated the 'Alice' node, so we now have two 
node instances that reference the same data object, as we can see from the
identical data_id:


```python
tree.print(repr="{node}", title=False)
```

    Node<'Department<Development>', data_id=276550603>
    ├── Node<'Department<Test>', data_id=276359695>
    │   ╰── Node<'Person<Claire (45)>', data_id=276365848>
    ╰── Node<'Person<Alice (25)>', data_id=276365464>
    Node<'Department<Marketing>', data_id=276360022>
    ├── Node<'Person<Dave (55)>', data_id=278573658>
    ╰── Node<'Person<Bob (35)>', data_id=276365659>
    Node<'Person<Alice (25)>', data_id=276365464>



```python
for clone in tree.find_all(alice):
    print(f"{clone}, parent={clone.parent}")
```

    Node<'Person<Alice (25)>', data_id=276365464>, parent=None
    Node<'Person<Alice (25)>', data_id=276365464>, parent=Node<'Department<Development>', data_id=276550603>


## Special Data Types
### Plain Strings

Plain strings are hashable objects, so we can handle them the same way as any 
other object:


```python
tree_str = Tree()
a = tree_str.add("A")
a.add("a1")
a.add("a2")
tree_str.add("B")
tree_str.print()
```

    Tree<'4456612640'>
    ├── 'A'
    │   ├── 'a1'
    │   ╰── 'a2'
    ╰── 'B'


### Dictionaries

We cannot add Python `dict` objects to a tree, because nutree cannot derive
a *data_id* for unhashable types. <br>
We can handle this by passing a *data_id* explicitly to `add()` and similar 
methods, or implement a `calc_data_id` callback as shown before.

As another workaround, we can wrap it inside `DictWrapper` objects:


```python
from nutree import DictWrapper, Tree

d = {"title": "foo", "id": 1}

tree = Tree()
tree.add("A").up().add("B")
tree["A"].add(DictWrapper(d))
tree["B"].add(DictWrapper(d))
tree.print(repr="{node}")
# tree.find(d)
```

    Tree<'4457449184'>
    ├── Node<'A', data_id=-2140708064199008729>
    │   ╰── Node<"DictWrapper<{'title': 'foo', 'id': 1}>", data_id=4421803904>
    ╰── Node<'B', data_id=-6374143811137841581>
        ╰── Node<"DictWrapper<{'title': 'foo', 'id': 1}>", data_id=4421803904>


## Serialization

Read the user guide for different methods to save, load, or convert a tree
to different output formats.

## Typed Trees

The `TypedTree` subclass adds a 'kind' attribute to the nodes, and related 
methods. <br>
This allows to organize objects in directed graphs:


```python
from nutree import TypedTree

typed_tree = TypedTree()
typed_tree.add("Mia", kind="friend").add("Noah", kind="brother").up().add(
    "Olivia", kind="sister"
)
typed_tree.print()
```

    TypedTree<'4415355264'>
    ╰── friend → Mia
        ├── brother → Noah
        ╰── sister → Olivia


# Typing

Nutree comes fully typed (passing [pyright](https://microsoft.github.io/pyright/#/) 
standard checks). This improves type-safety and auto-complete features in your IDE.
