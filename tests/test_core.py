# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt and contributors; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import re

import pytest

from nutree import AmbigousMatchError, IterMethod, Node, Tree
from nutree.common import SkipChildren, StopTraversal

from . import fixture


class TestBasics:
    def test_add_child(self):
        tree = Tree("fixture")
        assert not tree, "empty tree is falsy"
        assert tree.count == 0
        assert len(tree) == 0
        assert f"{tree}" == "Tree<'fixture'>"
        assert f"{tree!r}" == "Tree<'fixture'>"

        records = tree.add_child("Records")
        assert isinstance(records, Node)

        # Check read-only prperties
        with pytest.raises(AttributeError):
            records.name = "not allowed"
        with pytest.raises(AttributeError):
            records.parent = "not allowed"

        records.add_child("Let It Be")
        records.add_child("Get Yer Ya-Ya's Out!")

        books = tree.add_child("Books")
        books.add_child("The Little Prince")

        assert fixture.check_content(
            tree,
            """
            Tree<'fixture'>
            +- Records
            |  +- Let It Be
            |  `- Get Yer Ya-Ya's Out!
            `- Books
               `- The Little Prince
            """,
        )


class TestNavigate:
    def setup_method(self):
        tree = Tree("fixture")
        self.tree: Tree = tree
        n = tree.add("Records")
        n.add("Let It Be")
        n.add("Get Yer Ya-Ya's Out!")
        n = tree.add("Books")
        n.add("The Little Prince")

    def teardown_method(self):
        self.tree = None

    def test_basic(self):
        tree = self.tree

        assert tree.count == 5

        print(tree.format(repr="{node.data}"))
        tree.print()

        records = tree["Records"]
        assert isinstance(records, Node)

        assert records.tree is records._tree

        assert tree.find(data="Records") is records
        # TODO: hashes are salted in Py3, so we can't assume stable keys in tests
        # assert tree.find(data_id="1862529381406879915") is records
        assert tree.find(data_id=records.data_id) is records

        assert records.name == "Records"
        assert f"{records.data}" == "Records"
        assert f"{records}".startswith("Node<'Records', data_id=")
        assert f"{records!r}".startswith("Node<'Records', data_id=")

        assert records.is_top()
        assert records.is_first_sibling()
        assert records.next_sibling.is_last_sibling()
        assert records.last_child.is_leaf()

        assert records.count_descendants() == 2
        assert records.count_descendants(leaves_only=True) == 2

        assert tree.first_child is records
        assert tree.last_child.name == "Books"

        assert records.parent is None
        assert records.first_child.parent is records
        assert records.first_child.name == "Let It Be"
        assert records.first_child.next_sibling.name == "Get Yer Ya-Ya's Out!"
        assert records.last_child.name == "Get Yer Ya-Ya's Out!"
        assert records.last_child.prev_sibling.name == "Let It Be"
        assert records.last_child.next_sibling is None
        assert records.first_sibling is records
        assert records.prev_sibling is None

        assert records.next_sibling.name == "Books"
        assert records.last_sibling.name == "Books"

        assert len(records.get_siblings()) == 1
        assert len(records.get_siblings(add_self=True)) == 2
        assert len(records.get_siblings(add_self=False)) == 1

        # assert tree.last_child is tree["The Little Prince"]

        assert len(records.children) == 2
        assert records.depth == 1
        with pytest.raises(NotImplementedError):
            assert tree == tree  # __eq__ not implemented

        let_it_be = records.first_child
        assert records.find("Let It Be") is let_it_be
        assert let_it_be.name == "Let It Be"
        assert let_it_be.depth == 2
        assert let_it_be.parent is records

        assert let_it_be.has_children() is False
        assert not let_it_be.children

        assert let_it_be.get_path(repr="{node.data}") == "/Records/Let It Be"
        assert let_it_be.get_path(repr="{node.data}", add_self=False) == "/Records"

        assert let_it_be.get_top() is records

        assert tree._self_check()

    def test_statistics(self):
        """
        Tree<'fixture'>
        ├── A
        │   ├── a1
        │   │   ├── a11
        │   │   ╰── a12
        │   ╰── a2
        ╰── B
            ╰── b1
                ╰── b11
        """
        tree = fixture.create_tree()

        assert len(tree) == 8
        assert tree.count == 8
        assert tree.calc_height() == 3

        assert tree["a12"].calc_height() == 0
        assert tree["a1"].calc_height() == 1
        assert tree["a1"].calc_depth() == 2
        assert tree["A"].count_descendants() == 4
        assert tree["A"].count_descendants(leaves_only=True) == 3
        assert tree["A"].calc_depth() == 1
        assert tree["A"].calc_height() == 2

    def test_relations(self):
        """
        Tree<'fixture'>
        ├── A
        │   ├── a1
        │   │   ├── a11
        │   │   ╰── a12
        │   ╰── a2
        ╰── B
            ╰── b1
                ╰── b11
        """
        tree = fixture.create_tree()

        assert tree["a11"].get_top() is tree["A"]
        assert not tree["a1"].is_top()
        assert tree["B"].get_top() is tree["B"]
        assert tree["B"].is_top()
        assert not tree["a1"].is_leaf()
        assert tree["a2"].is_leaf()

        assert tree["a1"].is_descendant_of(tree["A"])
        assert tree["a11"].is_descendant_of(tree["A"])
        assert tree["a11"].is_descendant_of(tree["a1"])
        assert not tree["a1"].is_descendant_of(tree["a1"])
        assert not tree["a1"].is_descendant_of(tree["a11"])
        assert not tree["B"].is_descendant_of(tree["a11"])

        assert tree["a1"].is_ancestor_of(tree["a12"])
        assert tree["B"].is_ancestor_of(tree["b11"])
        assert not tree["B"].is_ancestor_of(tree["A"])

        assert tree["a11"].get_common_ancestor(tree["a2"]) is tree["A"]
        assert tree["b11"].get_common_ancestor(tree["a11"]) is None

        assert tree["a11"].get_index() == 0
        assert tree["a12"].get_index() == 1

    def test_data_id(self):
        """
        Tree<'fixture'>
        ├── A
        │   ├── a1
        │   │   ├── a11
        │   │   ╰── a12
        │   ╰── a2
        ╰── B
            ├── a1  <-- Clone
            ╰── b1
                ╰── b11
        """
        tree = fixture.create_tree()
        tree["B"].prepend_child("a1")

        print(tree.format(repr="{node.data}"))

        tree["A"].rename("new_A")

        assert fixture.check_content(
            tree,
            """
            Tree<'fixture'>
            +- new_A
            |  +- a1
            |  |  +- a11
            |  |  `- a12
            |  `- a2
            `- B
               +- a1
               `- b1
                  `- b11
            """,
        )
        assert tree._self_check()

        # Reset tree
        tree = fixture.create_tree()
        tree["B"].prepend_child("a1")

        with pytest.raises(AmbigousMatchError):  # not allowed for clones
            tree.find_first("a1").rename("new_a1")

        with pytest.raises(ValueError):  # missing args
            tree.find_first("a1").set_data(None)

        # Only rename first occurence:
        tree.find_first("a1").set_data("new_a1", with_clones=False)

        assert fixture.check_content(
            tree,
            """
            Tree<'fixture'>
            +- A
            |  +- new_a1
            |  |  +- a11
            |  |  `- a12
            |  `- a2
            `- B
               +- a1
               `- b1
                  `- b11
            """,
        )
        assert tree._self_check()

        # Reset tree
        tree = fixture.create_tree()
        tree["B"].prepend_child("a1")

        # Rename all occurences:
        tree.find_first("a1").set_data("new_a1", with_clones=True)

        assert fixture.check_content(
            tree,
            """
            Tree<'fixture'>
            +- A
            |  +- new_a1
            |  |  +- a11
            |  |  `- a12
            |  `- a2
            `- B
               +- new_a1
               `- b1
                  `- b11
            """,
        )
        assert tree._self_check()

    def test_search(self):
        tree = self.tree

        records = tree["Records"]

        with pytest.raises(KeyError):
            tree.__getitem__("Let It Boo")

        n = tree["Let It Be"]
        assert n.name == "Let It Be"

        # Search by data
        assert tree.find("Let It Be") is n
        assert tree.find("Let It Boo") is None

        assert tree.find_first(node_id=records.node_id) is records

        assert "Let It Be" in tree
        assert "Let It Boo" not in tree
        assert "Let" not in tree

        # Search by data.name
        assert tree.find(match="Let It Boo") is None
        assert tree.find(match="Let") is None
        assert tree.find(match="Let.*") is n
        assert tree.find(match="It") is None
        assert tree.find(match="It.*") is None
        assert tree.find(match=".*It") is None
        assert tree.find(match=".*It.*") is n
        assert tree.find(match="let it be") is None  # case sensitive!
        assert tree.find(match=("let it be", re.I)) is n  # case insensitive!
        assert tree.find(match="Let It Be") is n

        assert records.find(match="Let It Be") is n
        assert records.find(match=".* It Be") is n
        assert records.find(match="It Be") is None

        # Search multiple
        assert tree.find_all(match="Let It Be") == [n]
        assert tree.find_all(match="Let It Boo") == []
        assert records.find_all(match="Let It Be") == [n]
        assert records.find_all(match="Let It Boo") == []

        res = tree.find_all(match=r"[GL]et.*")
        assert len(res) == 2
        assert n in res
        assert res == records.find_all(match=r"[GL]et.*")

        res = tree.find_all(match=r"[GL]et.*", max_results=1)
        assert len(res) == 1
        assert n in res

        res = tree.find_all(match=lambda n: "y" in n.name.lower())
        assert len(res) == 1

    def test_clear(self):
        tree = fixture.create_tree()

        assert tree.count == 8
        assert tree
        tree.clear()
        assert not tree
        assert len(tree) == 0
        assert tree._self_check()


