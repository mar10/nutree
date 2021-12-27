# ![logo](https://raw.githubusercontent.com/mar10/nutree/main/docs/nutree_48x48.png) nutree

[![Build Status](https://travis-ci.com/mar10/nutree.svg?branch=main)](https://travis-ci.com/mar10/nutree)
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

Search by name pattern, id, or object reference<br>
Handle multiple references of single objects<br>
Store plain strings or arbitrary objects<br>
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

print(tree.format())
```

```ascii
Tree<'Store'>
├── 'Records'
│   ├── 'Let It Be'
│   ╰── "Get Yer Ya-Ya's Out!"
╰── 'Books'
    ╰── 'The Little Prince'
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

[Read the Docs](https://nutree.readthedocs.io/) for more.
