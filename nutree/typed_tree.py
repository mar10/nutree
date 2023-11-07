# (c) 2021-2023 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Declare the :class:`~nutree.tree.TypedTree` class.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import IO, Any, Dict, Iterator, List, Optional, Union

from nutree.common import (
    ROOT_ID,
    CalcIdCallbackType,
    IterMethod,
    KeyMapType,
    MapperCallbackType,
    NodeFactoryType,
    PredicateCallbackType,
    UniqueConstraintError,
    ValueMapType,
    call_mapper,
)

from .node import Node
from .tree import Tree


class ANY_KIND:
    """Special argument value for some methods that access child nodes."""


DEFAULT_CHILD_TYPE = "child"


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
        parent: TypedNode,
        data_id=None,
        node_id=None,
        meta: Dict = None,
    ):
        super().__init__(
            data, parent=parent, data_id=data_id, node_id=node_id, meta=meta
        )
        assert isinstance(kind, str) and kind != ANY_KIND, f"Unsupported `kind`: {kind}"
        self._kind = kind
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

    @property
    def parent(self) -> TypedNode:
        """Return parent node or None for toplevel nodes."""
        p = self._parent
        return p if p._parent else None

    @property
    def children(self) -> List[TypedNode]:
        """Return list of direct child nodes (list may be empty).

        Note that this property returns all children, independent of the kind.
        See also :meth:`get_children`.
        """
        c = self._children
        return [] if c is None else c

    def get_children(self, kind: Union[str, ANY_KIND]) -> List[TypedNode]:
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

    def first_child(self, kind: Union[str, ANY_KIND]) -> Union[TypedNode, None]:
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

    def last_child(self, kind: Union[str, ANY_KIND]) -> Union[TypedNode, None]:
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

    def has_children(self, kind: Union[str, ANY_KIND]) -> bool:
        """Return true if this node has one or more children."""
        if kind is ANY_KIND:
            return bool(self._children)
        return len(self.get_children(kind)) > 1

    def get_siblings(self, *, add_self=False, any_kind=False) -> List[TypedNode]:
        """Return a list of all sibling entries of self (excluding self) if any."""
        if any_kind:
            return super().get_siblings(add_self=add_self)
        children = self._parent._children
        rel = self.kind
        return [n for n in children if (add_self or n is not self) and n.kind == rel]

    def first_sibling(self, *, any_kind=False) -> TypedNode:
        """Return first sibling `of the same kind` (may be self)."""
        pc = self._parent._children
        if any_kind:
            return pc[0]
        for n in pc:
            if n._kind == self._kind:
                return n
        raise AssertionError("Internal error")

    def last_sibling(self, *, any_kind=False) -> TypedNode:
        """Return last sibling `of the same kind` (may be self)."""
        pc = self._parent._children
        if any_kind:
            return pc[-1]
        for n in reversed(pc):
            if n._kind == self._kind:
                return n
        raise AssertionError("Internal error")

    def prev_sibling(self, *, any_kind=False) -> Union[TypedNode, None]:
        """Return predecessor `of the same kind` or None if node is first sibling."""
        pc = self._parent._children
        own_idx = pc.index(self)
        if own_idx > 0:
            for idx in range(own_idx - 1, -1, -1):
                n = pc[idx]
                if any_kind or n._kind == self._kind:
                    return n
        return None

    def next_sibling(self, *, any_kind=False) -> Union[TypedNode, None]:
        """Return successor `of the same kind` or None if node is last sibling."""
        pc = self._parent._children
        pc_len = len(pc)
        own_idx = pc.index(self)

        if own_idx < pc_len - 2:
            for idx in range(own_idx + 1, pc_len):
                n = pc[idx]
                if any_kind or n._kind == self._kind:
                    return n
        return None

    # def get_clones(self, *, add_self=False) -> List[TypedNode]:
    #     """Return a list of all nodes that reference the same data if any."""
    #     clones = self._tree._nodes_by_data_id[self._data_id]
    #     if add_self:
    #         return clones.copy()
    #     return [n for n in clones if n is not self]

    def get_index(self, *, any_kind=False) -> int:
        """Return index in sibling list."""
        if any_kind:
            kc = self._parent._children
        else:
            kc = self.parent.get_children(self.kind)
        return kc.index(self)

    def is_first_sibling(self, *, any_kind=False) -> bool:
        """Return true if this node is the first sibling, i.e. the first child
        of its parent."""
        if any_kind:
            return self is self._parent._children[0]
        return self is self.first_sibling(any_kind=False)

    def is_last_sibling(self, *, any_kind=False) -> bool:
        """Return true if this node is the last sibling, i.e. the last child
        **of this kind** of its parent."""
        if any_kind:
            return self is self._parent._children[-1]
        return self is self.last_sibling(any_kind=False)

    def add_child(
        self,
        child: Union[TypedNode, TypedTree, Any],
        *,
        kind: str = None,
        before: Union[TypedNode, bool, int, None] = None,
        deep: bool = None,
        data_id=None,
        node_id=None,
    ) -> TypedNode:
        """See ..."""
        # assert not isinstance(child, TypedNode) or child.kind == self.kind
        # TODO: kind is optional if child is a TypedNode
        # TODO: Check if target and child types match
        # TODO: share more code from overloaded method
        if kind is None:
            kind = DEFAULT_CHILD_TYPE

        if isinstance(child, (Node, Tree)) and not isinstance(
            child, (TypedNode, TypedTree)
        ):
            raise TypeError("If child is a node or tree it must be typed.")

        if isinstance(child, self._tree.__class__):
            if deep is None:
                deep = True
            topnodes = child._root.children
            if isinstance(before, (int, TypedNode)) or before is True:
                topnodes.reverse()
            for n in topnodes:
                self.add_child(n, before=before, deep=deep)
            return

        source_node = None
        factory = self._tree._node_factory
        if isinstance(child, Node):  # TypedNode):
            if deep is None:
                deep = False
            if deep and data_id is not None or node_id is not None:
                raise ValueError("Cannot set ID for deep copies.")
            source_node = child
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
            child_class = child.__class__

            node = child_class(
                kind,
                source_node.data,
                parent=self,
                data_id=data_id,
                node_id=node_id,
            )
        else:
            node = factory(kind, child, parent=self, data_id=data_id, node_id=node_id)

        children = self._children
        if children is None:
            assert before in (None, True, int, False)
            self._children = [node]
        elif before is True:  # prepend
            children.insert(0, node)
        elif type(before) is int:
            children.insert(before, node)
        elif before:
            if before._parent is not self:
                raise ValueError(
                    f"`before=node` ({before._parent}) "
                    f"must be a child of target node ({self})"
                )
            idx = children.index(before)  # raises ValueError
            children.insert(idx, node)
        else:
            children.append(node)

        if deep and source_node:
            node._add_from(source_node)

        return node

    #: Alias for :meth:`add_child`
    add = add_child

    def append_child(
        self,
        child: Union[TypedNode, TypedTree, Any],
        *,
        kind: str = None,
        deep=None,
        data_id=None,
        node_id=None,
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
        child: Union[TypedNode, TypedTree, Any],
        *,
        kind: str = None,
        deep=None,
        data_id=None,
        node_id=None,
    ):
        """Prepend a new subnode.

        This is a shortcut for :meth:`add_child` with ``before=True``.
        """
        return self.add_child(
            child,
            kind=kind,
            before=self.first_child(),
            deep=deep,
            data_id=data_id,
            node_id=node_id,
        )

    def prepend_sibling(
        self,
        child: Union[TypedNode, TypedTree, Any],
        *,
        deep=None,
        data_id=None,
        node_id=None,
    ) -> TypedNode:
        """Add a new node **of same kind** before `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        return self._parent.add_child(
            child, before=self, deep=deep, data_id=data_id, node_id=node_id
        )

    def append_sibling(
        self,
        child: Union[TypedNode, TypedTree, Any],
        *,
        deep=None,
        data_id=None,
        node_id=None,
    ) -> TypedNode:
        """Add a new node **of same kind** after `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        next_node = self.next_sibling
        return self._parent.add_child(
            child, before=next_node, deep=deep, data_id=data_id, node_id=node_id
        )

    def move_to(
        self,
        new_parent: Union[TypedNode, TypedTree],
        *,
        before: Union[TypedNode, bool, int, None] = None,
    ):
        """Move this node before or after `new_parent`."""
        raise NotImplementedError

    # def remove(self, *, keep_children=False, with_clones=False) -> None:
    #     """Remove this node.

    #     If `keep_children` is true, all children will be moved one level up,
    #     so they become siblings, before this node is removed.

    #     If `with_clones` is true, all nodes that reference the same data
    #     instance are removed as well.
    #     """
    #     raise NotImplementedError

    # def remove_children(self, kind: Union[str, ANY_KIND]):
    #     """Remove all children of this node, making it a leaf node."""
    #     raise NotImplementedError

    def copy(self, *, add_self=True, predicate=None) -> TypedTree:
        """Return a new :class:`~nutree.typed_tree.TypedTree` instance from this branch.

        See also :meth:`_add_from` and :ref:`iteration-callbacks`.
        """
        return super().copy(add_self=add_self, predicate=predicate)

    def filtered(self, predicate: PredicateCallbackType) -> TypedTree:
        """Return a filtered copy of this node and descendants as tree.

        See also :ref:`iteration-callbacks`.
        """
        return super().filtered(predicate=predicate)

    def iterator(
        self, method=IterMethod.PRE_ORDER, *, add_self=False
    ) -> Iterator[Node]:
        """Generator that walks the hierarchy."""
        return super().iterator(method=method, add_self=add_self)

    #: Implement ``for subnode in node: ...`` syntax to iterate descendant nodes.
    __iter__ = iterator

    # def sort_children(self, *, key=None, reverse=False, deep=False):
    #     """Sort child nodes.

    #     `key` defaults to ``attrgetter("name")``, so children are sorted by
    #     their string representation.
    #     """
    #     cl = self._children
    #     if not cl or len(cl) == 1 and not deep:
    #         return
    #     if key is None:
    #         key = attrgetter("name")
    #     cl.sort(key=key, reverse=reverse)
    #     if deep:
    #         for c in cl:
    #             c.sort_children(key=key, reverse=reverse, deep=True)
    #     return

    # def _get_prefix(self, style, lstrip):
    #     s0, s1, s2, s3 = style

    #     parts = []
    #     depth = 0
    #     for p in self.get_parent_list():
    #         depth += 1
    #         if depth <= lstrip:
    #             continue
    #         if p.is_last_sibling():
    #             parts.append(s0)  # "    "
    #         else:
    #             parts.append(s1)  # " |  "

    #     if depth >= lstrip:
    #         if self.is_last_sibling():
    #             parts.append(s2)  # " ╰─ "
    #         else:
    #             parts.append(s3)  # " ├─ "

    #     return "".join(parts)

    # def _render_lines(self, *, repr=None, style=None, add_self=True):
    #     if type(style) not in (list, tuple):
    #         try:
    #             style = CONNECTORS[style or self.tree.DEFAULT_CONNECTOR_STYLE]
    #         except KeyError:
    #             raise ValueError(
    #                 f"Invalid style '{style}'. "
    #                 f"Expected: {'|'.join(CONNECTORS.keys())}"
    #             )

    #     if repr is None:
    #         repr = DEFAULT_NAME_REPR

    #     # Find out if we need to strip some of the leftmost prefixes.
    #     # If this was called for a normal node, we strip all parent levels
    #     # (and also the own prefix when `add_self` is false).
    #     # If this was called for the system root node, we do the same, but we
    #     # never render self, because the the title is rendered by the caller.
    #     lstrip = self.depth()
    #     if not add_self:
    #         lstrip += 1
    #     if not self._parent:
    #         add_self = False

    #     for n in self.iterator(add_self=add_self):
    #         prefix = n._get_prefix(style, lstrip)

    #         if callable(repr):
    #             s = repr(n)
    #         else:
    #             s = repr.format(node=n)

    #         yield prefix + s

    #     return

    # def to_dict(self, *, mapper: MapperCallbackType = None) -> Dict:
    #     """Return a nested dict of this node and its children."""
    #     res = {
    #         "data": str(self.data),
    #     }
    #     # Add custom data_id if any
    #     # data_id = hash(self._data)
    #     data_id = self._tree._calc_data_id(self._data)
    #     if data_id != self._data_id:
    #         res["data_id"] = data_id
    #     res = call_mapper(mapper, self, res)
    #     # if mapper:
    #     #     res = mapper(self, res)
    #     if self._children:
    #         res["children"] = cl = []
    #         for n in self._children:
    #             cl.append(n.to_dict(mapper=mapper))
    #     return res

    @classmethod
    def _make_list_entry(cls, node: TypedNode) -> dict:
        node_data = node._data
        # is_custom_id = node._data_id != hash(node_data)

        if type(node_data) is str:
            # Node._make_list_entry() would return a plain str, but we always
            # need a dict
            data = {
                "str": node_data,
            }
        else:
            data = Node._make_list_entry(node)

        if node.kind != ANY_KIND:
            data["kind"] = node.kind
        return data

    def to_dot(
        self,
        *,
        add_self=False,
        unique_nodes=True,
        graph_attrs: dict = None,
        node_attrs: dict = None,
        edge_attrs: dict = None,
        node_mapper: MapperCallbackType = None,
        edge_mapper: MapperCallbackType = None,
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
# - TypedTree
# ------------------------------------------------------------------------------
class TypedTree(Tree):
    """
    A special tree variant, derived from :class:`~nutree.tree.Tree`,
    that uses :class:`~nutree.typed_tree.TypedNode` objects, which maintain
    an addition `kind` attribute.

    See :ref:`typed-tree` for details.
    """

    #: Default value for ``key_map`` argument when saving
    DEFAULT_KEY_MAP = {"data_id": "i", "str": "s", "kind": "k"}
    #: Default value for ``value_map`` argument when saving
    DEFAULT_VALUE_MAP = {}  # expands to { "kind": [<distinct `kind` values>] }

    def __init__(
        self,
        name: str = None,
        *,
        factory: NodeFactoryType = None,
        calc_data_id: CalcIdCallbackType = None,
        shadow_attrs: bool = False,
    ):
        if factory is None:
            factory = TypedNode
        super().__init__(
            name, factory=factory, calc_data_id=calc_data_id, shadow_attrs=shadow_attrs
        )
        self._root = _SystemRootTypedNode(self)

    def __getitem__(self, data: object) -> TypedNode:
        return super().__getitem__(data)

    def add_child(
        self,
        child: Union[TypedNode, TypedTree, Any],
        *,
        kind: str = None,
        before: Union[TypedNode, bool, int, None] = None,
        deep: bool = None,
        data_id=None,
        node_id=None,
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

    def first_child(self, kind: Union[str, ANY_KIND]) -> Union[TypedNode, None]:
        """Return the first toplevel node."""
        return self._root.first_child(kind=kind)

    def last_child(self, kind: Union[str, ANY_KIND]) -> Union[TypedNode, None]:
        """Return the last toplevel node."""
        return self._root.last_child(kind=kind)

    def iter_by_type(self, kind: Union[str, ANY_KIND]) -> Iterator[TypedNode]:
        if kind == ANY_KIND:
            return self.iterator()
        for n in self.iterator():
            if n._kind == kind:
                yield n
        return

    @classmethod
    def _from_list(cls, obj: List[Dict], *, mapper=None) -> TypedTree:
        tree = cls()

        # System root has index #0:
        node_idx_map = {0: tree._root}

        # Start reading data lines starting at index #1:
        for idx, (parent_idx, data) in enumerate(obj, 1):
            parent = node_idx_map[parent_idx]
            # print(idx, parent_idx, data, parent)
            if type(data) is str:
                # This can only happen if the source was generated by a plain Tree
                n = parent.add(data, kind=DEFAULT_CHILD_TYPE)
            elif type(data) is int:
                first_clone = node_idx_map[data]
                n = parent.add(
                    first_clone, kind=first_clone.kind, data_id=first_clone.data_id
                )
            elif mapper:
                kind = data.get("kind", DEFAULT_CHILD_TYPE)
                data_id = data.get("data_id")
                data_obj = call_mapper(mapper, parent, data)
                n = parent.add(data_obj, kind=kind, data_id=data_id)
            elif isinstance(data, dict) and "str" in data:
                # This can happen if the source was generated without a
                # serialization mapper, for a TypedTree that has str nodes
                n = parent.add(data["str"], kind=data.get("kind"))
            else:
                raise RuntimeError(f"Need mapper for {data}")  # pragma: no cover

            node_idx_map[idx] = n

        return tree

    def save(
        self,
        target: Union[IO[str], str, Path],
        *,
        mapper: Optional[MapperCallbackType] = None,
        meta: Optional[dict] = None,
        key_map: Union[KeyMapType, bool] = True,
        value_map: Union[ValueMapType, bool] = True,
    ) -> None:
        """Store tree in a compact JSON file stream.

        See also :meth:`to_list_iter` and :meth:`load` methods.
        """
        # TypedTrees can assume reasaonable defaults for key_map and value_map
        # (key_map is evaluated in base class from TypedTree.DEFAULT_KEY_MAP)

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
    def load(
        cls,
        target: Union[IO[str], str, Path],
        *,
        mapper=None,
        file_meta: dict = None,
    ) -> TypedTree:
        """Create a new :class:`TypedTree` instance from a JSON file stream.

        See also Tree's :meth:`~nutree.tree.Tree.save()` and
        :meth:`~nutree.tree.Tree.load()` methods.
        """
        return super().load(target, mapper=mapper, file_meta=file_meta)


# ------------------------------------------------------------------------------
# - _SystemRootTypedNode
# ------------------------------------------------------------------------------
class _SystemRootTypedNode(TypedNode):
    """Invisible system root node."""

    def __init__(self, tree: TypedTree) -> None:
        self._tree: TypedTree = tree
        self._parent = None
        self._node_id = self._data_id = ROOT_ID
        self._data = tree.name
        self._children = []
        self._meta = None
        self._kind = None
