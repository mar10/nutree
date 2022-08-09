# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Declare the :class:`~nutree.tree.TypedTree` class.
"""
from typing import Any, Dict, Generator, List, Union

from nutree.common import (
    IterMethod,
    MapperCallbackType,
    PredicateCallbackType,
    UniqueConstraintError,
)

from .node import Node
from .tree import Tree


class ANY_TYPE:
    """Special argument value for some methods that access child nodes."""


DEFAULT_CHILD_TYPE = "child"


# ------------------------------------------------------------------------------
# - TypedNode
# ------------------------------------------------------------------------------
class TypedNode(Node):
    """
    A special node variant, derived from :class:`~nutree.node.Node` and
    used by :class:`~nutree.typed_tree.TypedTree`.
    """

    __slots__ = ("_kind",)

    def __init__(
        self,
        kind: str,
        data,
        *,
        parent: "TypedNode",
        data_id=None,
        node_id=None,
        meta: Dict = None,
    ):
        super().__init__(
            data, parent=parent, data_id=data_id, node_id=node_id, meta=meta
        )
        assert isinstance(kind, str) and kind != ANY_TYPE
        self._kind = kind
        # del self._children
        # self._child_map: Dict[Node] = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.name!r}, data_id={self.data_id}>"

    @property
    def name(self) -> str:
        """String representation of the embedded `data` object with kind."""
        return f"{self._kind} → {self.data}"
        # Inspired by clarc notation: http://www.jclark.com/xml/xmlns.htm
        # return f"{{{self._kind}}}:{self.data}"
        # return f"{self.data}"

    @property
    def kind(self) -> str:
        return self._kind

    def children(self, kind: Union[str, ANY_TYPE]) -> List["TypedNode"]:
        """Return list of direct child nodes of a given type (list may be empty)."""
        all_children = self._children
        if not all_children:
            return []
        elif kind is ANY_TYPE:
            return all_children
        return list(filter(lambda n: n._kind == kind, all_children))

    # def set_data(
    #     self, kind: str, data, *, data_id=None, with_clones: bool = None
    # ) -> None:
    #     """Change node's `data` and/or `data_id` and update bookkeeping."""
    #     super().set_data(data, data_id=data_id, with_clones=with_clones)

    def first_child(self, kind: Union[str, ANY_TYPE]) -> Union["TypedNode", None]:
        """First direct childnode or None if no children exist."""
        all_children = self._children
        if not all_children:
            return None
        elif kind is ANY_TYPE:
            return all_children[0]

        for n in all_children:
            if n._kind == kind:
                return n
        return None

    def last_child(self, kind: Union[str, ANY_TYPE]) -> Union["TypedNode", None]:
        """Last direct childnode or None if no children exist."""
        all_children = self._children
        if not all_children:
            return None
        elif kind is ANY_TYPE:
            return all_children[-1]

        for i in range(len(all_children) - 1, -1, -1):
            n = all_children[i]
            if n._kind == kind:
                return n
        return None

    @property
    def first_sibling(self) -> "TypedNode":
        """Return first sibling **of the same kind** (may be self)."""
        raise NotImplementedError

    @property
    def last_sibling(self) -> "TypedNode":
        """Return last sibling **of the same kind** (may be self)."""
        raise NotImplementedError

    @property
    def prev_sibling(self) -> Union["TypedNode", None]:
        """Return predecessor **of the same kind** or None, if node is first sibling."""
        raise NotImplementedError

    @property
    def next_sibling(self) -> Union["TypedNode", None]:
        """Return successor **of the same kind** or None, if node is last sibling."""
        raise NotImplementedError

    def get_siblings(self, *, add_self=False, any_type=False) -> List["TypedNode"]:
        """Return a list of all sibling entries of self (excluding self) if any."""
        children = self._parent._children
        if any_type:
            if add_self:
                return children
            return [n for n in children if n is not self]
        rel = self.kind
        return [n for n in children if (add_self or n is not self) and n.kind == rel]

    # def get_clones(self, *, add_self=False) -> List["TypedNode"]:
    #     """Return a list of all nodes that reference the same data if any."""
    #     clones = self._tree._nodes_by_data_id[self._data_id]
    #     if add_self:
    #         return clones.copy()
    #     return [n for n in clones if n is not self]

    def get_index(self, *, any_type=False) -> int:
        """Return index in sibling list."""
        assert any_type
        return self._parent._children.index(self)

    # --------------------------------------------------------------------------

    def is_first_sibling(self, *, any_type=False) -> bool:
        """Return true if this node is the first sibling, i.e. the first child of its parent."""
        assert any_type
        return self is self._parent._children[0]

    def is_last_sibling(self, *, any_type=False) -> bool:
        """Return true if this node is the last sibling, i.e. the last child
        **of this kind** of its parent."""
        assert any_type
        return self is self._parent._children[-1]

    def has_children(self, kind: Union[str, ANY_TYPE]) -> bool:
        """Return true if this node has one or more children."""
        assert kind is ANY_TYPE
        return bool(self._children)

    # --------------------------------------------------------------------------

    def add_child(
        self,
        child: Union["TypedNode", "TypedTree", Any],
        *,
        kind: str = None,
        before: Union["TypedNode", bool, int, None] = None,
        deep: bool = None,
        data_id=None,
        node_id=None,
    ) -> "TypedNode":
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
        if isinstance(child, TypedNode):
            if deep is None:
                deep = False
            if deep and data_id is not None or node_id is not None:
                raise ValueError("Cannot set ID for deep copies.")
            source_node = child
            if source_node._tree is self._tree:
                if source_node._parent is self._parent:
                    raise UniqueConstraintError(
                        f"Same parent not allowed: {source_node}"
                    )
            else:
                pass
                # raise NotImplementedError("Cross-tree adding")
            if data_id and data_id != source_node._data_id:
                raise UniqueConstraintError(f"data_id conflict: {source_node}")
            node = TypedNode(
                kind,
                source_node.data,
                parent=self,
                data_id=data_id,
                node_id=node_id,
            )
        else:
            node = TypedNode(kind, child, parent=self, data_id=data_id, node_id=node_id)

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
                raise ValueError("`before=node` argument must be a child of this node")
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
        child: Union["TypedNode", "TypedTree", Any],
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
        child: Union["TypedNode", "TypedTree", Any],
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
            before=self.first_child,
            deep=deep,
            data_id=data_id,
            node_id=node_id,
        )

    def prepend_sibling(
        self,
        child: Union["TypedNode", "TypedTree", Any],
        *,
        deep=None,
        data_id=None,
        node_id=None,
    ) -> "TypedNode":
        """Add a new node **of same kind** before `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        return self._parent.add_child(
            child, before=self, deep=deep, data_id=data_id, node_id=node_id
        )

    def append_sibling(
        self,
        child: Union["TypedNode", "TypedTree", Any],
        *,
        deep=None,
        data_id=None,
        node_id=None,
    ) -> "TypedNode":
        """Add a new node **of same kind** after `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        next_node = self.next_sibling
        return self._parent.add_child(
            child, before=next_node, deep=deep, data_id=data_id, node_id=node_id
        )

    def move(
        self,
        new_parent: Union["TypedNode", "TypedTree"],
        *,
        before: Union["TypedNode", bool, int, None] = None,
    ):
        """Move this node before or after `otherNode` ."""
        raise NotImplementedError

    def remove(self, *, keep_children=False, with_clones=False) -> None:
        """Remove this node.

        If `keep_children` is true, all children will be moved one level up,
        so they become siblings, before this node is removed.

        If `with_clones` is true, all nodes that reference the same data
        instance are removed as well.
        """
        raise NotImplementedError

    def remove_children(self, kind: Union[str, ANY_TYPE]):
        """Remove all children of this node, making it a leaf node."""
        raise NotImplementedError

    def copy(self, *, add_self=True, predicate=None) -> "TypedTree":
        """Return a new :class:`~nutree.typed_tree.TypedTree` instance from this branch.

        See also :meth:`_add_from` and :ref:`iteration callbacks`.
        """
        return super().copy(add_self=add_self, predicate=predicate)

    def filtered(self, predicate: PredicateCallbackType) -> "TypedTree":
        """Return a filtered copy of this node and descendants as tree.

        See also :ref:`iteration callbacks`.
        """
        return super().filtered(predicate=predicate)

    def iterator(
        self, method=IterMethod.PRE_ORDER, *, add_self=False
    ) -> Generator["TypedNode", None, None]:
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
    #             style = CONNECTORS[style or DEFAULT_CONNECTOR_STYLE]
    #         except KeyError:
    #             raise ValueError(
    #                 f"Invalid style '{style}'. Expected: {'|'.join(CONNECTORS.keys())}"
    #             )

    #     if repr is None:
    #         repr = DEFAULT_REPR

    #     # Find out if we need to strip some of the leftmost prefixes.
    #     # If this was called for a normal node, we strip all parent levels
    #     # (and also the own prefix when `add_self` is false).
    #     # If this was called for the system root node, we do the same, but we
    #     # never render self, because the the title is rendered by the caller.
    #     lstrip = self.depth
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

    # def to_list_iter(
    #     self, *, mapper: MapperCallbackType = None
    # ) -> Generator[Dict, None, None]:
    #     """Yield children as parent-referencing list.

    #     ```py
    #     [(parent_key, data)]
    #     ```
    #     """
    #     calc_id = self._tree._calc_data_id
    #     #: For nodes with multiple occurrences: index of the first one
    #     clone_idx_map = {}
    #     parent_id_map = {self._node_id: 0}

    #     for id_gen, node in enumerate(self, 1):
    #         # Compact mode: use integer sequence as keys
    #         # Store idx with original id for later parent-ref. We only have to
    #         # do this of nodes that have children though:
    #         node_id = node._node_id
    #         if node._children:
    #             parent_id_map[node_id] = id_gen

    #         parent_id = node._parent._node_id
    #         parent_idx = parent_id_map[parent_id]

    #         data = node._data
    #         data_id = calc_id(data)
    #         # data_id = hash(data)

    #         # If node is a 2nd occurence of a clone, only store the index of the
    #         # first occurence and do not call the mapper
    #         clone_idx = clone_idx_map.get(data_id)
    #         if clone_idx:
    #             yield (parent_idx, clone_idx)
    #             continue
    #         elif node.is_clone():
    #             clone_idx_map[data_id] = id_gen

    #         # If data is more complex than a simple string, or if we use a custom
    #         # data_id, we store data as a dict instead of a str:
    #         if type(data) is str:
    #             if data_id != node._data_id:
    #                 data = {
    #                     "str": data,
    #                     "id": data_id,
    #                 }
    #             # else: data is stored as-is, i.e. plain string instead of dict
    #         else:
    #             data = {
    #                 # "id": data_id,
    #             }
    #         # Let caller serialize custom data objects
    #         data = call_mapper(mapper, node, data)
    #         # if mapper:
    #         #     data = mapper(node, data)

    #         yield (parent_idx, data)
    #     return

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
    ) -> Generator[str, None, None]:
        """Generate a DOT formatted graph representation.

        See :ref:`Graphs` for details.
        """

        def _node_mapper(node, data):
            data["label"] = f"{node.data}"
            if node_mapper:
                return node_mapper(node, data)

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
            node_mapper=_node_mapper,
            edge_mapper=_edge_mapper,
        )
        return res


