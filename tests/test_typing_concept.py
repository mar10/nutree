# ruff: noqa: T201, T203 `print` found
# pyright: reportIncompatibleMethodOverride=false

from __future__ import annotations

from typing import Any, Generic, List, Type, TypeVar, cast

try:
    from typing import Self
except ImportError as e:
    print(f"ImportError: {e}")
    from typing_extensions import Self  # noqa: F401


TNode = TypeVar("TNode", bound="Node")


class Node:
    def __init__(self, data: Any, parent: Self):
        self.data: Any = data
        self.parent: Self = parent
        self.children: List[Self] = []

    def add(self, data: Any) -> Self:
        node = self.__class__(data, self)
        self.children.append(node)
        return node


class Tree(Generic[TNode]):
    node_factory: Type[TNode] = cast(Type[TNode], Node)

    def __init__(self):
        self.root: TNode = self.node_factory("__root__", cast(TNode, None))

    def add(self, data: Any) -> TNode:
        node = self.root.add(data)
        return node

    def first(self) -> TNode:
        return self.root.children[0]


# ----------------------------


class TypedNode(Node):
    def __init__(self, data: Any, kind: str, parent: Self):
        super().__init__(data, parent)
        self.kind: str = kind
        # self.children: List[TypedNode] = []

    def add(self, data: Any, kind: str) -> Self:
        node = self.__class__(data, kind, self)
        self.children.append(node)
        return node


class TypedTree(Tree[TypedNode]):
    node_factory = TypedNode

    def __init__(self):
        self.root: TypedNode = self.node_factory(
            "__root__", "__root__", cast(TypedNode, None)
        )

    def add(self, data: Any, kind: str) -> TypedNode:
        node = self.root.add(data, kind)
        return node


class TestTypingSelf:
    def test_tree(self):
        tree = Tree[Node]()
        n = tree.add("top")
        n.add("child")
        tree.first().add("child2")

    def test_typed_tree(self):
        tree = TypedTree()

        tree.add("child", kind="child")
        tree.add("child2", kind="child")

        # tree.first().children
        tree.first().add("child3", kind="child")
