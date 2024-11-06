# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found

import pytest
from nutree import AmbiguousMatchError, Node, Tree
from nutree.common import DictWrapper, UniqueConstraintError

from . import fixture


class TestClones:
    def setup_method(self):
        self.tree = Tree("fixture")

    def teardown_method(self):
        self.tree = None

    def test_clones(self):
        """ """
        tree = fixture.create_tree_simple()

        # Add another 'a1' below 'B'
        tree["B"].add("a1")

        print(tree.format(repr="{node.data}"))

        assert tree.count == 9
        assert tree.count_unique == 8

        # Not allowed to add two clones to same parent
        with pytest.raises(UniqueConstraintError):
            tree["B"].add("a1")

        # tree[data] expects single matches
        with pytest.raises(KeyError):
            tree["not_existing"]
        with pytest.raises(AmbiguousMatchError):
            tree["a1"]

        # # Not allowed to add two clones to same parent
        with pytest.raises(UniqueConstraintError):
            tree.add("A")
        with pytest.raises(UniqueConstraintError):
            tree.add(tree["A"])

        res = tree.find("a1")
        assert res
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

    def test_clones_typed(self):
        """
        TypedTree<'fixture'>
        ├── function → func1
        │   ├── failure → fail1
        │   │   ├── cause → cause1
        │   │   ├── cause → cause2
        │   │   ├── effect → eff1
        │   │   ╰── effect → eff2
        │   ╰── failure → fail2
        ╰── function → func2
        """
        tree = fixture.create_typed_tree_simple()

        assert tree.count == 8
        assert tree.count_unique == 8

        fail1 = tree["fail1"]
        # Not allowed to add two clones to same parent
        with pytest.raises(UniqueConstraintError):
            fail1.add("cause1", kind="cause")
        fail1.add("cause1", kind="other")
        tree.print()
        assert tree.count == 9
        assert tree.count_unique == 8

    def test_dict(self):
        """ """
        tree = fixture.create_tree_simple()
        d = {"a": 1, "b": 2}
        # Add another 'a1' below 'B'
        n1 = tree["A"].add(DictWrapper(d))

        with pytest.raises(UniqueConstraintError):
            # Not allowed to add two clones to same parent
            tree["A"].add(DictWrapper(d))

        n2 = tree["B"].add(DictWrapper(d))

        tree.print(repr="{node}")

        assert tree.count == 10
        assert tree.count_unique == 9
        assert n1.data._dict is d
        assert n2.data._dict is d
        n1.data["a"] = 42
        assert n2.data["a"] == 42
        with pytest.raises(TypeError, match="unhashable type: 'dict'"):
            _ = tree.find(d)

        n = tree.find(DictWrapper(d))
        assert n
        assert n is n1
        assert n.is_clone()

        assert len(tree.find_all(DictWrapper(d))) == 2
        assert n1.get_clones() == [n2]
        assert n1.get_clones(add_self=True) == [n1, n2]

        tree._self_check()