# ------------------------------------------------------------------------------
# - TypedTree
# ------------------------------------------------------------------------------
class TypedTree(Tree):
    """
    A special tree variant, derived from :class:`~nutree.tree.Tree`.

    See :ref:`Typed Tree` for details.
    """

    def __init__(self, name: str = None, *, factory=None, calc_data_id=None):
        if factory is None:
            factory = TypedNode
        super().__init__(name, factory=factory, calc_data_id=calc_data_id)
        self._root = _SystemRootTypedNode(self)

    def __getitem__(self, data: object) -> "TypedNode":
        return super().__getitem__(data)

    def add_child(
        self,
        child: Union["TypedNode", "TypedTree", Any],
        *,
        kind: str = None,
        before: Union["TypedNode", bool, int, None] = None,
        deep: bool = None,
        data_id=None,
        node_id=None,
    ) -> "TypedNode":
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

    def iter_by_type(self, kind: Union[str, ANY_TYPE]):
        if kind == ANY_TYPE:
            return self.iter()
        raise NotImplementedError


# ------------------------------------------------------------------------------
# - _SystemRootTypedNode
# ------------------------------------------------------------------------------
class _SystemRootTypedNode(TypedNode):
    """Invisible system root node."""

    def __init__(self, tree: TypedTree):

        self._tree: TypedTree = tree
        self._parent = None
        self._node_id = self._data_id = "__root__"
        self._data = tree.name
        self._children = []
        self._meta = None
        self._kind = None

    # @property
    # def name(self) -> str:
    #     return self.tree.name
