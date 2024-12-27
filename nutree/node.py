# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Declare the :class:`~nutree.node.Node` class.
"""
# Mypy reports some errors that are not reported by pyright, and there is no
# way to suppress them with `type: ignore`, because then pyright will report
# an 'Unnecessary "# type: ignore" comment'. For now, we disable the errors
# globally for mypy:

# mypy: disable-error-code="truthy-function, arg-type"

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from operator import attrgetter
from pathlib import Path
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Generic,
    cast,
)

# typing.Self requires Python 3.11
# TypeVar(..., default="Node") requires Python 3.13
from typing_extensions import Self, TypeVar

from nutree.mermaid import (
    MermaidDirectionType,
    MermaidEdgeMapperCallbackType,
    MermaidFormatType,
    MermaidNodeMapperCallbackType,
    node_to_mermaid_flowchart,
)

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from nutree.tree import Tree


from nutree.common import (
    CONNECTORS,
    DataIdType,
    DeserializeMapperType,
    FlatJsonDictType,
    IterMethod,
    KeyMapType,
    MapperCallbackType,
    MatchArgumentType,
    PredicateCallbackType,
    ReprArgType,
    SelectBranch,
    SerializeMapperType,
    SkipBranch,
    SortKeyType,
    StopTraversal,
    TraversalCallbackType,
    UniqueConstraintError,
    ValueDictMapType,
    ValueMapType,
    call_mapper,
    call_predicate,
    call_traversal_cb,
)
from nutree.dot import node_to_dot
from nutree.rdf import RDFMapperCallbackType, node_to_rdf

TData = TypeVar("TData", bound="Any", default="Any")
TNode = TypeVar("TNode", bound="Node", default="Node[TData]")


# ------------------------------------------------------------------------------
# - Node
# ------------------------------------------------------------------------------
class Node(Generic[TData]):
    """
    A Node represents a single element in the tree.
    It is a shallow wrapper around a user data instance, that adds navigation,
    modification, and other functionality.

    Node objects are rarely created using this contructor, but indirectly by
    invoking helper methods like :meth:`~nutree.node.Node.add_child`, etc.

    `data`
        is the arbitrary object that this node will hold.
    `parent`
        is the parent :meth:`~nutree.node.Node` instance. This node will
        also inherit the tree reference from it.
    `data_id`
        is an optional integer or string that will be used as ID
        (instead of calculating ``hash(data)``).
        A tree may contain more than one node with the same data and data_id.
        In this case we call the nodes 'clones'.
    `node_id`
        is an optional integer, that is used as unique ID for this node.
        Even 'clones' must have unique node IDs. The default is calculated as
        `id(self)`.
    `meta`
        is an optional dictionary. See also :meth:`~nutree.node.Node.get_meta`,
        :meth:`~nutree.node.Node.set_meta`, :meth:`~nutree.node.Node.update_meta`,
        and :meth:`~nutree.node.Node.clear_meta`.

    """

    # Slots may reduce node size (about 20% smaller):
    __slots__ = (
        "__weakref__",  # Allow weak references to Nodes
        "_children",
        "_data_id",
        "_data",
        "_meta",
        "_node_id",
        "_parent",
        "_tree",
    )
    #: Default value for ``repr`` argument when formatting data for print/display.
    DEFAULT_RENDER_REPR = "{node.data!r}"

    # #: Default value for ``repr`` argument when formatting data for export,
    # #: like DOT, RDF, ...
    # DEFAULT_NAME_REPR = "{node.data!r}"
    # # DEFAULT_NAME_REPR = "{node.data}"

    def __init__(
        self,
        data: TData,
        *,
        parent: Self,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
        meta: dict | None = None,
    ):
        self._data: TData = data
        self._parent: Self = parent

        tree = parent._tree
        self._tree: Tree[Self] = tree
        self._children: list[Self] | None = None

        if data_id is None:
            self._data_id: DataIdType = tree.calc_data_id(data)
        else:
            self._data_id = data_id

        if node_id is None:
            self._node_id: int = id(self)
        else:
            self._node_id = int(node_id)

        self._meta = meta

        tree._register(self)  # type: ignore

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.name!r}, data_id={self.data_id}>"

    def __eq__(self, other: Any) -> bool:
        """Implement ``node == other`` syntax to compare embedded data.

        If `other` is a :class:`Node` instance, ``self.data == other.data`` is
        evaluated.
        Otherwise ``self.data == other`` is compared.

        Use ``node is other`` syntax instead to check if two nodes are truly
        identical.
        """
        if isinstance(other, Node):
            return cast(bool, self._data == other._data)
        return cast(bool, self._data == other)

    def __getattr__(self, name: str) -> Any:
        """Implement ``node.NAME`` aliasing  to ``node.data.NAME``.

        See :ref:`forward-attributes`.
        """
        if self._tree._forward_attrs:
            return getattr(self._data, name)
        # Allow calling simple methods from within TEMPLATE.format(),
        # e.g. `"{node.path()}"`:
        if name.endswith("()"):
            return getattr(self, name[:-2])()
        raise AttributeError(repr(name))

    # Do not define __len__: we don't want leaf nodes to evaluate as falsy
    # def __len__(self) -> int:
    #     raise NotImplementedError("Use `len(node.data)` or `len(node._children)`.")

    @property
    def name(self) -> str:
        """String representation of the embedded `data` object."""
        return f"{self.data}"

    @property
    def path(self) -> str:
        """All ancestor names including self, starting with and separated by '/'."""
        return self.get_path(repr="{node.name}")

    @property
    def tree(self) -> Tree[Self]:
        """Return container :class:`~nutree.tree.Tree` instance."""
        return self._tree

    @property
    def parent(self) -> Self | None:
        """Return parent node or None for toplevel nodes.

        See also :meth:`~nutree.node.Node.up`.
        """
        p = self._parent
        return p if p._parent else None

    def up(self, level: int = 1) -> Self:
        """Return ancestor node.

        Unlike :meth:`~nutree.node.Node.parent`, this method returns the
        system root node for toplevel nodes.

        One use case is method chaining when creating trees::

            tree = Tree().add("n1").add("child1").up().add("child2").up(2).add("n2")
        """
        if level < 1:
            raise ValueError("Level must be positive")
        p = self
        while level > 0:
            p = p._parent
            if p is None:
                raise ValueError("Cannot go up beyond system root node")
            level -= 1
        return p

    @property
    def children(self) -> list[Self]:
        """Return list of direct child nodes (list may be empty)."""
        c = self._children
        return [] if c is None else c

    @property
    def data(self) -> TData:
        """Return the wrapped data instance (use :meth:`~nutree.tree.Tree.set_data()`
        to modify)."""
        return self._data

    @property
    def data_id(self) -> DataIdType:
        """Return the wrapped data instance's id
        (use :meth:`~nutree.tree.Tree.set_data()` to modify)."""
        return self._data_id

    @property
    def node_id(self) -> int:
        """Return the node's unique key."""
        return self._node_id

    @property
    def meta(self) -> dict | None:
        """Return the node's metadata dictionary or None if empty.

        See also :meth:`get_meta`, :meth:`set_meta`, :meth:`update_meta`,
        :meth:`clear_meta`.
        """
        return self._meta

    def get_meta(self, key: str, default=None) -> Any:
        """Return metadata value."""
        m = self._meta
        return default if m is None else m.get(key, default)

    def set_meta(self, key: str, value) -> None:
        """Set metadata value (pass value `None` to remove)."""
        if value is None:
            self.clear_meta(key)
        elif self._meta is None:
            self._meta = {key: value}
        else:
            self._meta[key] = value

    def clear_meta(self, key: str | None = None) -> None:
        """Reset all metadata or a distinct entry."""
        if key is None:
            self._meta = None
            return
        m = self._meta
        if m is not None:
            m.pop(key, None)
            if len(m) == 0:
                self._meta = None
        return

    def update_meta(self, values: dict, *, replace: bool = False) -> None:
        """Add `values` dict to current metadata.

        If `replace` is true, previous metatdata will be cleared.
        """
        if replace or self._meta is None:
            self._meta = values.copy()
        else:
            self._meta.update(values)

    def rename(self, new_name: str) -> None:
        """Set `self.data` to a new string (assuming plain string node)."""
        if isinstance(self._data, str):
            return self.set_data(new_name)
        raise ValueError("Can only rename plain string nodes")

    def set_data(
        self,
        data,
        *,
        data_id: DataIdType | None = None,
        with_clones: bool | None = None,
    ) -> None:
        """Change node's `data` and/or `data_id` and update bookkeeping."""
        return self.tree._set_data(
            self,  # type: ignore
            data,
            data_id=data_id,
            with_clones=with_clones,
        )

    # def set_data(
    #     self,
    #     data,
    #     *,
    #     data_id: DataIdType | None = None,
    #     with_clones: bool | None = None,
    # ) -> None:
    #     """Change node's `data` and/or `data_id` and update bookkeeping."""
    #     if not data and not data_id:
    #         raise ValueError("Missing data or data_id")

    #     tree = self.tree

    #     if data is None or data is self._data:
    #         new_data = None
    #     else:
    #         new_data = data
    #         if data_id is None:
    #             data_id = tree.calc_data_id(data)

    #     if data_id is None or data_id == self._data_id:
    #         new_data_id = None
    #     else:
    #         new_data_id = data_id

    #     node_map = tree._nodes_by_data_id
    #     cur_nodes = node_map[self._data_id]
    #     has_clones = len(cur_nodes) > 1

    #     if has_clones and with_clones is None:
    #         raise AmbiguousMatchError(
    #             "set_data() for clones requires `with_clones` decision"
    #         )

    #     if new_data_id:
    #         # data_id (and possibly data) changes: we have to update the map
    #         if has_clones:
    #             if with_clones:
    #                 # Move the whole slot (but check if new id already exist)
    #                 prev_clones = node_map[self._data_id]
    #                 del node_map[self._data_id]
    #                 try:  # are we adding to existing clones now?
    #                     node_map[new_data_id].extend(prev_clones)
    #                 except KeyError:  # still a singleton, just a new data_id
    #                     node_map[new_data_id] = prev_clones
    #                 for n in prev_clones:
    #                     n._data_id = new_data_id
    #                     if new_data:
    #                         n._data = new_data
    #             else:
    #                 # Move this one node to another slot in the map
    #                 node_map[self._data_id].remove(self)
    #                 try:  # are we adding to existing clones again?
    #                     node_map[new_data_id].append(self)
    #                 except KeyError:  # now a singleton with a new data_id
    #                     node_map[new_data_id] = [self]
    #                 self._data_id = new_data_id
    #                 if new_data:
    #                     self._data = new_data
    #         else:
    #             # data_id (and possibly data) changed for a *single* node
    #             del node_map[self._data_id]
    #             try:  # are we creating a clone now?
    #                 node_map[new_data_id].append(self)
    #             except KeyError:  # still a singleton, just a new data_id
    #                 node_map[new_data_id] = [self]
    #             self._data_id = new_data_id
    #             if new_data:
    #                 self._data = new_data
    #     elif new_data:
    #         # `data` changed, but `data_id` remains the same:
    #         # simply replace the reference
    #         if with_clones:
    #             for n in cur_nodes:
    #                 n._data = data
    #         else:
    #             self._data = new_data

    #     return

    def get_children(self) -> list[Self]:
        """Return list of direct child nodes (list may be empty)."""
        return self.children

    def first_child(self) -> Self | None:
        """First direct child node or None if no children exist."""
        return self._children[0] if self._children else None

    def last_child(self) -> Self | None:
        """Last direct child node or None if no children exist."""
        return self._children[-1] if self._children else None

    def get_siblings(self, *, add_self=False) -> list[Self]:
        """Return a list of all sibling entries of self (excluding self) if any."""
        if add_self:
            return self._parent._children  # type: ignore
        return [n for n in self._parent._children if n is not self]  # type: ignore

    def first_sibling(self) -> Self:
        """Return first sibling (may be self)."""
        return self._parent._children[0]  # type: ignore

    def prev_sibling(self) -> Self | None:
        """Predecessor or None, if node is first sibling."""
        if self.is_first_sibling():
            return None
        idx = self._parent._children.index(self)  # type: ignore
        return self._parent._children[idx - 1]  # type: ignore

    def next_sibling(self) -> Self | None:
        """Return successor or None, if node is last sibling."""
        if self.is_last_sibling():
            return None
        idx = self._parent._children.index(self)  # type: ignore
        return self._parent._children[idx + 1]  # type: ignore

    def last_sibling(self) -> Self:
        """Return last node, that share own parent (may be `self`)."""
        return self._parent._children[-1]  # type: ignore

    def get_clones(self, *, add_self=False) -> list[Self]:
        """Return a list of all nodes that reference the same data if any."""
        clones = cast(list[Self], self._tree._nodes_by_data_id[self._data_id])
        if add_self:
            return clones.copy()
        return [n for n in clones if n is not self]

    def depth(self) -> int:
        """Return the distance to the root node (1 for toplevel nodes)."""
        return self.calc_depth()

    def count_descendants(self, *, leaves_only=False) -> int:
        """Return number of descendant nodes, not counting self."""
        all = not leaves_only
        i = 0
        for node in self.iterator():
            if all or not node._children:
                i += 1
        return i

    def calc_depth(self) -> int:
        """Return the distance to the root node (1 for toplevel nodes)."""
        depth = 0
        pe = self._parent
        while pe is not None:
            depth += 1
            pe = pe._parent
        return depth

    def calc_height(self) -> int:
        """Return the maximum depth of all descendants (0 for leaves)."""
        height = 0

        def _ch(n: Self, h: int) -> None:
            nonlocal height
            c = n._children
            if c:
                for n in c:
                    _ch(n, h + 1)
            elif h > height:
                height = h

        _ch(self, 0)
        return height

    def get_index(self) -> int:
        """Return index in sibling list."""
        return self._parent._children.index(self)  # type: ignore

    # --------------------------------------------------------------------------

    def is_system_root(self) -> bool:
        """Return true if this node is the invisible system root
        :class:`~nutree.tree._SystemRootNode`."""
        return self._parent is None

    def is_top(self) -> bool:
        """Return true if this node has no parent."""
        return self._parent._parent is None

    def is_leaf(self) -> bool:
        """Return true if this node is an end node, i.e. has no children."""
        return not self._children

    def is_clone(self) -> bool:
        """Return true if this node's data is referenced at least one more time."""
        return bool(len(self._tree._nodes_by_data_id.get(self._data_id)) > 1)  # type: ignore

    def is_first_sibling(self) -> bool:
        """Return true if this node is the first sibling, i.e. the first child
        of its parent."""
        return self is self._parent._children[0]  # type: ignore

    def is_last_sibling(self) -> bool:
        """Return true if this node is the last sibling, i.e. the last child
        of its parent."""
        return self is self._parent._children[-1]  # type: ignore

    def has_children(self) -> bool:
        """Return true if this node has one or more children."""
        return bool(self._children)

    def get_top(self) -> Self:
        """Return toplevel ancestor (may be self)."""
        root = self
        while root._parent._parent:
            root = root._parent
        return root

    def is_descendant_of(self, other: Self) -> bool:
        """Return true if this node is direct or indirect child of `other`."""
        parent = self._parent
        while parent is not None and parent._parent is not None:
            if parent is other:
                return True
            parent = parent._parent
        return False

    def is_ancestor_of(self, other: Self) -> bool:
        """Return true if this node is a parent, grandparent, ... of `other`."""
        return other.is_descendant_of(self)

    def get_common_ancestor(self, other: Self) -> Self | None:
        """Return the nearest node that contains `self` and `other` (may be None)."""
        if self._tree is other._tree:
            other_parent_set = {
                n._node_id for n in other.get_parent_list(add_self=True)
            }
            for parent in self.get_parent_list(add_self=True, bottom_up=True):
                if parent._node_id in other_parent_set:
                    return parent
        return None

    def get_parent_list(self, *, add_self=False, bottom_up=False) -> list[Self]:
        """Return ordered list of all parent nodes."""
        res = []
        parent = self if add_self else self._parent
        while parent is not None and parent._parent is not None:
            res.append(parent)
            parent = parent._parent
        if not bottom_up:
            res.reverse()
        return res

    def get_path(
        self, *, add_self: bool = True, separator: str = "/", repr: str = "{node.name}"
    ) -> str:
        """Return a breadcrumb string, e.g. '/A/a1/a12'."""
        res = (repr.format(node=p) for p in self.get_parent_list(add_self=add_self))
        return separator + separator.join(res)

    # --------------------------------------------------------------------------

    def add_child(
        self,
        child: Self | Tree | TData,
        *,
        before: Self | bool | int | None = None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id=None,
    ) -> Self:
        """Append or insert a new subnode or branch as child.

        If `child` is an existing :class:`~nutree.node.Node` instance, a copy
        of this node will be created, that references the same `child.data`
        object. |br|
        If `deep` is true, the children are copied recursively.

        If `child` is a :class:`~nutree.tree.Tree`, all of its topnodes are
        added recursively (unless `deep` is false).

        If `child` is neither a :class:`~nutree.node.Node` nor a
        :class:`~nutree.tree.Tree`, `child` itself will become the
        `data` object of a new node that is added.

        The source node may come from the same or from a foreign tree. |br|
        Note that adding the same data below one parent is not allowed.

        If this node has no children yet, the new node is created as first child.
        Otherwise, it will be appended to the existing children by default. |br|
        The `before` option may be used to  specifiy the position:

            - False, None: append the new node as last child
            - True, 0: prepend the new node as first child
            - <int>: prepend the new node before the existing child with this index
            - <Node>: prepend the new node before this child node

        Args:
            child (Node|Tree|TData):
                Either an existing Node or a data object.
            before (bool|int|Node|None):
                Optional position.
            deep (bool):
                Copy descendants if any.
                This argument defaults to false  when `child` is a
                :class:`~nutree.node.Node`.
                It defaults to true  when `child` is a :class:`~nutree.tree.Tree`.
            data_id (str|int|None):
                Allow to override the new node's `data_id`.
                This argument is only allowed for single nodes, but not for
                deep copies.
                Default `None` will to calculate from ``hash(node.data)``.
            node_id (str|int|None):
                Optional custom unique node key (defaults to ``id(node)``)
                This argument is only allowed for single nodes, but not for
                deep copies.
        Returns:
            the new :class:`~nutree.node.Node` instance
        """
        if isinstance(child, self._tree.__class__):
            if deep is None:
                deep = True
            topnodes = cast(list[Self], child.system_root.children)
            if isinstance(before, (int, Node)) or before is True:
                topnodes.reverse()
            n = None
            for n in topnodes:
                self.add_child(n, before=before, deep=deep)
            return cast(Self, n)

        factory = self.tree.node_factory
        source_node: Self = None  # type: ignore
        new_node: Self = None  # type: ignore

        if isinstance(child, Node):
            assert isinstance(child, self.tree.node_factory)
            # Adding an existing node means that we create a clone
            if deep is None:
                deep = False
            if deep and data_id is not None or node_id is not None:
                raise ValueError("Cannot set ID for deep copies.")

            source_node = cast(Self, child)
            if source_node._tree is self._tree:
                if source_node._parent is self:
                    raise UniqueConstraintError(
                        f"Cannot add a copy of {source_node} as child of {self}, "
                        "because it would create a 2nd instance in the same parent."
                    )
            else:
                pass

            if data_id and data_id != source_node._data_id:
                raise UniqueConstraintError(f"data_id conflict: {source_node}")

            new_node = factory(
                source_node.data,  # type: ignore
                parent=self,  # type: ignore
                data_id=data_id,
                node_id=node_id,
            )
        else:
            new_node = factory(child, parent=self, data_id=data_id, node_id=node_id)  # type: ignore

        new_node = cast(Self, new_node)

        if before is True:
            before = 0  # prepend

        children = self._children
        if children is None:
            assert before in (None, True, int, False)
            self._children = [new_node]
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
        child: Self | Tree | TData,
        *,
        deep=None,
        data_id: DataIdType | None = None,
        node_id=None,
    ):
        """Append a new subnode.

        This is a shortcut for :meth:`add_child` with ``before=None``.
        """
        return self.add_child(
            child, before=None, deep=deep, data_id=data_id, node_id=node_id
        )

    def prepend_child(
        self,
        child: Self | Tree | TData,
        *,
        deep=None,
        data_id: DataIdType | None = None,
        node_id=None,
    ):
        """Prepend a new subnode.

        This is a shortcut for :meth:`add_child` with ``before=True``.
        """
        return self.add_child(
            child,
            before=self.first_child(),
            deep=deep,
            data_id=data_id,
            node_id=node_id,
        )

    def prepend_sibling(
        self,
        child: Self | Tree | TData,
        *,
        deep=None,
        data_id: DataIdType | None = None,
        node_id=None,
    ) -> Self:
        """Add a new node before `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        return self._parent.add_child(
            child, before=self, deep=deep, data_id=data_id, node_id=node_id
        )

    def append_sibling(
        self,
        child: Self | Tree | TData,
        *,
        deep=None,
        data_id: DataIdType | None = None,
        node_id=None,
    ) -> Self:
        """Add a new node after `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        next_node = self.next_sibling()
        return self._parent.add_child(
            child, before=next_node, deep=deep, data_id=data_id, node_id=node_id
        )

    def move_to(
        self,
        new_parent: Self | Tree[TData, Self],
        *,
        before: Self | bool | int | None = None,
    ):
        """Move this node to another parent.

        By default, the node is appended to existing children.
        See :meth:`add_child` for a description of `before`.
        """
        assert new_parent is not None
        if not isinstance(new_parent, Node):
            # it's a Tree
            # assert isinstance(new_parent, self.tree.__class__)
            # assert isinstance(new_parent, Tree)
            new_parent = new_parent.system_root
        assert isinstance(new_parent, Node)

        if new_parent.tree is not self.tree:
            raise NotImplementedError("Can only move nodes inside same tree")

        self._parent._children.remove(self)  # type: ignore
        if not self._parent._children:  # store None instead of `[]`
            self._parent._children = None
        self._parent = cast(Self, new_parent)

        if before is True:
            before = 0  # prepend

        target_siblings = new_parent._children
        if target_siblings is None:
            assert before in (None, True, False, 0), before
            new_parent._children = [self]
        elif isinstance(before, Node):
            assert before._parent is new_parent, before
            idx = target_siblings.index(before)  # raise ValueError if not found
            target_siblings.insert(idx, self)
        elif isinstance(before, int):
            target_siblings.insert(before, self)
        else:
            target_siblings.append(self)

        return

    def remove(self, *, keep_children=False, with_clones=False) -> None:
        """Remove this node.

        If `keep_children` is true, all children will be moved one level up,
        so they become siblings, before this node is removed.

        If `with_clones` is true, all nodes that reference the same data
        instance are removed as well.
        """
        if with_clones:
            for c in self.get_clones():  # Excluding self
                c.remove(keep_children=keep_children, with_clones=False)
            assert not self.is_clone()

        if keep_children:
            for c in self.children.copy():
                c.move_to(self._parent, before=self)
        else:
            self.remove_children()

        pc = self._parent._children
        pc.remove(self)  # type: ignore
        if not pc:  # store None instead of `[]`
            pc = self._parent._children = None

        self._tree._unregister(self)  # type: ignore

    def remove_children(self) -> None:
        """Remove all children of this node, making it a leaf node."""
        _unregister = self._tree._unregister
        for n in self._iter_post():
            _unregister(n)  # type: ignore
        self._children = None
        return

    def copy(
        self, *, add_self=True, predicate: PredicateCallbackType | None = None
    ) -> Tree[TData, Self]:
        """Return a new :class:`~nutree.tree.Tree` instance from this branch.

        See also :ref:`iteration-callbacks`.
        """
        new_tree = cast("Tree[TData, Self]", self._tree.__class__())
        if add_self:
            root = new_tree.add(self)
        else:
            root = new_tree.system_root
        root._add_from(self, predicate=predicate)
        return new_tree

    def copy_to(
        self,
        target: Self | Tree[TData, Self],
        *,
        add_self=True,
        before: Self | bool | int | None = None,
        deep: bool = False,
    ) -> Self:
        """Copy this node to another parent and return the new node.

        If `add_self` is set, a copy of this node becomes a child of `target`.
        Otherwise copies of all children of this node are created below `target`.

        By default new nodes are appended to existing children. The `before`
        argument defines an alternative positioning.
        It is only available when `add_self` is true.
        See :meth:`add_child` for a description of `before`.

        If `deep` is set, all descendants are copied recursively.
        """
        res: Self = self
        if add_self:
            res = target.add_child(self, before=before, deep=deep)
            return cast(Self, res)  # if target is Tree, type is not inferred?

        assert before is None
        if not self._children:
            raise ValueError("Need child nodes when `add_self=False`")
        for child in self.children:
            n = target.add_child(child, before=None, deep=deep)
            res = res or n  # Return the first new node
        return res

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
            data_id = child._data_id if child._data_id != hash(child.data) else None
            new_child = self.add_child(child.data, data_id=data_id)
            if child.children:
                # if child.has_children():
                new_child._add_from(child, predicate=None)
        return

    def _add_filtered(self, other: Self, predicate: PredicateCallbackType) -> None:
        """Append a filtered copy of `other` and its descendants as children.

        See also :ref:`iteration-callbacks`.
        """
        # Stack of parent node objects 2-tuples (is_existing, node), used to
        # create optional parents on demand.
        # If existing, `node` references this tree. Otherwise, `node` references
        # the `other` tree.
        parent_stack: list[tuple[bool, Self]] = [(True, self)]

        def _create_parents() -> Node[TData]:
            """Materialize all virtual parents and return the last one."""
            # print("_create_parents", parent_stack)
            p = parent_stack[0][1]
            for idx, (existing, n) in enumerate(parent_stack):
                if existing:
                    p = n
                else:
                    p = p.add(n)
                    parent_stack[idx] = (True, p)
            return p

        def _visit(other: Self) -> None:
            """Return True if any descendant returned True."""

            # print("_visit", parent_stack, other)
            for n in other.children:
                parent_stack.append((False, n))

                res = call_predicate(predicate, n)

                if res is None or res is False:  # Add only if has a `true` descendant
                    _visit(n)
                elif res is True:  # Add this node (and also check children)
                    _create_parents()
                    _visit(n)
                elif isinstance(res, SkipBranch):
                    if res.and_self is False:
                        # Add the node itself if user explicitly returned
                        # `SkipBranch(and_self=False)`
                        _create_parents()
                elif isinstance(res, StopTraversal):
                    raise res
                elif isinstance(res, SelectBranch):
                    # Unconditionally copy whole branch: no need to visit children
                    p = _create_parents()
                    p._add_from(n)
                else:
                    raise ValueError(f"Invalid predicate return value: {res}")

                parent_stack.pop()
            return

        try:
            _visit(other)
        except StopTraversal:
            pass
        return

    def filtered(self, predicate: PredicateCallbackType) -> Tree[TData, Self]:
        """Return a filtered copy of this node and descendants as tree.

        See also :ref:`iteration-callbacks`.
        """
        if not predicate:
            raise ValueError("Predicate is required (use copy() instead)")
        return self.copy(add_self=True, predicate=predicate)

    def filter(self, predicate: PredicateCallbackType) -> None:
        """In-place removal of mismatching nodes.

        See also :ref:`iteration-callbacks`.
        """
        if not predicate:
            raise ValueError("Predicate is required (use copy() instead)")

        def _visit(parent: Self) -> bool:
            """Return True if any descendant returned True."""
            remove_nodes = []
            must_keep = False

            for n in parent.children:
                res = call_predicate(predicate, n)
                if res is None or res is False:  # Keep only if has a `true` descendant
                    if _visit(n):
                        must_keep = True
                    else:
                        remove_nodes.append(n)
                elif res is True:  # Keep this node (and also check children)
                    _visit(n)
                    must_keep = True
                elif isinstance(res, SelectBranch):
                    # Unconditionally keep whole branch: no need to visit children
                    must_keep = True
                elif isinstance(res, SkipBranch):
                    if res.and_self is False:
                        must_keep = True
                        remove_nodes = n.children.copy()
                    else:
                        remove_nodes.append(n)
                elif isinstance(res, StopTraversal):
                    for n in remove_nodes:
                        n.remove()
                    raise res

            for n in remove_nodes:
                n.remove()
            return must_keep

        try:
            _visit(self)
        except StopTraversal:
            pass
        return

    def from_dict(
        self, obj: list[dict], *, mapper: DeserializeMapperType | None = None
    ) -> None:
        """Append copies of all source children to self."""
        # TODO:
        # if mapper is None:
        #     mapper = self._tree.DEFAULT_DESERIALZATION_MAPPER
        assert not self._children
        for item in obj:
            if mapper:
                # mapper may add item['data_id']
                # data = mapper(parent=self, item=item)
                data_obj = call_mapper(mapper, self, item)
            else:
                data_obj = item["data"]

            child = self.append_child(
                data_obj, data_id=item.get("data_id"), node_id=item.get("node_id")
            )
            child_items = item.get("children")
            if child_items:
                child.from_dict(child_items, mapper=mapper)
        return

    def _visit_pre(self, callback, memo) -> None:
        """Depth-first, pre-order traversal."""
        # Call callback and skip children if SkipBranch was returned.
        # Also a StopTraversal(value) exception may be raised.
        if call_traversal_cb(callback, self, memo) is False:
            return

        children = self._children
        if children:
            for c in children:
                c._visit_pre(callback, memo)
        return

    def _visit_post(self, callback, memo) -> None:
        """Depth-first, post-order traversal."""
        # Callback may raise StopTraversal (also if callback returns false)
        # but SkipBranch is not supported with post-order traversal
        if self._children:
            for c in self._children:
                c._visit_post(callback, memo)
        call_traversal_cb(callback, self, memo)

    def _visit_level(self, callback, memo) -> None:
        """Breadth-first (aka level-order) traversal."""
        # Note that this is non-recursive.
        children = self._children
        while children:
            next_level = []
            for c in children:
                if call_traversal_cb(callback, c, memo) is False:
                    continue
                if c._children:
                    next_level.extend(c._children)
            children = next_level
        return

    def visit(
        self,
        callback: TraversalCallbackType,
        *,
        add_self=False,
        method: IterMethod = IterMethod.PRE_ORDER,
        memo: Any | None = None,
    ) -> None | Any:
        """Call `callback(node, memo)` for all subnodes.

        The callback may return :class:`SkipBranch` (or an instance
        thereof) to omit child nodes but continue traversal otherwise.
        Raising `SkipBranch` has the same effect.

        The callback may return ``False`` or :class:`StopIteration` to immediately
        interrupt traversal.
        Raising `StopTraversal(value)` has the same effect but also allows to
        specify a return value for the visit method. |br|
        See also :ref:`iteration-callbacks`.

        Args:
            callback (function(node, memo)):
                Callback ``function(node, memo)``
            add_self (bool):
                If true, this node will also be visited (typically as first call).
            method (IterMethod):
                Traversal method, defaults to pre-order, depth-first search.
            memo (Any):
                This value will be passed to all calls and may be useful to
                implement caching or collect and return traversal results.
                If no `memo` argument is passed, an empty dict is created at
                start, which has a life-span of the traversal only.
        """
        try:
            handler = getattr(self.__class__, f"_visit_{method.value}")
        except AttributeError:
            raise NotImplementedError(
                f"Unsupported traversal method {method!r}."
            ) from None

        if memo is None:
            memo = {}

        try:
            # Level-order is non-recursive
            if method == IterMethod.LEVEL_ORDER:
                if add_self:
                    if call_traversal_cb(callback, self, memo) is False:
                        return None
                self._visit_level(callback, memo)
                return None
            # Otherwise pre- or post-order
            if add_self and method != IterMethod.POST_ORDER:
                if call_traversal_cb(callback, self, memo) is False:
                    return None

            for c in self.children:
                handler(c, callback, memo)

            if add_self and method == IterMethod.POST_ORDER:
                if call_traversal_cb(callback, self, memo) is False:
                    return None
        except StopTraversal as e:
            return e.value
        return None

    def _iter_pre(self) -> Iterator[Self]:
        """Depth-first, pre-order traversal."""
        children = self._children
        if children:
            for c in children:
                yield c
                yield from c._iter_pre()
        return

    def _iter_post(self) -> Iterator[Self]:
        """Depth-first, post-order traversal."""
        for c in self.children:
            yield from c._iter_post()
            yield c
        return

    def _iter_level(self, *, revert=False, toggle=False) -> Iterator[Self]:
        """Breadth-first (aka level-order) traversal."""
        children = self._children
        while children:
            next_level = []
            for c in children:
                if c._children:
                    next_level.extend(c._children)

            if revert:
                yield from reversed(children)
            else:
                yield from children

            if toggle:
                revert = not revert

            children = next_level

        return

    def _iter_level_rtl(self) -> Iterator[Self]:
        """Breadth-first (aka level-order) traversal, right-to-left."""
        return self._iter_level(revert=True, toggle=False)

    def _iter_zigzag(self) -> Iterator[Self]:
        """ZigZag traversal."""
        return self._iter_level(revert=False, toggle=True)

    def _iter_zigzag_rtl(self) -> Iterator[Self]:
        """ZigZag traversal, right-to-left."""
        return self._iter_level(revert=True, toggle=True)

    def iterator(
        self, method: IterMethod = IterMethod.PRE_ORDER, *, add_self=False
    ) -> Iterator[Self]:
        """Generator that walks the hierarchy."""
        try:
            handler = getattr(self, f"_iter_{method.value}")
        except AttributeError:
            raise NotImplementedError(
                f"Unsupported traversal method {method!r}."
            ) from None

        if add_self and method != IterMethod.POST_ORDER:
            yield self

        yield from handler()

        if add_self and method == IterMethod.POST_ORDER:
            yield self

    #: Implement ``for subnode in node: ...`` syntax to iterate descendant nodes.
    __iter__ = iterator

    def _search(
        self,
        match: MatchArgumentType,
        *,
        max_results: int | None = None,
        add_self=False,
    ) -> Iterator[Self]:
        if callable(match):
            cb_match = match
        elif isinstance(match, str):
            pattern = re.compile(pattern=match)
            cb_match = lambda node: bool(pattern.fullmatch(node.name))  # noqa: E731
        elif isinstance(match, (list, tuple)):
            assert len(match) == 2, match
            pattern = re.compile(pattern=match[0], flags=match[1])
            cb_match = lambda node: bool(pattern.fullmatch(node.name))  # noqa: E731
        else:
            cb_match = lambda node: node._data is match  # noqa: E731

        count = 0
        for node in self.iterator(add_self=add_self):
            if not cb_match(node):
                continue
            count += 1
            yield node
            if max_results and count >= max_results:
                break
        return

    def find_all(
        self,
        data=None,
        *,
        match: MatchArgumentType | None = None,
        data_id: DataIdType | None = None,
        add_self=False,
        max_results: int | None = None,
    ) -> list[Self]:
        """Return a list of matching nodes (list may be empty).

        See also :ref:`iteration-callbacks`.
        """
        if data:
            assert data_id is None
            data_id = self._tree.calc_data_id(data)
        if data_id:
            assert match is None
            return [
                n for n in self.iterator(add_self=add_self) if n._data_id == data_id
            ]
        return [
            n for n in self._search(match, add_self=add_self, max_results=max_results)
        ]

    def find_first(
        self,
        data=None,
        *,
        match: MatchArgumentType | None = None,
        data_id: DataIdType | None = None,
    ) -> Self | None:
        """Return the first matching node or `None`.

        See also :ref:`iteration-callbacks`.
        """
        res = self.find_all(data, match=match, data_id=data_id, max_results=1)
        return res[0] if res else None

    #: Alias for :meth:`find_first`
    find = find_first

    def sort_children(
        self, *, key: SortKeyType | None = None, reverse=False, deep=False
    ) -> None:
        """Sort child nodes.

        `key` defaults to ``attrgetter("name")``, so children are sorted by
        their string representation.
        """
        cl = self._children
        if not cl or len(cl) == 1 and not deep:
            return
        if key is None:
            key = attrgetter("name")
        cl.sort(key=key, reverse=reverse)
        if deep:
            for c in cl:
                c.sort_children(key=key, reverse=reverse, deep=True)
        return

    def _get_prefix(self, style, lstrip) -> str:
        if len(style) == 4:
            s0, s1, s2, s3 = style
            s4 = s2
            s5 = s3
        elif len(style) == 6:
            s0, s1, s2, s3, s4, s5 = style
        else:
            raise ValueError(f"Invalid style {style!r}")

        def _is_last(p) -> bool:
            # Don't use `is_last_sibling()` which is overloaded by TypedNode
            return p is p._parent._children[-1]

        parts = []
        depth = 0
        for p in self.get_parent_list():
            depth += 1
            if depth <= lstrip:
                continue
            if _is_last(p):
                parts.append(s0)  # "    "
            else:
                parts.append(s1)  # " |  "

        if depth >= lstrip:
            if self._children:
                if _is_last(self):
                    parts.append(s4)  # " ╰┬─ "
                else:
                    parts.append(s5)  # " ├┬─ "
            else:
                if _is_last(self):
                    parts.append(s2)  # " ╰── "
                else:
                    parts.append(s3)  # " ├── "

        return "".join(parts)

    def _render_lines(
        self, *, repr: ReprArgType | None = None, style=None, add_self=True
    ) -> Iterator[str]:
        if not isinstance(style, (list, tuple)):
            try:
                style = CONNECTORS[style or self.tree.DEFAULT_CONNECTOR_STYLE]
            except KeyError:
                raise ValueError(
                    f"Invalid style {style!r}. Expected: {'|'.join(CONNECTORS.keys())}"
                ) from None

        if repr is None:
            repr = self.DEFAULT_RENDER_REPR

        # Find out if we need to strip some of the leftmost prefixes.
        # If this was called for a normal node, we strip all parent levels
        # (and also the own prefix when `add_self` is false).
        # If this was called for the system root node, we do the same, but we
        # never render self, because the title is rendered by the caller.
        lstrip = self.depth()
        if not add_self:
            lstrip += 1
        if not self._parent:
            add_self = False

        for n in self.iterator(add_self=add_self):
            prefix = n._get_prefix(style, lstrip)

            if callable(repr):
                s = repr(n)
            else:
                s = repr.format(node=n)

            yield prefix + s

        return

    def format_iter(
        self,
        *,
        repr: ReprArgType | None = None,
        style: str | None = None,
        add_self=True,
    ) -> Iterator[str]:
        """This variant of :meth:`format` returns a line generator."""
        if style == "list":
            if repr is None:
                repr = self.DEFAULT_RENDER_REPR
            for n in self.iterator(add_self=add_self):
                if callable(repr):
                    yield repr(n)
                else:
                    yield repr.format(node=n)
            return
        yield from self._render_lines(repr=repr, style=style, add_self=add_self)

    def format(
        self,
        *,
        repr: ReprArgType | None = None,
        style: str | None = None,
        add_self=True,
        join: str = "\n",
    ) -> str:
        r"""Return a pretty string representation of the node hierarchy.

        more

        Args:
            repr (str):
                A string or callback that defines how the node is rendered
                after the connector prefixes are generated.
            style (str):
                A string that defines the connector type, e.g. "round42" will
                produce "│ ", "╰─", "├─".
            add_self (bool):
                If false, only the descendants of this node are formatted.
            join (str):
                A string that is used to terminate the single lines. Defaults
                to "\n", but may be set to ", " together with `style="list"`
                to create a single line output.

        Example:

            print(node.format(repr="{node.name}", style="round42"))

        """
        iter_lines = self.format_iter(repr=repr, style=style, add_self=add_self)
        return join.join(iter_lines)

    def to_dict(self, *, mapper: SerializeMapperType | None = None) -> dict:
        """Return a nested dict of this node and its children."""
        res: dict = {
            "data": str(self.data),
        }
        # Add custom data_id if not calculated to the hash by default.
        if self._data_id != hash(self._data):
            res["data_id"] = self._data_id
        res = call_mapper(mapper, self, res)
        # if mapper:
        #     res = mapper(self, res)
        if self._children:
            res["children"] = cl = []
            for n in self._children:
                cl.append(n.to_dict(mapper=mapper))
        return res

    @classmethod
    def _compress_entry(
        cls, data: dict | str, key_map: KeyMapType, value_map: ValueDictMapType
    ) -> None:
        if isinstance(data, str):
            return
        for key, value in list(data.items()):
            if key in key_map:
                short_key = key_map[key]
                data[short_key] = data.pop(key)
            else:
                short_key = key

            if key in value_map:
                data[short_key] = value_map[key][value]
        return

    @classmethod
    def _make_list_entry(cls, node: Self) -> dict[str, Any] | str:
        node_data = node._data
        is_custom_id = node._data_id != hash(node_data)

        # If data is more complex than a simple string, or if we use a custom
        # data_id, we store data as a dict instead of a str:
        if isinstance(node_data, str):
            if not is_custom_id:
                # Special case: node.data is a plain string without custom ID
                return node_data
            data: dict[str, Any] = {
                "str": node_data,
            }
        else:
            # data is stored as-is, i.e. plain string instead of dict
            data = {
                # "id": data_id,
            }
        # Add custom data_id if not calculated as hash by default.
        if node._data_id != hash(node_data):
            data["data_id"] = node._data_id
        return data

    def to_list_iter(
        self,
        *,
        mapper: SerializeMapperType | None = None,
        key_map: KeyMapType | None = None,
        value_map: ValueMapType | None = None,
    ) -> Iterator[tuple[DataIdType, FlatJsonDictType | str | int]]:
        """Yield children as parent-referencing list.

        ```py
        [(parent_key, data)]
        ```
        """
        calc_id = self._tree.calc_data_id
        #: For nodes with multiple occurrences: index of the first one
        #: For typed nodes, we must also check if the `kind` matches, before
        #: simply store a reference.
        clone_idx_and_kind_map: dict[DataIdType, tuple[DataIdType, str | None]] = {}
        parent_id_map = {self._node_id: 0}

        if mapper is None:
            mapper = self._tree.serialize_mapper

        if key_map is None:
            key_map = {}

        if value_map is None:
            value_dict_map: ValueDictMapType = {}
        else:
            # Convert value_map entries from lists to dicts for faster lookup
            # of the index.
            # E.g. `{'t': ['person', 'dept']}` -> {'t': {'person': 0, 'dept': 1}}`
            value_dict_map = {
                k: {v: i for i, v in enumerate(a)} for k, a in value_map.items()
            }
            # print("value_map", value_map)

        for id_gen, node in enumerate(self, 1):
            # Compact mode: use integer sequence as keys
            # Store idx with original id for later parent-ref. We only have to
            # do this for nodes that have children though:
            node_id = node._node_id
            if node._children:
                parent_id_map[node_id] = id_gen

            parent_id = node._parent._node_id
            parent_idx = parent_id_map[parent_id]

            node_data = node._data
            data_id = calc_id(node_data)

            # If node is a 2nd occurrence of a clone, only store the index of the
            # first occurrence and do not call the mapper
            node_kind = getattr(node, "kind", None)

            clone_idx, clone_kind = clone_idx_and_kind_map.get(data_id, (None, None))
            if clone_idx:
                if node_kind == clone_kind:
                    yield (parent_idx, clone_idx)
                    continue
            elif node.is_clone():
                # First instance of a clone node: take a note
                clone_idx_and_kind_map[data_id] = (id_gen, node_kind)

            # If node.data is more complex than a simple string, or if we use a
            # custom data_id, we store data as a dict instead of a str:
            data = self._make_list_entry(node)

            # Let caller serialize custom data objects
            if mapper and isinstance(data, dict):
                data = call_mapper(mapper, node, data)

            # Compress data if requested
            if key_map or value_map:
                self._compress_entry(data, key_map, value_dict_map)

            yield (parent_idx, data)
        return

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
        res = node_to_dot(
            self,
            add_self=add_self,
            unique_nodes=unique_nodes,
            graph_attrs=graph_attrs,
            node_attrs=node_attrs,
            edge_attrs=edge_attrs,
            node_mapper=node_mapper,
            edge_mapper=edge_mapper,
        )
        return res

    def to_rdf_graph(
        self, *, add_self: bool = True, node_mapper: RDFMapperCallbackType | None = None
    ):
        """Return an instance of ``rdflib.Graph``.

        See :ref:`graphs` for details.
        """
        return node_to_rdf(self, add_self=add_self, node_mapper=node_mapper)

    def to_mermaid_flowchart(
        self,
        target: IO[str] | str | Path,
        *,
        as_markdown: bool = True,
        direction: MermaidDirectionType = "TD",
        title: str | bool | None = True,
        format: MermaidFormatType | None = None,
        mmdc_options: dict | None = None,
        add_self: bool = True,
        unique_nodes: bool = True,
        headers: Iterable[str] | None = None,
        root_shape: str | None = None,
        node_mapper: MermaidNodeMapperCallbackType | str | None = None,
        edge_mapper: MermaidEdgeMapperCallbackType | str | None = None,
    ) -> None:
        """Serialize a Mermaid flowchart representation.

        Optionally convert to a Graphviz display formats.
        See :ref:`graphs` for details.
        """
        return node_to_mermaid_flowchart(
            node=self,
            target=target,
            as_markdown=as_markdown,
            direction=direction,
            title=title,
            format=format,
            mmdc_options=mmdc_options,
            add_root=add_self,
            unique_nodes=unique_nodes,
            headers=headers,
            root_shape=root_shape,
            node_mapper=node_mapper,
            edge_mapper=edge_mapper,
        )
