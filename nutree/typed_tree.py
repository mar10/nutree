# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php

# Type checker suppressions for this file:
#
# We allow
#   Invalid override of method `FOO`: Definition is incompatible with `Node.FOO`
#   info: incompatible return types: `list[TypedNode[TData@TypedNode]]`
#         is not assignable to `list[Node[TData@TypedNode]]`
#   info: This violates the Liskov Substitution Principle
#
# ty: ignore[invalid-method-override]

"""
Declare the :class:`~nutree.tree.TypedTree` class.
"""

from __future__ import annotations

import copy
import warnings
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import IO, cast, final

# typing.Self requires Python 3.11
from typing_extensions import Any, Self, deprecated

from nutree.common import (
    ROOT_DATA_ID,
    ROOT_NODE_ID,
    CalcIdCallbackType,
    CycleDetectedError,
    DataIdType,
    DeserializeMapperType,
    DotMapperCallbackType,
    IterMethod,
    KeyMapType,
    PredicateCallbackType,
    SerializeMapperType,
    UniqueConstraintError,
    ValueMapType,
    call_dot_mapper,
)
from nutree.node import Node, TData
from nutree.tree import Tree


@final
class ANY_KIND:
    """Sentinel meaning that child-node operations should accept any kind."""


# ------------------------------------------------------------------------------
# - TypedNode
# ------------------------------------------------------------------------------