class TestSort:
    def test_reverse_deep(self):
        tree = fixture.create_tree()

        tree.sort(reverse=True)

        assert fixture.check_content(
            tree.format(repr="{node.name}"),
            """\
            Tree<*>
            ├── B
            │   ╰── b1
            │       ╰── b11
            ╰── A
                ├── a2
                ╰── a1
                    ├── a12
                    ╰── a11
        """,
        )


class TestFormat:
    def test_format(self):
        tree = fixture.create_tree()

        assert fixture.check_content(
            tree.format(repr="{node.name}"),
            """\
            Tree<'fixture'>
            ├── A
            │   ├── a1
            │   │   ├── a11
            │   │   ╰── a12
            │   ╰── a2
            ╰── B
                ╰── b1
                    ╰── b11
        """,
        )

        assert fixture.check_content(
            tree.format(repr="{node.name}", style="ascii32"),
            """\
            Tree<'fixture'>
            +- A
            |  +- a1
            |  |  +- a11
            |  |  `- a12
            |  `- a2
            `- B
               `- b1
                  `- b11
            """,
        )

        assert fixture.check_content(
            tree.format(repr="{node.data}", title=False),
            """\
            A
            ├── a1
            │   ├── a11
            │   ╰── a12
            ╰── a2
            B
            ╰── b1
                ╰── b11
            """,
        )

        assert fixture.check_content(
            tree["A"].format(repr="{node.data}"),
            """\
            A
            ├── a1
            │   ├── a11
            │   ╰── a12
            ╰── a2
            """,
        )

        assert fixture.check_content(
            tree["A"].format(repr="{node.data}", add_self=False),
            """\
            a1
            ├── a11
            ╰── a12
            a2
            """,
        )

        assert fixture.check_content(
            tree.format(repr="{node.path}", style="list"),
            """\
            /A
            /A/a1
            /A/a1/a11
            /A/a1/a12
            /A/a2
            /B
            /B/b1
            /B/b1/b11
            """,
        )

        assert fixture.check_content(
            tree.format(repr="{node.path}", style="list", join=","),
            "/A,/A/a1,/A/a1/a11,/A/a1/a12,/A/a2,/B,/B/b1,/B/b1/b11",
        )


