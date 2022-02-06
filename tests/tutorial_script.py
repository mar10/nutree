# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import json

from nutree import Node, Tree


class Item:
    def __init__(self, name, price, count):
        self.name = name
        self.price = float(price)
        self.count = int(count)

    def __repr__(self):
        return f"Item<{self.name!r}, {self.price:.2f}$>"


if __name__ == "__main__":
    tree = Tree("Store")

    n = tree.add("Records")
    n.add("Let It Be")
    n.add("Get Yer Ya-Ya's Out!")
    n = tree.add("Books")
    n.add("The Little Prince")

    tree.print()

    print(tree.format(repr="{node}", style="lines32", title="My Store"))

    assert tree.count == 5

    record_node = tree["Records"]
    assert isinstance(record_node, Node)
    assert tree.first_child is record_node

    assert len(record_node.children) == 2
    assert record_node.depth == 1

    assert tree.find("Records") is record_node
    assert tree.find("records") is None

    n = record_node.first_child
    assert record_node.find("Let It Be") is n

    assert n.name == "Let It Be"
    assert n.depth == 2
    assert n.parent is record_node
    assert n.prev_sibling is None
    assert n.next_sibling.name == "Get Yer Ya-Ya's Out!"
    assert not n.children

    res = tree.find_all(match=r"[GL]et.*")
    print(res)
    assert len(res) == 2

    res = tree.find_all(match=lambda n: "y" in n.name.lower())
    assert len(res) == 1

    # Note that `find()` is an alias for `find_first()`
    res = tree.find_first(match=r"[GL]et.*")
    assert res.name == "Let It Be"
    assert tree._self_check()

    tree = Tree("multi")
    a = tree.add("A")
    a.add("a1")
    a.add("a2")
    b = tree.add("B")
    b.add("b1")
    b.add("a2")
    tree.print()
    print(tree.find("a2"))
    print(tree.find_all("a2"))

    res = tree.dumps("dict")

    res = json.dumps(tree.to_dict())
    print(res)

    res = list(tree.to_list_iter())
    print(res)
