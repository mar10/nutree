# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt and contributors; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import pytest

from nutree import Tree


class Item:
    def __init__(self, name, price, count):
        self.name = name
        self.price = float(price)
        self.count = int(count)

    def __repr__(self):
        return f"Item<{self.name!r}, {self.price:.2f}$>"


class TestObjects:
    def setup_method(self):
        self.tree = Tree("fixture")

    def teardown_method(self):
        self.tree = None

    def test_objects(self):
        tree = self.tree

        n = tree.add("Records")
        let_it_be = Item("Let It Be", 12.34, 17)
        n.add(let_it_be)
        n.add(Item("Get Yer Ya-Ya's Out!", 23.45, 71))
        n = tree.add("Books")
        n.add(Item("The Little Prince", 3.21, 11))

        # print(f"{tree}\n" + tree.format(repr="{node.key}-{node.name}"))

        records = tree["Records"]
        assert records.name == "Records"
        print(tree.format(repr="{node.data}"))

        n = tree[let_it_be]
        assert n.data is let_it_be
        assert n.data.name == "Let It Be"
        assert n.name == repr(n.data)
        assert n.name == "Item<'Let It Be', 12.34$>"

        assert tree.find(match=".*Let It Be.*").data is let_it_be

        pony = Item("Dig A Pony", 0.99, 0)
        n.add(pony)

        get_back = Item("Get Back", 0.99, 0)
        n.add(get_back, data_id="123-456")

        print(tree.format(repr="{node.data}"))

        n = tree.find(pony)
        assert n.data is pony

        n = tree.find(get_back)
        assert n is None
        n = tree.find(data_id="123-000")
        assert n is None
        n = tree.find(data_id="123-456")
        assert n.data is get_back
        assert "Get Back" not in tree
        # FIXME: this should work
        # assert get_back in tree
        # assert "123-456" in tree

        with pytest.raises(ValueError):
            n.rename("foo")
        assert tree._self_check()
