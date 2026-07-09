# ruff: noqa: T201, T203 `print` found
# pyright: reportIncompatibleMethodOverride=false
# mypy: disable-error-code="override"

# type: ignore

from __future__ import annotations

from typing import Generic, cast
from uuid import UUID, uuid4

from typing_extensions import Any, Self, TypeVar, reveal_type

TData = TypeVar("TData", bound="Any", default="Any")
TNode = TypeVar("TNode", bound="Node", default="Node[TData]")


class Node(Generic[TData]):
    def __init__(self, data: TData, parent: Self):
        self.data: TData = data
        self.parent: Self = parent
        self.children: list[Self] = []

    def add(self, data: TData) -> Self:
        node = self.__class__(data, self)
        self.children.append(node)
        return node


class Tree(Generic[TData, TNode]):
    node_factory: type[TNode] = cast(type[TNode], Node)

    def __init__(self):
        self._root: Node = self.node_factory("__root__", None)  # type: ignore

    def add(self, data: TData) -> TNode:
        node = self.root.add(data)
        return node

    @property
    def root(self) -> TNode:
        return cast(TNode, self._root)

    def first(self) -> TNode:
        return self.root.children[0]


# ----------------------------


class TypedNode(Node[TData]):
    def __init__(self, data: TData, kind: str, parent: Self):
        super().__init__(data, parent)
        self.kind: str = kind
        # self.children: List[TypedNode] = []

    def add(self, data: TData, kind: str) -> Self:
        node = self.__class__(data, kind, self)
        self.children.append(node)
        return node


class TypedTree(Tree[TData, TypedNode[TData]]):
    node_factory = TypedNode

    def __init__(self):
        self._root = TypedNode("__root__", "__root__", None)  # type: ignore

    def add(self, data: TData, kind: str) -> TypedNode[TData]:
        node = self.root.add(data, kind)
        return node


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
        tree.first().add("child2")

        reveal_type(tree.root)
        reveal_type(n)
        reveal_type(tree.first())
        reveal_type(tree.first().data)

    def test_str_tree(self):
        tree = Tree[str]()

        n = tree.add("child")
        n.add("child2")
        n.add(42)
        tree.add(42)

        reveal_type(tree.root)
        reveal_type(n)
        reveal_type(tree.first())
        reveal_type(tree.first().data)

    def test_orga_tree(self):
        tree = Tree[OrgaEntry]()

        dev = tree.add(Department("Development"))
        alice = dev.add(Person("Alice", 42))
        tree.add(42)
        alice.add(42)

        reveal_type(tree.root)
        reveal_type(alice)
        reveal_type(tree.first())
        reveal_type(tree.first().data)
        reveal_type(alice)
        reveal_type(alice.data)


class TestTypedTreeTyping:
    def test_typed_tree(self):
        tree = TypedTree()

        n = tree.add("child", kind="child")
        n.add("child2", kind="child")
        tree.add(42, kind="child")

        tree.first().add("child3", kind="child")

        reveal_type(tree.root)
        reveal_type(n)
        reveal_type(tree.first())
        reveal_type(tree.first().data)

    def test_typed_tree_str(self):
        tree = TypedTree[str]()

        n = tree.add("child", kind="child")
        n.add("child2", kind="child")
        n.add(42, kind="child")
        tree.add(42, kind="child")

        tree.first().add("child3", kind="child")

        reveal_type(tree.root)
        reveal_type(n)
        reveal_type(tree.first())
        reveal_type(tree.first().data)

    def test_typed_tree_orga(self):
        tree = TypedTree[OrgaEntry]()

        dev = tree.add(Department("Development"), kind="department")
        alice = dev.add(Person("Alice", 42), kind="member")
        tree.add(42, kind="child")
        alice.add(42, kind="child")

        reveal_type(alice)
        reveal_type(tree.first())
        reveal_type(tree.first().data)
        reveal_type(alice)
        reveal_type(alice.data)