class TypedNode(Node[TData]):
    """
    :class:`~nutree.node.Node` variant used by :class:`~nutree.typed_tree.TypedTree`.

    In addition to the wrapped data, a typed node has a string ``kind`` that
    identifies its role in the hierarchy. Methods that accept a ``kind`` filter
    by that value; :class:`~nutree.typed_tree.ANY_KIND` disables the filter.
    """

    __slots__ = ("_kind",)

    #: Default value for ``repr`` argument when formatting data for print/display.
    DEFAULT_RENDER_REPR = "{node.kind} → {node.data}"

    def __init__(
        self,
        kind: str,
        data: TData,
        *,
        parent: Self,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
        meta: dict[str, Any] | None = None,
    ):
        # tree._register() checks for this attribute in __init__():
        self._kind: str = kind
        super().__init__(
            data, parent=parent, data_id=data_id, node_id=node_id, meta=meta
        )
        assert isinstance(kind, str), f"Unsupported `kind`: {kind}"

        # del self._children
        # self._child_map: Dict[Node] = None

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}<kind={self.kind}, "
            f"{self.name}, data_id={self.data_id!r}>"
        )

    @property
    def kind(self) -> str:
        return self._kind

    def get_children(self, kind: str | type[ANY_KIND]) -> list[Self]:
        """Return direct children of ``kind`` (or all kinds with :class:`ANY_KIND`)."""
        all_children = self._children
        if not all_children:
            return []
        elif kind is ANY_KIND:
            return all_children
        return list(filter(lambda n: n._kind == kind, all_children))

    def first_child(self, kind: str | type[ANY_KIND]) -> Self | None:
        """Return the first direct child of ``kind``, or ``None`` if absent."""
        all_children = self._children
        if not all_children:
            return None
        elif kind is ANY_KIND:
            return all_children[0]

        for n in all_children:
            if n._kind == kind:
                return n
        return None

    def last_child(self, kind: str | type[ANY_KIND]) -> Self | None:
        """Return the last direct child of ``kind``, or ``None`` if absent."""
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

    def iterator(
        self,
        method: IterMethod = IterMethod.PRE_ORDER,
        *,
        add_self: bool = False,
        kind: str | type[ANY_KIND] = ANY_KIND,
    ) -> Iterator[TypedNode[TData]]:
        """Iterate descendants in ``method`` order, optionally filtered by kind.

        Pass :class:`ANY_KIND` to include all kinds. See
        :meth:`~nutree.node.Node.iterator` and :class:`~nutree.common.IterMethod`.
        """
        if kind is ANY_KIND:
            yield from super().iterator(method=method, add_self=add_self)
            return

        if add_self and self.kind == kind:
            yield self
        for n in super().iterator(method=method, add_self=False):
            if n.kind == kind:
                yield n
        return

    def has_children(self, kind: str | type[ANY_KIND]) -> bool:
        """Return whether this node has children of ``kind``.

        Pass :class:`ANY_KIND` to test for children of any kind.
        """
        if kind is ANY_KIND:
            return bool(self._children)
        return len(self.get_children(kind)) > 1

    def count_descendants(
        self, *, leaves_only: bool = False, kind: str | type[ANY_KIND] = ANY_KIND
    ) -> int:
        """Count descendants, optionally restricted to ``kind`` or leaves."""
        if kind is ANY_KIND:
            return super().count_descendants(leaves_only=leaves_only)
        all = not leaves_only
        i = 0
        for node in self.iterator():
            if (all or not node._children) and node.kind == kind:
                i += 1
        return i

    def get_siblings(
        self, *, add_self: bool = False, any_kind: bool = False
    ) -> list[Self]:
        """Return siblings of the same kind, excluding this node by default.

        Set ``any_kind`` to include siblings of every kind and ``add_self`` to
        include this node in the result.
        """
        if any_kind:
            return super().get_siblings(add_self=add_self)
        children = self._parent.children
        rel = self.kind
        return [n for n in children if (add_self or n is not self) and n.kind == rel]

    def first_sibling(self, *, any_kind: bool = False) -> Self:
        """Return the first sibling of the same kind, which may be this node.

        Set ``any_kind`` to consider siblings of every kind.
        """
        pc = self._parent.children
        if any_kind:
            return pc[0]
        for n in pc:
            if n._kind == self._kind:
                return n
        raise AssertionError("Internal error")  # pragma: no cover

    def last_sibling(self, *, any_kind: bool = False) -> Self:
        """Return the last sibling of the same kind, which may be this node.

        Set ``any_kind`` to consider siblings of every kind.
        """
        pc = self._parent.children
        if any_kind:
            return pc[-1]
        for n in reversed(pc):
            if n._kind == self._kind:
                return n
        raise AssertionError("Internal error")  # pragma: no cover

    def prev_sibling(self, *, any_kind: bool = False) -> Self | None:
        """Return the previous sibling, or ``None`` if there is no match.

        By default, only siblings of the same kind are considered. Set
        ``any_kind`` to consider every kind.
        """
        pc = self._parent.children
        own_idx = pc.index(self)
        if own_idx > 0:
            for idx in range(own_idx - 1, -1, -1):
                n = pc[idx]
                if any_kind or n._kind == self._kind:
                    return n
        return None

    def next_sibling(self, *, any_kind: bool = False) -> Self | None:
        """Return the next sibling, or ``None`` if there is no match.

        By default, only siblings of the same kind are considered. Set
        ``any_kind`` to consider every kind.
        """
        pc = self._parent.children
        pc_len = len(pc)
        own_idx = pc.index(self)

        if own_idx < pc_len - 2:
            for idx in range(own_idx + 1, pc_len):
                n = pc[idx]
                if any_kind or n._kind == self._kind:
                    return n
        return None

    def get_index(self, *, any_kind: bool = False) -> int:
        """Return this node's index among same-kind siblings.

        Set ``any_kind`` to use the complete child list.
        """
        if any_kind:
            kc = self._parent.children
        else:
            kc = self._parent.get_children(self.kind)
        return kc.index(self)

    def is_first_sibling(self, *, any_kind: bool = False) -> bool:
        """Return whether this node is the first relevant sibling.

        By default, siblings of the same kind are considered. Set ``any_kind``
        to consider every kind.
        """
        if any_kind:
            return self is self._parent.children[0]
        return self is self.first_sibling(any_kind=False)

    def is_last_sibling(self, *, any_kind: bool = False) -> bool:
        """Return whether this node is the last relevant sibling.

        By default, siblings of the same kind are considered. Set ``any_kind``
        to consider every kind.
        """
        if any_kind:
            return self is self._parent.children[-1]
        return self is self.last_sibling(any_kind=False)

    def _add_from(
        self, other: Self, *, predicate: PredicateCallbackType | None = None
    ) -> None:
        """Append copies of all source descendants to self.

        See also :ref:`iteration-callbacks`.
        """
        if predicate:
            return self._add_filtered(other, predicate)

        assert not self._children
        for child in other.children:
            new_child = self.add_child(
                child.data, kind=child.kind, data_id=child._data_id
            )
            if child.children:
                new_child._add_from(child, predicate=None)
        return

    def add_child(
        self,
        child: Self | TypedTree | TData,
        *,
        kind: str | None,
        before: Self | bool | int | None = None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> Self:
        """Append or insert a typed node or branch below this node.

        Args:
            kind: Kind of the new node. If ``None``, use ``child.kind`` when
                ``child`` is a node, otherwise
                :attr:`~nutree.typed_tree.TypedTree.DEFAULT_CHILD_TYPE`.

        See :meth:`~nutree.node.Node.add_child` for the ``before`` and ``deep``
        options.
        """
        # assert not isinstance(child, TypedNode) or child.kind == self.kind
        # TODO: kind is optional if child is a TypedNode
        # TODO: Check if target and child types match
        # TODO: share more code from overloaded method
        if kind is None:
            if isinstance(child, TypedNode):
                kind = child.kind
            else:
                kind = cast(TypedTree, self._tree).DEFAULT_CHILD_TYPE

        if isinstance(child, (Node, Tree)) and not isinstance(
            child, (TypedNode, TypedTree)
        ):
            raise TypeError("If child is a node or tree it must be typed.")

        if isinstance(child, TypedTree):
            if deep is None:
                deep = True
            topnodes = cast(list[Self], child.system_root.children)
            if isinstance(before, (int, Node)) or before is True:
                topnodes.reverse()
            for n in topnodes:
                self.add_child(
                    n,
                    kind=n.kind,
                    before=before,
                    deep=deep,
                )
            return child.system_root  # type: ignore

        source_node: Self = None  # type: ignore
        new_node: Self = None  # type: ignore
        factory: type[Self] = self._tree.node_factory  # type: ignore

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
                kind,
                cast(TData, child),
                parent=self,
                data_id=data_id,
                node_id=node_id,
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

    # NOTE: mypy cannot handle this alias correctly, so we have to write the
    #       method signature again:
    # #: Alias for :meth:`add_child`
    # add = add_child
    def add(
        self,
        child: Self | TypedTree | TData,
        *,
        kind: str | None,
        before: Self | bool | int | None = None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> Self:
        """Alias for :meth:`add_child`."""
        return self.add_child(
            child,
            kind=kind,
            before=before,
            deep=deep,
            data_id=data_id,
            node_id=node_id,
        )

    def append_child(
        self,
        child: Self | TypedTree | TData,
        *,
        kind: str | None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> Self:
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
        child: Self | TypedTree | TData,
        *,
        kind: str | None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> Self:
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
        child: Self | TypedTree | TData,
        *,
        kind: str | None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> Self:
        """Add a new node **of same kind** before `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        return self._parent.add_child(
            child, kind=kind, before=self, deep=deep, data_id=data_id, node_id=node_id
        )

    def append_sibling(
        self,
        child: Self | TypedTree | TData,
        *,
        kind: str | None,
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

    def copy(
        self,
        *,
        add_self: bool = True,
        predicate: PredicateCallbackType | None = None,
    ) -> TypedTree[TData]:
        """Return a new :class:`~nutree.typed_tree.TypedTree` instance from this branch.

        See also :ref:`iteration-callbacks`.
        """
        new_tree = cast(
            "TypedTree[TData]",
            self._tree.__class__(calc_data_id=self._tree._calc_data_id_hook),
        )
        if add_self:
            root = new_tree.add(self, kind=self.kind)
        else:
            root = new_tree.system_root
        root._add_from(self, predicate=predicate)
        return new_tree

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
        add_self: bool = False,
        unique_nodes: bool = True,
        graph_attrs: dict[str, Any] | None = None,
        node_attrs: dict[str, Any] | None = None,
        edge_attrs: dict[str, Any] | None = None,
        node_mapper: DotMapperCallbackType | None = None,
        edge_mapper: DotMapperCallbackType | None = None,
    ) -> Iterator[str]:
        """Generate a DOT graph representation with kind-labelled edges.

        See :ref:`graphs` for details.
        """

        # TypedNodes can provide labelled edges:
        def _edge_mapper(node: Node, data: dict[str, Any]) -> dict[str, Any] | None:
            data["label"] = node.kind
            if edge_mapper:
                return edge_mapper(node, data)
            return None

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
        self._tree: TypedTree = tree
        self._parent = None  # type: ignore
        self._node_id = ROOT_NODE_ID
        self._data_id = ROOT_DATA_ID
        self._data = tree.name
        self._children = []
        self._meta = None
        self._kind = None  # type: ignore


# ------------------------------------------------------------------------------
# - TypedTree
# ------------------------------------------------------------------------------


class TypedTree(Tree[TData, TypedNode[TData]]):
    """
    :class:`~nutree.tree.Tree` variant whose nodes have a string ``kind``.

    See :ref:`typed-tree` for the typed-node model and kind-specific operations.
    """

    node_factory: type[TypedNode] = cast(type[TypedNode], TypedNode)
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
    ) -> None:
        super().__init__(
            name=name,
            calc_data_id=calc_data_id,
            forward_attrs=forward_attrs,
            check_dag=True,
        )
        self._system_root = self.root_node_factory(self)

    @classmethod
    def deserialize_mapper(
        cls, parent: Node, data: dict[str, Any]
    ) -> str | object | None:
        """Used as default `mapper` argument for :meth:`load`."""
        if "str" in data and len(data) <= 2:
            # This can happen if the source was generated without a
            # serialization mapper, for a TypedTree that has pure str nodes
            return cast(str, data["str"])
        raise NotImplementedError(
            f"Override this method or pass a mapper callback to evaluate {data}."
        )

    def deepcopy(
        self,
        *,
        name: str | None = None,
        memo: dict[int, Any] | None = None,
    ) -> TypedTree[TData]:
        """Return a deep copy of this tree.

        New :class:`~nutree.typed_tree.TypedTree`
        and :class:`~nutree.typed_tree.TypedNode` instances are created.
        The new nodes reference deep-copied data objects (created using the system
        `copy.deepcopy` function).

        See Node's :meth:`~nutree.tree.Tree.copy` and :ref:`iteration-callbacks`
        method for details.
        """
        if name is None:
            name = self.name
        if memo is None:
            memo = {}

        new_tree = self.__class__(name, calc_data_id=self._calc_data_id_hook)

        def _copy_children(source_parent, target_parent) -> None:
            for c in source_parent.children:
                new_data = copy.deepcopy(c.data, memo)

                # Let the new tree calculate the new data_id unless the original node
                # had a custom data_id, in which case we keep it
                if c.data_id == self.calc_data_id(c.data):
                    new_data_id = None
                else:
                    new_data_id = c.data_id

                new_node = target_parent.add(
                    new_data, deep=False, data_id=new_data_id, kind=c.kind
                )
                _copy_children(c, new_node)

        with self:
            _copy_children(self.system_root, new_tree.system_root)

        return new_tree

    def _check_insert(self, node: TypedNode[TData]):
        """Raise error if inserting a node would violate DAG restrictions."""
        # We can assume that node.parent is set and that node already has at
        # least one clone registered in self._nodes_by_data_id, when this is
        # called from _register()
        assert node._kind, node
        ref_key = node._data_id
        kind = node._kind
        if node._parent._children:
            for sibling in node._parent._children:
                if sibling._data_id == ref_key and sibling._kind == kind:
                    raise UniqueConstraintError(
                        f"Node with data_id {ref_key} and kind {kind} "
                        f"already exists in parent {node._parent}"
                    )
        for n in self._nodes_by_data_id[ref_key]:
            if node.is_descendant_of(n) and n._kind == kind:
                raise CycleDetectedError(
                    f"Inserting {node} would create a cycle with {n}"
                )

    def add_child(
        self,
        child: TypedNode[TData] | Self | TData,
        *,
        kind: str | None,
        before: TypedNode[TData] | bool | int | None = None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> TypedNode[TData]:
        """Add a top-level typed node; an alias for :meth:`add`.

        See Node's :meth:`~nutree.typed_tree.TypedNode.add_child` method for details.
        """
        return self.system_root.add_child(
            child,
            kind=kind,
            before=before,
            deep=deep,
            data_id=data_id,
            node_id=node_id,
        )

    # NOTE: mypy cannot handle this alias correctly, so we have to write the
    #       method signature again:
    # #: Alias for :meth:`add_child`
    # add = add_child
    def add(
        self,
        child: TypedNode[TData] | Self | TData,
        *,
        kind: str | None,
        before: TypedNode[TData] | bool | int | None = None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> TypedNode[TData]:
        """Add a top-level typed node; an alias for :meth:`add_child`.

        See :meth:`~nutree.typed_tree.TypedNode.add_child` for details.
        """
        return self.system_root.add_child(
            child,
            kind=kind,
            before=before,
            deep=deep,
            data_id=data_id,
            node_id=node_id,
        )

    def first_child(self, kind: str | type[ANY_KIND]) -> TypedNode[TData] | None:
        """Return the first top-level node of ``kind``, or ``None``."""
        return self.system_root.first_child(kind=kind)

    def last_child(self, kind: str | type[ANY_KIND]) -> TypedNode[TData] | None:
        """Return the last top-level node of ``kind``, or ``None``."""
        return self.system_root.last_child(kind=kind)

    @deprecated("Use Tree.iterator(..., kind=...) instead.")
    def iter_by_type(self, kind: str | type[ANY_KIND]) -> Iterator[TypedNode[TData]]:
        """Yield nodes of ``kind``.

        .. deprecated:: 1.1
            Use :meth:`iterator` with the ``kind`` argument instead.
        """
        warnings.warn(
            "Tree.iter_by_type() is deprecated since v1.1, "
            "use Tree.iterator(..., kind=...) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        yield from self.iterator(kind=kind)

    def iterator(
        self,
        method: IterMethod = IterMethod.PRE_ORDER,
        *,
        kind: str | type[ANY_KIND] = ANY_KIND,
    ) -> Iterator[TypedNode[TData]]:
        """Iterate nodes in ``method`` order, optionally filtered by ``kind``.

        Pass :class:`ANY_KIND` to include all kinds. See
        :meth:`~nutree.tree.Tree.iterator`.
        """
        if kind == ANY_KIND:
            yield from super().iterator(method=method)
            return

        for n in super().iterator(method=method):
            if n._kind == kind:
                yield n
        return

    def count_descendants(
        self, *, leaves_only: bool = False, kind: str | type[ANY_KIND] = ANY_KIND
    ) -> int:
        """Count descendants, optionally restricted to ``kind`` or leaves."""
        return self.system_root.count_descendants(leaves_only=leaves_only, kind=kind)

    def save(
        self,
        target: IO[str] | str | Path,
        *,
        compression: bool | int = False,
        mapper: SerializeMapperType | None = None,
        meta: dict[str, Any] | None = None,
        key_map: KeyMapType | bool = True,
        value_map: ValueMapType | bool = True,
    ) -> None:
        """Store this typed tree in a compact JSON file or text stream.

        The default key and value maps include the node ``kind`` field. See
        :ref:`serialize`, :meth:`~nutree.tree.Tree.to_list_iter`, and :meth:`load`.
        """
        # TypedTrees can assume reasaonable defaults for key_map and value_map
        # (key_map is evaluated in base class from TypedTree.DEFAULT_KEY_MAP)

        if value_map is True or isinstance(value_map, dict):
            if value_map is True:
                value_map = self.DEFAULT_VALUE_MAP.copy()

            if "kind" not in value_map:
                counter = Counter[str]()
                for n in self:
                    counter[n.kind] += 1
                value_map.update({"kind": list(counter.keys())})
        else:
            assert value_map is False, value_map

        return super().save(
            target,
            compression=compression,
            mapper=mapper,
            meta=meta,
            key_map=key_map,
            value_map=value_map,
        )

    @classmethod
    def _from_list(
        cls, obj: list[dict[int, Any]], *, mapper: DeserializeMapperType | None = None
    ) -> Self:
        tree = cls()

        if mapper is None:
            mapper = cls.deserialize_mapper

        # System root has index #0:
        node_idx_map: dict[int, TypedNode[TData]] = {0: tree.system_root}

        # Start reading data lines starting at index #1:
        for idx, (parent_idx, data) in enumerate(obj, 1):
            parent = node_idx_map[parent_idx]

            if isinstance(data, str):
                # This can only happen if the source was generated by a plain Tree
                n = parent.add_child(data, kind=cls.DEFAULT_CHILD_TYPE)
            elif isinstance(data, int):
                first_clone = node_idx_map[data]
                n = parent.add_child(
                    first_clone, kind=first_clone.kind, data_id=first_clone.data_id
                )
            else:
                kind = data.get("kind", cls.DEFAULT_CHILD_TYPE)
                data_id = data.get("data_id")
                data_obj = call_dot_mapper(mapper, parent, data)
                n = parent.add_child(data_obj, kind=kind, data_id=data_id)
            # elif isinstance(data, dict) and "str" in data:
            #     # This can happen if the source was generated without a
            #     # serialization mapper, for a TypedTree that has str nodes
            #     n = parent.add_child(data["str"], kind=data.get("kind"))
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
        file_meta: dict[str, Any] | None = None,
    ) -> Self:
        """Create a :class:`TypedTree` from a JSON file or text stream.

        See :meth:`~nutree.tree.Tree.save` and :meth:`~nutree.tree.Tree.load`.
        """
        return super().load(target, mapper=mapper, file_meta=file_meta)

    # @classmethod
    # def build_random_tree(cls, structure_def: dict) -> Self:
    #     """Build a random tree for testing."""
    #     tt = build_random_tree(cls, structure_def)
    #     return tt
