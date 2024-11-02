# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Declare the :class:`~nutree.tree.TypedTree` class.
"""
# pyright: reportIncompatibleMethodOverride=false

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import IO, Any, Iterator, Type, cast

# typing.Self requires Python 3.11
from typing_extensions import Self

from nutree.common import (
    ROOT_DATA_ID,
    ROOT_NODE_ID,
    CalcIdCallbackType,
    DataIdType,
    DeserializeMapperType,
    KeyMapType,
    MapperCallbackType,
    SerializeMapperType,
    UniqueConstraintError,
    ValueMapType,
    call_mapper,
    sentinel,
)
from nutree.node import Node
from nutree.tree import Tree


class TAnyKind:
    """Special argument value for some methods that access child nodes."""


#: Special argument value for some methods that access child nodes
ANY_KIND = sentinel.ANY_KIND


# ------------------------------------------------------------------------------
# - TypedNode
# ------------------------------------------------------------------------------
class TypedNode(Node):
    """
    A special node variant, derived from :class:`~nutree.node.Node` and
    used by :class:`~nutree.typed_tree.TypedTree`.

    In addition to :class:`~nutree.node.Node`, we have a `kind` member to
    define the node's type.
    """

    __slots__ = ("_kind",)

    #: Default value for ``repr`` argument when formatting data for print/display.
    DEFAULT_RENDER_REPR = "{node.kind} → {node.data}"

    # #: Default value for ``repr`` argument when formatting data for export,
    # #: like DOT, RDF, ...
    # DEFAULT_NAME_REPR = "{node.data!r}"

    def __init__(
        self,
        kind: str,
        data,
        *,
        parent: Self,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
        meta: dict | None = None,
    ):
        self._kind = kind  # tree._register() checks for this attribute
        super().__init__(
            data, parent=parent, data_id=data_id, node_id=node_id, meta=meta
        )
        assert isinstance(kind, str) and kind != ANY_KIND, f"Unsupported `kind`: {kind}"

        # del self._children
        # self._child_map: Dict[Node] = None

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}<kind={self.kind}, "
            f"{self.name}, data_id={self.data_id!r}>"
        )

    # @property
    # def name(self) -> str:
    #     """String representation of the embedded `data` object with kind."""
    #     # return f"{self._kind} → {self.data}"
    #     # Inspired by clarc notation: http://www.jclark.com/xml/xmlns.htm
    #     # return f"{{{self._kind}}}:{self.data}"
    #     return f"{self.data}"

    @property
    def kind(self) -> str:
        return self._kind

    # @property
    # def parent(self) -> TypedNode | None:
    #     """Return parent node or None for toplevel nodes."""
    #     p = self._parent
    #     return p if p._parent else None

    # @property
    # def children(self) -> list[TypedNode]:
    #     """Return list of direct child nodes (list may be empty).

    #     Note that this property returns all children, independent of the kind.
    #     See also :meth:`get_children`.
    #     """
    #     c = self._children
    #     return [] if c is None else c

    def get_children(self, kind: str | ANY_KIND) -> list[Self]:
        """Return list of direct child nodes of a given type (list may be empty)."""
        all_children = self._children
        if not all_children:
            return []
        elif kind is ANY_KIND:
            return all_children
        return list(filter(lambda n: n._kind == kind, all_children))

    # def set_data(
    #     self, kind: str, data, *, data_id=None, with_clones: bool = None
    # ) -> None:
    #     """Change node's `data` and/or `data_id` and update bookkeeping."""
    #     super().set_data(data, data_id=data_id, with_clones=with_clones)

    def first_child(self, kind: str | ANY_KIND) -> Self | None:
        """First direct child node or None if no children exist."""
        all_children = self._children
        if not all_children:
            return None
        elif kind is ANY_KIND:
            return all_children[0]

        for n in all_children:
            if n._kind == kind:
                return n
        return None

    def last_child(self, kind: str | ANY_KIND) -> Self | None:
        """Last direct child node or None if no children exist."""
        all_children = self._children
        if not all_children:
            return None
        elif kind is ANY_KIND:
            return all_children[-1]

        for i in range(len(all_children) - 1, -1, -1):
            n = all_children[i]
            if n._kind == kind:
                return n
        return None

    def has_children(self, kind: str | ANY_KIND) -> bool:
        """Return true if this node has one or more children."""
        if kind is ANY_KIND:
            return bool(self._children)
        return len(self.get_children(kind)) > 1

    def get_siblings(self, *, add_self=False, any_kind=False) -> list[Self]:
        """Return a list of all sibling entries of self (excluding self) if any."""
        if any_kind:
            return super().get_siblings(add_self=add_self)
        children = self._parent.children
        rel = self.kind
        return [n for n in children if (add_self or n is not self) and n.kind == rel]

    def first_sibling(self, *, any_kind=False) -> Self:
        """Return first sibling `of the same kind` (may be self)."""
        pc = self._parent.children
        if any_kind:
            return pc[0]
        for n in pc:
            if n._kind == self._kind:
                return n
        raise AssertionError("Internal error")  # pragma: no cover

    def last_sibling(self, *, any_kind=False) -> Self:
        """Return last sibling `of the same kind` (may be self)."""
        pc = self._parent.children
        if any_kind:
            return pc[-1]
        for n in reversed(pc):
            if n._kind == self._kind:
                return n
        raise AssertionError("Internal error")  # pragma: no cover

    def prev_sibling(self, *, any_kind=False) -> Self | None:
        """Return predecessor `of the same kind` or None if node is first sibling."""
        pc = self._parent.children
        own_idx = pc.index(self)
        if own_idx > 0:
            for idx in range(own_idx - 1, -1, -1):
                n = pc[idx]
                if any_kind or n._kind == self._kind:
                    return n
        return None

    def next_sibling(self, *, any_kind=False) -> Self | None:
        """Return successor `of the same kind` or None if node is last sibling."""
        pc = self._parent.children
        pc_len = len(pc)
        own_idx = pc.index(self)

        if own_idx < pc_len - 2:
            for idx in range(own_idx + 1, pc_len):
                n = pc[idx]
                if any_kind or n._kind == self._kind:
                    return n
        return None

    def get_index(self, *, any_kind=False) -> int:
        """Return index in sibling list."""
        if any_kind:
            kc = self._parent.children
        else:
            kc = self._parent.get_children(self.kind)
        return kc.index(self)

    def is_first_sibling(self, *, any_kind=False) -> bool:
        """Return true if this node is the first sibling, i.e. the first child
        of its parent."""
        if any_kind:
            return self is self._parent.children[0]
        return self is self.first_sibling(any_kind=False)

    def is_last_sibling(self, *, any_kind=False) -> bool:
        """Return true if this node is the last sibling, i.e. the last child
        **of this kind** of its parent."""
        if any_kind:
            return self is self._parent.children[-1]
        return self is self.last_sibling(any_kind=False)

    def add_child(
        self,
        child: Self | TypedTree | Any,
        *,
        kind: str | None = None,
        before: Self | bool | int | None = None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> Self:
        """See ..."""
        # assert not isinstance(child, TypedNode) or child.kind == self.kind
        # TODO: kind is optional if child is a TypedNode
        # TODO: Check if target and child types match
        # TODO: share more code from overloaded method
        if kind is None:
            kind = cast(TypedTree, self._tree).DEFAULT_CHILD_TYPE

        if isinstance(child, (Node, Tree)) and not isinstance(
            child, (TypedNode, TypedTree)
        ):
            raise TypeError("If child is a node or tree it must be typed.")

        if isinstance(child, TypedTree):
            if deep is None:
                deep = True
            topnodes = child._root.children
            if isinstance(before, (int, Node)) or before is True:
                topnodes.reverse()
            for n in topnodes:
                self.add_child(n, kind=n.kind, before=before, deep=deep)
            return child._root  # type: ignore

        source_node: Self = None  # type: ignore
        new_node: Self = None  # type: ignore
        factory: Type[Self] = self._tree.node_factory  # type: ignore

        if isinstance(child, TypedNode):
            if deep is None:
                deep = False
            if deep and data_id is not None or node_id is not None:
                raise ValueError("Cannot set ID for deep copies.")
            source_node = cast(Self, child)
            if source_node._tree is self._tree:
                if source_node._parent is self:
                    raise UniqueConstraintError(
                        f"Same parent not allowed: {source_node}"
                    )
            else:
                pass
            if data_id and data_id != source_node._data_id:
                raise UniqueConstraintError(f"data_id conflict: {source_node}")

            # If creating an inherited node, use the parent class as constructor
            new_node = factory(
                kind,
                source_node.data,
                parent=self,
                data_id=data_id,
                node_id=node_id,
            )
        else:
            new_node = factory(
                kind, child, parent=self, data_id=data_id, node_id=node_id
            )

        # assert isinstance(node, self.__class__)

        children = self._children
        if children is None:
            assert before in (None, True, int, False)
            self._children = [new_node]
        elif before is True:  # prepend
            children.insert(0, new_node)
        elif isinstance(before, int):
            children.insert(before, new_node)
        elif before:
            if before._parent is not self:
                raise ValueError(
                    f"`before=node` ({before._parent}) "
                    f"must be a child of target node ({self})"
                )
            idx = children.index(before)  # raises ValueError
            children.insert(idx, new_node)
        else:
            children.append(new_node)

        if deep and source_node:
            new_node._add_from(source_node)

        return new_node

    #: Alias for :meth:`add_child`
    add = add_child

    def append_child(
        self,
        child: Self | TypedTree | Any,
        *,
        kind: str | None = None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ):
        """Append a new subnode.

        This is a shortcut for :meth:`add_child` with ``before=None``.
        """
        return self.add_child(
            child,
            kind=kind,
            before=None,
            deep=deep,
            data_id=data_id,
            node_id=node_id,
        )

    def prepend_child(
        self,
        child: Self | TypedTree | Any,
        *,
        kind: str | None = None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ):
        """Prepend a new subnode.

        This is a shortcut for :meth:`add_child` with ``before=True``.
        """
        return self.add_child(
            child,
            kind=kind,
            before=self.first_child(kind=ANY_KIND),
            deep=deep,
            data_id=data_id,
            node_id=node_id,
        )

    def prepend_sibling(
        self,
        child: Self | TypedTree | Any,
        *,
        kind: str | None = None,
        deep=None,
        data_id=None,
        node_id=None,
    ) -> Self:
        """Add a new node **of same kind** before `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        return self._parent.add_child(
            child, kind=kind, before=self, deep=deep, data_id=data_id, node_id=node_id
        )

    def append_sibling(
        self,
        child: Self | TypedTree | Any,
        *,
        kind: str | None = None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> Self:
        """Add a new node **of same kind** after `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        next_node = self.next_sibling()
        return self._parent.add_child(
            child,
            kind=kind,
            before=next_node,
            deep=deep,
            data_id=data_id,
            node_id=node_id,
        )

    @classmethod
    def _make_list_entry(cls, node: Self) -> dict[str, Any]:
        node_data = node._data
        # is_custom_id = node._data_id != hash(node_data)

        if isinstance(node_data, str):
            # Node._make_list_entry() would return a plain str, but we always
            # need a dict
            data = {
                "str": node_data,
            }
        else:
            data = Node._make_list_entry(node)

        assert isinstance(data, dict)
        if node.kind is not ANY_KIND:
            data["kind"] = node.kind
        return data

    def to_dot(
        self,
        *,
        add_self=False,
        unique_nodes=True,
        graph_attrs: dict | None = None,
        node_attrs: dict | None = None,
        edge_attrs: dict | None = None,
        node_mapper: MapperCallbackType | None = None,
        edge_mapper: MapperCallbackType | None = None,
    ) -> Iterator[str]:
        """Generate a DOT formatted graph representation.

        See :ref:`graphs` for details.
        """

        # TypedNodes can provide labelled edges:
        def _edge_mapper(node, data):
            data["label"] = node.kind
            if edge_mapper:
                return edge_mapper(node, data)

        res = super().to_dot(
            add_self=add_self,
            unique_nodes=unique_nodes,
            graph_attrs=graph_attrs,
            node_attrs=node_attrs,
            edge_attrs=edge_attrs,
            node_mapper=node_mapper,
            edge_mapper=_edge_mapper,
        )
        return res


# ------------------------------------------------------------------------------
# - _SystemRootTypedNode
# ------------------------------------------------------------------------------
class _SystemRootTypedNode(TypedNode):
    """Invisible system root node."""

    def __init__(self, tree: TypedTree) -> None:
        self._tree: TypedTree = tree  # type: ignore
        self._parent = None  # type: ignore
        self._node_id = ROOT_NODE_ID
        self._data_id = ROOT_DATA_ID
        self._data = tree.name
        self._children = []
        self._meta = None
        self._kind = None


# ------------------------------------------------------------------------------
# - TypedTree
# ------------------------------------------------------------------------------
class TypedTree(Tree[TypedNode]):
    """
    A special tree variant, derived from :class:`~nutree.tree.Tree`,
    that uses :class:`~nutree.typed_tree.TypedNode` objects, which maintain
    an addition `kind` attribute.

    See :ref:`typed-tree` for details.
    """

    node_factory = TypedNode
    root_node_factory = _SystemRootTypedNode

    #: Default value for ``key_map`` argument when saving
    DEFAULT_KEY_MAP = {"data_id": "i", "str": "s", "kind": "k"}
    #: Default value for ``value_map`` argument when saving
    DEFAULT_VALUE_MAP = {}  # expands to { "kind": [<distinct `kind` values>] }
    #: Default value for ``add_child`` when loading.
    DEFAULT_CHILD_TYPE = "child"

    def __init__(
        self,
        name: str | None = None,
        *,
        calc_data_id: CalcIdCallbackType | None = None,
        forward_attrs: bool = False,
    ):
        super().__init__(
            name,
            calc_data_id=calc_data_id,
            forward_attrs=forward_attrs,
        )
        # self._root = _SystemRootTypedNode(self)

    @classmethod
    def deserialize_mapper(cls, parent: Node, data: dict) -> str | object | None:
        """Used as default `mapper` argument for :meth:`load`."""
        if "str" in data and len(data) <= 2:
            # This can happen if the source was generated without a
            # serialization mapper, for a TypedTree that has pure str nodes
            return data["str"]
        raise NotImplementedError(
            f"Override this method or pass a mapper callback to evaluate {data}."
        )

    def add_child(
        self,
        child: TypedNode | Self | Any,
        *,
        kind: str | None = None,
        before: TypedNode | bool | int | None = None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> TypedNode:
        """Add a toplevel node.

        See Node's :meth:`~nutree.node.Node.add_child` method for details.
        """
        return self._root.add_child(
            child,
            kind=kind,
            before=before,
            deep=deep,
            data_id=data_id,
            node_id=node_id,
        )

    #: Alias for :meth:`add_child`
    add = add_child  # Must re-bind here

    def first_child(self, kind: str | ANY_KIND) -> TypedNode | None:
        """Return the first toplevel node."""
        return self._root.first_child(kind=kind)

    def last_child(self, kind: str | ANY_KIND) -> TypedNode | None:
        """Return the last toplevel node."""
        return self._root.last_child(kind=kind)

    def iter_by_type(self, kind: str | ANY_KIND) -> Iterator[TypedNode]:
        if kind == ANY_KIND:
            return self.iterator()
        for n in self.iterator():
            if n._kind == kind:
                yield n
        return

    def save(
        self,
        target: IO[str] | str | Path,
        *,
        mapper: SerializeMapperType | None = None,
        meta: dict | None = None,
        key_map: KeyMapType | bool = True,
        value_map: ValueMapType | bool = True,
    ) -> None:
        """Store tree in a compact JSON file stream.

        See also :ref:`serialize` and :meth:`to_list_iter` and :meth:`load` methods.
        """
        # TypedTrees can assume reasaonable defaults for key_map and value_map
        # (key_map is evaluated in base class from TypedTree.DEFAULT_KEY_MAP)

        # print("value_map    ", value_map)
        if value_map is True or isinstance(value_map, dict):
            if value_map is True:
                value_map = self.DEFAULT_VALUE_MAP.copy()

            if "kind" not in value_map:
                counter = Counter()
                for n in self:
                    counter[n.kind] += 1
                value_map.update({"kind": list(counter.keys())})
                # print("value_map -> ", value_map)
        else:
            assert value_map is False, value_map

        return super().save(
            target,
            mapper=mapper,
            meta=meta,
            key_map=key_map,
            value_map=value_map,
        )

    @classmethod
    def _from_list(
        cls, obj: list[dict], *, mapper: DeserializeMapperType | None = None
    ) -> Self:
        tree = cls()

        if mapper is None:
            mapper = cls.deserialize_mapper

        # System root has index #0:
        node_idx_map: dict[int, TypedNode] = {0: tree._root}

        # Start reading data lines starting at index #1:
        for idx, (parent_idx, data) in enumerate(obj, 1):
            parent = node_idx_map[parent_idx]
            # print(idx, parent_idx, data, parent)
            if isinstance(data, str):
                # This can only happen if the source was generated by a plain Tree
                n = parent.add(data, kind=cls.DEFAULT_CHILD_TYPE)
            elif isinstance(data, int):
                first_clone = node_idx_map[data]
                n = parent.add(
                    first_clone, kind=first_clone.kind, data_id=first_clone.data_id
                )
            else:
                kind = data.get("kind", cls.DEFAULT_CHILD_TYPE)
                data_id = data.get("data_id")
                data_obj = call_mapper(mapper, parent, data)
                n = parent.add(data_obj, kind=kind, data_id=data_id)
            # elif isinstance(data, dict) and "str" in data:
            #     # This can happen if the source was generated without a
            #     # serialization mapper, for a TypedTree that has str nodes
            #     n = parent.add(data["str"], kind=data.get("kind"))
            # else:
            #     raise RuntimeError(f"Need mapper for {data}")

            node_idx_map[idx] = n

        return tree

    @classmethod
    def load(
        cls,
        target: IO[str] | str | Path,
        *,
        mapper: DeserializeMapperType | None = None,
        file_meta: dict | None = None,
    ) -> Self:
        """Create a new :class:`TypedTree` instance from a JSON file stream.

        See also Tree's :meth:`~nutree.tree.Tree.save()` and
        :meth:`~nutree.tree.Tree.load()` methods.
        """
        return super().load(target, mapper=mapper, file_meta=file_meta)

    # @classmethod
    # def build_random_tree(cls, structure_def: dict) -> Self:
    #     """Build a random tree for testing."""
    #     tt = build_random_tree(cls, structure_def)
    #     return tt
