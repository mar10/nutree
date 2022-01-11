# ![logo](https://raw.githubusercontent.com/mar10/nutree/main/docs/nutree_48x48.png) nutree

[![Build Status](https://travis-ci.com/mar10/nutree.svg?branch=main)](https://app.travis-ci.com/github/mar10/nutree)
[![Latest Version](https://img.shields.io/pypi/v/nutree.svg)](https://pypi.python.org/pypi/nutree/)
[![License](https://img.shields.io/pypi/l/nutree.svg)](https://github.com/mar10/nutree/blob/main/LICENSE.txt)
[![Documentation Status](https://readthedocs.org/projects/nutree/badge/?version=latest)](http://nutree.readthedocs.io/)
[![Coverage Status](https://coveralls.io/repos/github/mar10/nutree/badge.svg?branch=main)](https://coveralls.io/github/mar10/nutree?branch=main)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Released with: Yabs](https://img.shields.io/badge/released%20with-yabs-yellowgreen)](https://github.com/mar10/yabs)
[![StackOverflow: nutree](https://img.shields.io/badge/StackOverflow-nutree-blue.svg)](https://stackoverflow.com/questions/tagged/nutree)

> Elegant trees for primates&trade;

_Nutree_ is a Python library for tree data structures with an intuitive,
yet powerful, API.

**Nutree Facts**

Handle multiple references of single objects ('clones')<br>
Search by name pattern, id, or object reference<br>
Unobtrusive handling of arbitrary objects<br>
Nodes can be plain strings or objects<br>
Different traversal methods<br>
(De)Serialize to JSON<br>
Pretty print<br>
Navigation<br>
Filtering<br>

<!-- 
Compare two trees and calculate patches (NYI)<br>
Export to different formats (NYI)<br>
Set-like operations (NYI)<br>
-->

**Example**

A simple tree, with text nodes

```py
from nutree import Tree, Node

tree = Tree("Store")

n = tree.add("Records")

n.add("Let It Be")
n.add("Get Yer Ya-Ya's Out!")

n = tree.add("Books")
n.add("The Little Prince")

tree.print()
```

```ascii
Tree<'Store'>
├─── 'Records'
│    ├─── 'Let It Be'
│    ╰─── "Get Yer Ya-Ya's Out!"
╰─── 'Books'
     ╰─── 'The Little Prince'
```

Tree nodes wrap the data and also expose methods for navigation, searching,
iteration, ...

```py
records_node = tree["Records"]
assert isinstance(records_node, Node)
assert records_node.name == "Records"

print(records_node.first_child)
```

```ascii
Node<'Let It Be', data_id=510268653885439170>
```

Nodes may be strings or arbitrary objects:

```py
alice = Person("Alice", age=23, guid="{123-456}")
tree.add(alice)

# Lookup nodes by object, data_id, name pattern, ...
assert isinstance(tree[alice].data, Person)

del tree[alice]
```

[Read the Docs](https://nutree.readthedocs.io/) for more.
