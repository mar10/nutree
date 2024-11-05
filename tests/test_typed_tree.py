# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found
# pyright: reportOptionalMemberAccess=false

import re
from pathlib import Path

from nutree.typed_tree import ANY_KIND, TypedNode, TypedTree, _SystemRootTypedNode

from . import fixture


class TestTypedTree:
    # def met
    def test_add_child(self):
        tree = TypedTree("fixture")

        # --- Empty tree
        assert not tree, "empty tree is falsy"
        assert tree.count == 0
        assert len(tree) == 0
        assert f"{tree}" == "TypedTree<'fixture'>"
        assert isinstance(tree._root, _SystemRootTypedNode)

        # ---
        func = tree.add("func1", kind="function")

        assert isinstance(func, TypedNode)
        print(f"{func}")
        assert (
            re.sub(r"data_id=[-\d]+>", "data_id=*>", f"{func}")
            == "TypedNode<kind=function, func1, data_id=*>"
        )

        fail1 = func.add("fail1", kind="failure")

        fail1.add("cause1", kind="cause")
        fail1.add("cause2", kind="cause")

        fail1.add("eff1", kind="effect")
        fail1.add("eff2", kind="effect")

        func.add("fail2", kind="failure")

        func2 = tree.add("func2", kind="function")

        assert fixture.check_content(
            tree,
            """
            TypedTree<*>
            +- function → func1
            |  +- failure → fail1
            |  |  +- cause → cause1
            |  |  +- cause → cause2
            |  |  +- effect → eff1
            |  |  `- effect → eff2
            |  `- failure → fail2
            `- function → func2
           """,
        )
        assert tree.last_child(ANY_KIND).name == "func2"

        assert len(fail1.children) == 4
        assert fail1.get_children(kind=ANY_KIND) == fail1.children

        assert len(fail1.get_children(kind="cause")) == 2
        assert fail1.get_children(kind="unknown") == []

        assert fail1.has_children(kind="unknown") is False
        assert fail1.has_children(kind=ANY_KIND) is True
        assert fail1.has_children(kind="cause") is True

        assert fail1.first_child(kind="cause").name == "cause1"
        assert fail1.first_child(kind="effect").name == "eff1"
        assert fail1.first_child(kind=ANY_KIND).name == "cause1"
        assert fail1.first_child(kind="unknown") is None

        assert fail1.last_child(kind="cause").name == "cause2"
        assert fail1.last_child(kind="effect").name == "eff2"
        assert fail1.last_child(kind=ANY_KIND).name == "eff2"
        assert fail1.last_child(kind="unknown") is None

        cause1 = tree["cause1"]
        cause2 = tree["cause2"]
        eff1 = tree["eff1"]
        eff2 = tree["eff2"]

        assert cause2.get_siblings(any_kind=True, add_self=True) == fail1.get_children(
            kind=ANY_KIND
        )
        assert cause2.get_siblings() != fail1.get_children(kind=ANY_KIND)
        assert cause2.get_siblings(add_self=True) == fail1.get_children(kind="cause")

        assert cause2.parent is fail1

        assert len(list(tree.iter_by_type("cause"))) == 2

        assert cause2.get_children("undefined") == []

        assert cause2.first_child(ANY_KIND) is None
        assert cause2.first_child("undefined") is None

        assert cause2.last_child(ANY_KIND) is None
        assert cause2.last_child("undefined") is None

        assert cause2.first_sibling() is cause1
        assert cause2.first_sibling(any_kind=True) is cause1

        assert cause2.last_sibling() is cause2
        assert cause2.last_sibling(any_kind=True) is eff2

        assert cause1.prev_sibling() is None
        assert cause1.prev_sibling(any_kind=True) is None
        assert cause2.prev_sibling() is cause1
        assert cause2.prev_sibling(any_kind=True) is cause1

        assert cause1.next_sibling() is cause2
        assert cause1.next_sibling(any_kind=True) is cause2
        assert cause2.next_sibling() is None
        assert cause2.next_sibling(any_kind=True) is eff1

        assert eff1.is_first_sibling()
        assert not eff1.is_first_sibling(any_kind=True)
        assert not eff2.is_first_sibling()

        assert not eff1.is_last_sibling()
        assert not eff1.is_last_sibling(any_kind=True)
        assert eff2.is_last_sibling()
        assert eff2.is_last_sibling(any_kind=True)

        assert eff1.get_index() == 0
        assert eff2.get_index() == 1
        assert eff1.get_index(any_kind=True) == 2

        # Copy node
        assert not fail1.is_clone()
        func2_clone = func2.add(fail1, kind=None)
        assert func2_clone.kind == "failure"
        assert fail1.is_clone()

        subtree = func2.copy()
        assert isinstance(subtree, TypedTree)

    def test_add_child_2(self):
        tree = TypedTree("fixture")

        a = tree.add("A", kind=None)
        assert a.kind is tree.DEFAULT_CHILD_TYPE
        a.append_child("a1", kind=None)
        a.prepend_child("a0", kind=None)
        a.append_sibling("A2", kind=None)
        a.prepend_sibling("A0", kind=None)

        b = tree.add("B", kind="letter")
        tree_2 = (
            TypedTree("fixture2")
            .add("X", kind=None)
            .add("x1", kind=None)
            .up(2)
            .add("Y", kind=None)
            .add("y1", kind=None)
            .tree
        )
        b.append_child(tree_2, kind=None)
        tree.print()
        assert fixture.check_content(
            tree,
            """
            TypedTree<*>
            +- child → A0
            +- child → A
            |  +- child → a0
            |  `- child → a1
            +- child → A2
            `- letter → B
               +- child → X
               |  `- child → x1
               `- child → Y
                  `- child → y1           
            """,
        )

    def test_graph_product(self):
        tree = TypedTree("Pencil")

        func = tree.add("Write on paper", kind="function")
        fail = func.add("Wood shaft breaks", kind="failure")
        fail.add("Unable to write", kind="effect")
        fail.add("Injury from splinter", kind="effect")
        fail.add("Wood too soft", kind="cause")

        fail = func.add("Lead breaks", kind="failure")
        fail.add("Cannot erase (dissatisfaction)", kind="effect")
        fail.add("Lead material too brittle", kind="cause")

        func = tree.add("Erase text", kind="function")

        assert fixture.check_content(
            tree,
            """
            TypedTree<*>
            +- function → Write on paper
            |  +- failure → Wood shaft breaks
            |  |  +- effect → Unable to write
            |  |  +- effect → Injury from splinter
            |  |  `- cause → Wood too soft
            |  `- failure → Lead breaks
            |     +- effect → Cannot erase (dissatisfaction)
            |     `- cause → Lead material too brittle
            `- function → Erase text
           """,
        )
        # tree.print()
        # raise

    def test_graph_product2(self):
        tree = fixture.create_typed_tree_simple()
        tree.print()
        with fixture.WritableTempFile("w", suffix=".gv") as temp_file:
            tree.to_dotfile(temp_file.name)

            buffer = Path(temp_file.name).read_text()

        print(buffer)
        assert '[label="func2"]' in buffer
