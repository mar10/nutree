# ruff: noqa: T201, T203 `print` found

from __future__ import annotations

from typing import Any, Generic, List, TypeVar, cast

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self  # noqa: F401


# TData = TypeVar("TData")
TNode = TypeVar("TNode", bound="Node")


class Node:
    def __init__(self, data: Any, parent: Node):
        self.data: Any = data
        self.parent: Node = parent
        self.children: List[Node] = []

    def add(self, data: Any) -> Node:
        node = Node(data, self)
        self.children.append(node)
        return node


class Tree(Generic[TNode]):
    def __init__(self):
        self.root: Node = Node("__root__", cast(TNode, None))

    def add(self, data: Any) -> Node:
        node = self.root.add(data)
        return node

    def first(self) -> TNode:
        return self.root.children[0]


# ----------------------------
# ----------------------------


class TypedNode(Node):
    def __init__(self, data: Any, kind: str, parent: TypedNode):
        super().__init__(data, parent)
        self.kind: str = kind
        # self.children: List[TypedNode] = []

    def add(self, data: Any, kind: str) -> TypedNode:
        node = TypedNode(data, kind, self)
        self.children.append(node)
        return node


class TypedTree(Tree[TypedNode]):
    def __init__(self):
        self.root: TypedNode = TypedNode("__root__", "__root__", cast(TypedNode, None))

    def add(self, data: Any, kind: str) -> TNode:
        node = self.root.add(data, kind)
        return node


class TestTypingSelf:
    def test_tree(self):
        tree = Tree()
        n = tree.add("top")
        n.add("child")
        tree.first().add("child2")

    def test_typed_tree(self):
        tree = TypedTree()
        tree.add("child", kind="child")
        tree.add("child2", kind="child")

        tree.first().add("child3", kind="child")
