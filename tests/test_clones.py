# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import pytest

from nutree import AmbigousMatchError, Node, Tree

from . import fixture


class TestClones:
    def setup_method(self):
        self.tree = Tree("fixture")

    def teardown_method(self):
        self.tree = None

    def test_clones(self):
        """ """
        tree = fixture.create_tree()

        # Add another 'a1' below 'B'
        tree["B"].add("a1")

        print(tree.format(repr="{node.data}"))

        assert tree.count == 9
        assert tree.count_data == 8

        # Not allowed to add two clones to same parent
        # with pytest.raises(UniqueConstraintError):
        #     tree["B"].add("a1")

        # tree[data] expects single matches
        with pytest.raises(KeyError):
            tree["not_existing"]
        with pytest.raises(AmbigousMatchError):
            tree["a1"]

        # # Not allowed to add two clones to same parent
        # with pytest.raises(UniqueConstraintError):
        #     tree.add("A")
        # with pytest.raises(UniqueConstraintError):
        #     tree.add(tree["A"])

        res = tree.find("a1")
        assert res.data == "a1"
        assert res.is_clone()
        assert len(res.get_clones()) == 1
        assert len(res.get_clones(add_self=True)) == 2

        res = tree.find("not_existing")
        assert res is None

        assert not tree["a2"].is_clone()

        res = tree.find_all("a1")

        assert res[0].is_clone()
        assert res[1].is_clone()

        assert len(res) == 2
        assert isinstance(res[0], Node)
        assert res[0] == res[1]  # nodes are equal
        assert res[0] == res[1].data  # nodes are equal
        assert res[0] is not res[1]  # but not identical
        assert res[0].data == res[1].data  # node.data is equal
        assert res[0].data is res[1].data  # and identical

        res = tree.find_all("not_existing")
        assert res == []

        assert tree._self_check()
