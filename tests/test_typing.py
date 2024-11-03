# ruff: noqa: T201, T203 `print` found
# type: ignore
from __future__ import annotations

from uuid import UUID, uuid4

from nutree.tree import Tree
from nutree.typed_tree import ANY_KIND, TypedTree
from typing_extensions import reveal_type


# --- Sample data ------------------------------------------------------------
class OrgaEntry:
    def __init__(self, name: str):
        self.name: str = name
        self.guid: UUID = uuid4()


class Person(OrgaEntry):
    def __init__(self, name: str, age: int):
        super().__init__(name)
        self.age: int = age


class Department(OrgaEntry):
    def __init__(self, name: str):
        super().__init__(name)


# --- Test -------------------------------------------------------------------


class TestTreeTyping:
    def test_tree(self):
        tree = Tree()
        n = tree.add("top")
        n.add("child")
        tree.add(42)
        n.add(42)
        tree.first_child().add("child2")

        reveal_type(tree.system_root)
        reveal_type(n)
        reveal_type(tree.first_child())
        reveal_type(tree.first_child().data)

    def test_str_tree(self):
        tree = Tree[str]()

        n = tree.add("child")
        n.add("child2")
        n.add(42)
        tree.add(42)

        reveal_type(tree.system_root)
        reveal_type(n)
        reveal_type(tree.first_child())
        reveal_type(tree.first_child().data)

    def test_orga_tree(self):
        tree = Tree[OrgaEntry]()

        dev = tree.add(Department("Development"))
        alice = dev.add(Person("Alice", 42))
        tree.add(42)
        alice.add(42)

        reveal_type(tree.system_root)
        reveal_type(alice)
        reveal_type(tree.first_child())
        reveal_type(tree.first_child().data)
        reveal_type(alice)
        reveal_type(alice.data)


class TestTypedTreeTyping:
    def test_typed_tree(self):
        tree = TypedTree()

        n = tree.add("child", kind="child")
        n.add("child2", kind="child")
        tree.add(42, kind="child")

        tree.first_child(kind=ANY_KIND).add("child3", kind="child")

        reveal_type(tree.system_root)
        reveal_type(n)
        reveal_type(tree.first_child(kind=ANY_KIND))
        reveal_type(tree.first_child(kind=ANY_KIND).data)

    def test_typed_tree_str(self):
        tree = TypedTree[str]()

        n = tree.add("child", kind="child")
        n.add("child2", kind="child")
        n.add(42, kind="child")
        tree.add(42, kind="child")

        tree.first_child(kind=ANY_KIND).add("child3", kind="child")

        reveal_type(tree.system_root)
        reveal_type(n)
        reveal_type(tree.first_child(kind=ANY_KIND))
        reveal_type(tree.first_child(kind=ANY_KIND).data)

    def test_typed_tree_orga(self):
        tree = TypedTree[OrgaEntry]()

        dev = tree.add(Department("Development"), kind="department")
        alice = dev.add(Person("Alice", 42), kind="member")
        tree.add(42, kind="child")
        alice.add(42, kind="child")

        reveal_type(alice)
        reveal_type(tree.first_child(kind=ANY_KIND))
        reveal_type(tree.first_child(kind=ANY_KIND).data)
        reveal_type(alice)
        reveal_type(alice.data)