class TestTraversal:
    def test_iter(self):
        """
        Tree<'fixture'>
        ├── A
        │   ├── a1
        │   │   ├── a11
        │   │   ╰── a12
        │   ╰── a2
        ╰── B
            ╰── b1
                ╰── b11
        """
        tree = fixture.create_tree()

        # print(tree.format(repr="{node.data}"))

        s = ",".join(n.data for n in tree)
        assert s == "A,a1,a11,a12,a2,B,b1,b11"

        s = ",".join(n.data for n in tree.iterator(IterMethod.PRE_ORDER))
        assert s == "A,a1,a11,a12,a2,B,b1,b11"

        s = ",".join(n.data for n in tree.iterator(IterMethod.POST_ORDER))
        assert s == "a11,a12,a1,a2,A,b11,b1,B"

        s = ",".join(n.data for n in tree.iterator(IterMethod.LEVEL_ORDER))
        assert s == "A,B,a1,a2,b1,a11,a12,b11"

    def test_visit(self):
        """
        Tree<'fixture'>
        ├── A
        │   ├── a1
        │   │   ├── a11
        │   │   ╰── a12
        │   ╰── a2
        ╰── B
            ╰── b1
                ╰── b11
        """
        tree = fixture.create_tree()

        res = []

        def cb(node, memo):
            res.append(node.name)

        tree.visit(cb)
        assert ",".join(res) == "A,a1,a11,a12,a2,B,b1,b11"

        res = []
        tree.visit(cb, method=IterMethod.POST_ORDER)
        assert ",".join(res) == "a11,a12,a1,a2,A,b11,b1,B"

        res = []
        tree.visit(cb, method=IterMethod.LEVEL_ORDER)
        assert ",".join(res) == "A,B,a1,a2,b1,a11,a12,b11"

        res = []

        def cb(node, memo):
            res.append(node.name)
            if node.name == "a1":
                return SkipChildren
            if node.name == "b1":
                raise StopTraversal("Found b1")

        res_2 = tree.visit(cb)

        assert res_2 == "Found b1"
        assert ",".join(res) == "A,a1,a2,B,b1"


