# ![logo](https://raw.githubusercontent.com/mar10/nutree/main/docs/nutree_48x48.png) nutree

[![Latest Version](https://img.shields.io/pypi/v/nutree.svg)](https://pypi.python.org/pypi/nutree/)
[![Tests](https://github.com/mar10/nutree/actions/workflows/tests.yml/badge.svg)](https://github.com/mar10/nutree/actions/workflows/tests.yml)
[![codecov](https://codecov.io/github/mar10/nutree/branch/main/graph/badge.svg?token=9xmAFm8Icl)](https://codecov.io/github/mar10/nutree)
[![License](https://img.shields.io/pypi/l/nutree.svg)](https://github.com/mar10/nutree/blob/main/LICENSE.txt)
[![Documentation Status](https://readthedocs.org/projects/nutree/badge/?version=latest)](http://nutree.readthedocs.io/)
[![Downloads](https://img.shields.io/pypi/dm/nutree.svg)](https://pypi.python.org/pypi/nutree/)

<!-- [![Released with: Yabs](https://img.shields.io/badge/released%20with-yabs-yellowgreen)](https://github.com/mar10/yabs) -->
<!-- [![StackOverflow: nutree](https://img.shields.io/badge/StackOverflow-nutree-blue.svg)](https://stackoverflow.com/questions/tagged/nutree) -->

> _Nutree_ lets you organize and query arbitrary Python objects as a tree — with clones, diffing, and graph export built in.

Trees and nodes behave like familiar Python containers wherever that makes sense — len(tree) counts nodes, 
iterating walks the tree depth-first, and in tests membership. 
Lookup (tree[value]) matches by id or by the wrapped data, not by position, 
since a tree has no natural order. 

**Nutree Facts**

<a href="https://nutree.readthedocs.io/en/latest/ug_clones.html">Handle multiple references of single objects ('clones')</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_search_and_navigate.html#searching">Search by name pattern, id, or object reference</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_diff.html#diff-and-merge">Compare two trees and calculate patches</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_objects.html#objects">Unobtrusive handling of arbitrary objects</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_graphs.html#save-dot">Save as DOT file and graphwiz diagram</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_objects.html#objects">Nodes can be plain strings or objects</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_serialize.html#serialize">(De)Serialize to (compressed) JSON</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_graphs.html#save-mermaid">Save as Mermaid flow diagram</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_search_and_navigate.html#traversal">Multiple traversal methods</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_randomize.html#randomize">Generate random trees</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_graphs.html#save-rdf">Convert to RDF graph</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/rg_modules.html#api-reference">Fully type annotated</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_graphs.html#typed-tree">Typed child nodes</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_advanced.html#meta-data">Memory efficient</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_pretty_print.html#pretty-print">Pretty print</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_search_and_navigate.html#navigate">Navigation</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_mutation.html#mutation">Filtering</a> <br>
<a href="https://nutree.readthedocs.io/en/latest/ug_benchmarks.html">Fast</a> <br>

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

print(records_node.first_child())
```

```ascii
Node<'Let It Be', data_id=510268653885439170>
```

Nodes can holdarbitrary objects (not just strings):

```py
alice = Person("Alice", age=23, guid="{123-456}")
tree.add(alice)

# Lookup nodes by object, data_id, name pattern, ...
alice_node = tree[alice]
assert isinstance(alice_node.data, Person)

del tree[alice]
```

[Read the Docs](https://nutree.readthedocs.io/) for more.