class TestMutate:
    def test_add(self):
        tree = fixture.create_tree()
        b = tree["B"]
        a11 = tree["a11"]
        b.prepend_child(a11)

        a1 = tree["a1"]
        a1.prepend_sibling("pre_a1")
        a1.append_sibling("post_a1")
        a1.add_child("before_idx_1", before=1)
        a1.append_child("append_child")

        assert fixture.check_content(
            tree,
            """
            Tree<*>
            +- A
            |  +- pre_a1
            |  +- a1
            |  |  +- a11
            |  |  +- before_idx_1
            |  |  +- a12
            |  |  `- append_child
            |  +- post_a1
            |  `- a2
            `- B
               +- a11
               `- b1
                  `- b11
            """,
        )

    def test_delete(self):
        """
        Tree<'fixture'>
        +- A
        |   +- a1
        |   |   +- a11
        |   |   `- a12
        |   `- a2
        `- B
            `- b1
                `- b11
        """
        tree = fixture.create_tree()

        print(tree.format(repr="{node.data}", style="round43"))

        tree["a11"].remove()

        del tree["b1"]

        assert fixture.check_content(
            tree,
            """
            Tree<'fixture'>
            +- A
            |  +- a1
            |  |  `- a12
            |  `- a2
            `- B
            """,
        )
        assert tree._self_check()

        tree["A"].remove_children()
        assert fixture.check_content(
            tree,
            """
            Tree<'fixture'>
            +- A
            `- B
            """,
        )
        print(tree.format(repr="{node.data}"))
        assert tree._self_check()

    def test_move(self):
        """
        Tree<'fixture'>
        +- A
        |   +- a1
        |   |   +- a11
        |   |   `- a12
        |   `- a2
        `- B
            `- b1
                `- b11
        """
        tree = fixture.create_tree()
        a11 = tree["a11"]
        b1 = tree["b1"]

        print(tree.format(repr="{node.data}"))
        a11.move(b1)

        assert fixture.check_content(
            tree,
            """
            Tree<'fixture'>
            +- A
            |  +- a1
            |  |  `- a12
            |  `- a2
            `- B
               `- b1
                  +- b11
                  `- a11
            """,
        )
        assert tree._self_check()


class TestCopy:
    def test_copy(self):
        """ """
        tree_1 = fixture.create_tree()

        tree_2 = tree_1.copy()
        assert tree_1.count == tree_2.count
        assert tree_2.name == "Copy of Tree<'fixture'>"

        tree_2 = tree_1.copy()

        assert tree_1.count == tree_2.count
        assert tree_1["a11"] == tree_2["a11"]
        assert tree_1["a11"].data is tree_2["a11"].data

        assert fixture.trees_equal(tree_1, tree_2)
        # assert fixture.canonical_repr(tree_1) == fixture.canonical_repr(tree_2)

        assert tree_1._self_check()
        assert tree_2._self_check()

    def test_as_tree(self):
        tree = fixture.create_tree()

        subtree = tree["a1"].to_tree()
        assert fixture.check_content(
            subtree,
            """
            Tree<'fixture'>
            `- a1
               +- a11
               `- a12
            """,
        )
        assert subtree._self_check()

        subtree = tree["A"].to_tree(add_self=False)
        assert fixture.check_content(
            subtree,
            """
            Tree<'fixture'>
            +- a1
            |  +- a11
            |  `- a12
            `- a2
            """,
        )
        assert subtree._self_check()
