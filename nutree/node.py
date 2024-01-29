# (c) 2021-2023 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Declare the :class:`~nutree.node.Node` class.
"""
from __future__ import annotations

import re
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from .tree import Tree

from .common import (
    CONNECTORS,
    AmbiguousMatchError,
    DataIdType,
    DeserializeMapperType,
    IterMethod,
    KeyMapType,
    MapperCallbackType,
    PredicateCallbackType,
    SelectBranch,
    SerializeMapperType,
    SkipBranch,
    StopTraversal,
    TraversalCallbackType,
    UniqueConstraintError,
    ValueMapType,
    call_mapper,
    call_predicate,
    call_traversal_cb,
)
from .dot import node_to_dot
from .rdf import RDFMapperCallbackType, node_to_rdf


# ------------------------------------------------------------------------------
# - Node
# ------------------------------------------------------------------------------
class Node:
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
        data,
        *,
        parent: Node,
        data_id: Optional[DataIdType] = None,
        node_id: Optional[int] = None,
        meta: Dict = None,
    ):
        self._data = data
        self._parent: Node = parent

        tree = parent._tree
        self._tree: Tree = tree
        self._children: List[Node] = None

        if data_id is None:
            self._data_id: DataIdType = tree.calc_data_id(data)
        else:
            self._data_id: DataIdType = data_id

        if node_id is None:
            self._node_id: int = id(self)
        else:
            self._node_id = int(node_id)

        self._meta = meta

        tree._register(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.name!r}, data_id={self.data_id}>"

    def __eq__(self, other) -> bool:
        """Implement ``node == other`` syntax to compare embedded data.

        If `other` is a :class:`Node` instance, ``self.data == other.data`` is
        evaluated.
        Otherwise ``self.data == other`` is compared.

        Use ``node is other`` syntax instead to check if two nodes are truly
        identical.
        """
        if isinstance(other, Node):
            return self._data == other._data
        return self._data == other

    def __getattr__(self, name: str) -> Any:
        """Implement ``node.NAME`` aliasing  to ``node.data.NAME``.

        See :ref:`shadow-attributes`.
        """
        if self._tree._shadow_attrs:
            return getattr(self.data, name)
        raise AttributeError

    # def __iadd__(self, other) -> None:
    #     """Add child node(s)."""
    #     if isinstance(other, (Node, str)):
    #         self.add_child(other)
    #     elif isinstance(other, (list, tuple)):
    #         for o in other:
    #             self += o
    #     else:
    #         raise NotImplementedError

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
    def tree(self) -> Tree:
        """Return container :class:`~nutree.tree.Tree` instance."""
        return self._tree

    @property
    def parent(self) -> Node:
        """Return parent node or None for toplevel nodes."""
        p = self._parent
        return p if p._parent else None

    @property
    def children(self) -> List[Node]:
        """Return list of direct child nodes (list may be empty)."""
        c = self._children
        return [] if c is None else c

    @property
    def data(self) -> Any:
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
    def meta(self) -> Union[Dict, None]:
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

    def clear_meta(self, key: str = None) -> None:
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
        if type(self._data) is str:
            return self.set_data(new_name)
        raise ValueError("Can only rename plain string nodes")

    def set_data(self, data, *, data_id=None, with_clones: bool = None) -> None:
        """Change node's `data` and/or `data_id` and update bookkeeping."""
        if not data and not data_id:
            raise ValueError("Missing data or data_id")

        tree = self._tree

        if data is None or data is self._data:
            new_data = None
        else:
            new_data = data
            if data_id is None:
                data_id = tree.calc_data_id(data)

        if data_id is None or data_id == self._data_id:
            new_data_id = None
        else:
            new_data_id = data_id

        node_map = tree._nodes_by_data_id
        cur_nodes = node_map[self._data_id]
        has_clones = len(cur_nodes) > 1

        if has_clones and with_clones is None:
            raise AmbiguousMatchError(
                "set_data() for clones requires `with_clones` decision"
            )

        if new_data_id:
            # data_id (and possibly data) changes: we have to update the map
            if has_clones:
                if with_clones:
                    # Move the whole slot (but check if new id already exist)
                    prev_clones = node_map[self._data_id]
                    del node_map[self._data_id]
                    try:  # are we adding to existing clones now?
                        node_map[new_data_id].extend(prev_clones)
                    except KeyError:  # still a singleton, just a new data_id
                        node_map[new_data_id] = prev_clones
                    for n in prev_clones:
                        n._data_id = new_data_id
                        if new_data:
                            n._data = new_data
                else:
                    # Move this one node to another slot in the map
                    node_map[self._data_id].remove(self)
                    try:  # are we adding to existing clones again?
                        node_map[new_data_id].append(self)
                    except KeyError:  # now a singleton with a new data_id
                        node_map[new_data_id] = [self]
                    self._data_id = new_data_id
                    if new_data:
                        self._data = new_data
            else:
                # data_id (and possibly data) changed for a *single* node
                del node_map[self._data_id]
                try:  # are we creating a clone now?
                    node_map[new_data_id].append(self)
                except KeyError:  # still a singleton, just a new data_id
                    node_map[new_data_id] = [self]
                self._data_id = new_data_id
                if new_data:
                    self._data = new_data
        elif new_data:
            # `data` changed, but `data_id` remains the same:
            # simply replace the reference
            if with_clones:
                for n in cur_nodes:
                    n._data = data
            else:
                self._data = new_data

        return

    def get_children(self) -> List[Node]:
        """Return list of direct child nodes (list may be empty)."""
        return self.children

    def first_child(self) -> Union[Node, None]:
        """First direct child node or None if no children exist."""
        return self._children[0] if self._children else None

    def last_child(self) -> Union[Node, None]:
        """Last direct child node or None if no children exist."""
        return self._children[-1] if self._children else None

    def get_siblings(self, *, add_self=False) -> List[Node]:
        """Return a list of all sibling entries of self (excluding self) if any."""
        if add_self:
            return self._parent._children
        return [n for n in self._parent._children if n is not self]

    def first_sibling(self) -> Node:
        """Return first sibling (may be self)."""
        return self._parent._children[0]

    def prev_sibling(self) -> Union[Node, None]:
        """Predecessor or None, if node is first sibling."""
        if self.is_first_sibling():
            return None
        idx = self._parent._children.index(self)
        return self._parent._children[idx - 1]

    def next_sibling(self) -> Union[Node, None]:
        """Return successor or None, if node is last sibling."""
        if self.is_last_sibling():
            return None
        idx = self._parent._children.index(self)
        return self._parent._children[idx + 1]

    def last_sibling(self) -> Node:
        """Return last node, that share own parent (may be `self`)."""
        return self._parent._children[-1]

    def get_clones(self, *, add_self=False) -> List[Node]:
        """Return a list of all nodes that reference the same data if any."""
        clones = self._tree._nodes_by_data_id[self._data_id]
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

        def _ch(n: Node, h: int) -> None:
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
        return self._parent._children.index(self)

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
        return bool(len(self._tree._nodes_by_data_id.get(self._data_id)) > 1)

    def is_first_sibling(self) -> bool:
        """Return true if this node is the first sibling, i.e. the first child
        of its parent."""
        return self is self._parent._children[0]

    def is_last_sibling(self) -> bool:
        """Return true if this node is the last sibling, i.e. the last child
        of its parent."""
        return self is self._parent._children[-1]

    def has_children(self) -> bool:
        """Return true if this node has one or more children."""
        return bool(self._children)

    def get_top(self) -> Node:
        """Return toplevel ancestor (may be self)."""
        root = self
        while root._parent._parent:
            root = root._parent
        return root

    def is_descendant_of(self, other: Node) -> bool:
        """Return true if this node is direct or indirect child of `other`."""
        parent = self._parent
        while parent is not None and parent._parent is not None:
            if parent is other:
                return True
            parent = parent._parent
        return False

    def is_ancestor_of(self, other: Node) -> bool:
        """Return true if this node is a parent, grandparent, ... of `other`."""
        return other.is_descendant_of(self)

    def get_common_ancestor(self, other: Node) -> Union[Node, None]:
        """Return the nearest node that contains `self` and `other` (may be None)."""
        if self._tree is other._tree:
            other_parent_set = {
                n._node_id for n in other.get_parent_list(add_self=True)
            }
            for parent in self.get_parent_list(add_self=True, bottom_up=True):
                if parent._node_id in other_parent_set:
                    return parent
        return None

    def get_parent_list(self, *, add_self=False, bottom_up=False) -> List[Node]:
        """Return ordered list of all parent nodes."""
        res = []
        parent = self if add_self else self._parent
        while parent is not None and parent._parent is not None:
            res.append(parent)
            parent = parent._parent
        if not bottom_up:
            res.reverse()
        return res

    def get_path(self, *, add_self=True, separator="/", repr="{node.name}") -> str:
        """Return a breadcrumb string, e.g. '/A/a1/a12'."""
        res = (repr.format(node=p) for p in self.get_parent_list(add_self=add_self))
        return separator + separator.join(res)

    # --------------------------------------------------------------------------

    def add_child(
        self,
        child: Union[Node, Tree, Any],
        *,
        before: Union[Node, bool, int, None] = None,
        deep: bool = None,
        data_id=None,
        node_id=None,
    ) -> Node:
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
            child (Node|Tree|Any):
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
            topnodes = child._root.children
            if isinstance(before, (int, Node)) or before is True:
                topnodes.reverse()
            for n in topnodes:
                self.add_child(n, before=before, deep=deep)
            return

        source_node = None
        factory = self._tree._node_factory
        if isinstance(child, Node):
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

            # If creating an inherited node, use the parent class as constructor
            child_class = child.__class__

            node = child_class(
                source_node.data, parent=self, data_id=data_id, node_id=node_id
            )
        else:
            node = factory(child, parent=self, data_id=data_id, node_id=node_id)

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
        child: Union[Node, Tree, Any],
        *,
        deep=None,
        data_id=None,
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
        child: Union[Node, Tree, Any],
        *,
        deep=None,
        data_id=None,
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
        child: Union[Node, Tree, Any],
        *,
        deep=None,
        data_id=None,
        node_id=None,
    ) -> Node:
        """Add a new node before `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        return self._parent.add_child(
            child, before=self, deep=deep, data_id=data_id, node_id=node_id
        )

    def append_sibling(
        self,
        child: Union[Node, Tree, Any],
        *,
        deep=None,
        data_id=None,
        node_id=None,
    ) -> Node:
        """Add a new node after `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        next_node = self.next_sibling()
        return self._parent.add_child(
            child, before=next_node, deep=deep, data_id=data_id, node_id=node_id
        )

    def move_to(
        self,
        new_parent: Union[Node, Tree],
        *,
        before: Union[Node, bool, int, None] = None,
    ):
        """Move this node to another parent.

        By default, the node is appended to existing children.
        See :meth:`add_child` for a description of `before`.
        """
        if new_parent is None:
            new_parent = self._tree._root
        # elif isinstance(new_parent, Tree):
        #     new_parent = new_parent._root
        elif hasattr(new_parent, "_root"):  # it's a Tree
            new_parent = new_parent._root

        if new_parent._tree is not self._tree:
            raise NotImplementedError("Can only move nodes inside same tree")

        self._parent._children.remove(self)
        self._parent = new_parent

        target_siblings = new_parent._children
        if target_siblings is None:
            assert before in (None, True, False)
            new_parent._children = [self]
        elif before is True:  # prepend
            target_siblings.insert(0, self)
        elif before:
            assert before._parent is new_parent
            idx = target_siblings.index(before)  # raise ValueError if not found
            target_siblings.insert(idx, self)
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
        pc.remove(self)
        if not pc:  # store None instead of `[]`
            pc = self._parent._children = None

        self._tree._unregister(self)

    def remove_children(self) -> None:
        """Remove all children of this node, making it a leaf node."""
        _unregister = self._tree._unregister
        for n in self._iter_post():
            _unregister(n)
        self._children = None
        return

    def copy(self, *, add_self=True, predicate: PredicateCallbackType = None) -> Tree:
        """Return a new :class:`~nutree.tree.Tree` instance from this branch.

        See also :ref:`iteration-callbacks`.
        """
        new_tree = self._tree.__class__()
        if add_self:
            root = new_tree.add(self)
        else:
            root = new_tree._root
        root._add_from(self, predicate=predicate)
        return new_tree

    def copy_to(
        self,
        target: Union[Node, Tree],
        *,
        add_self=True,
        before: Union[Node, bool, int, None] = None,
        deep: bool = False,
    ) -> Node:
        """Copy this node to another parent and return the new node.

        If `add_self` is set, a copy of this node becomes a child of `target`.
        Otherwise copies of all children of this node are created below `target`.

        By default new nodes are appended to existing children. The `before`
        argument defines an alternative positioning.
        It is only available when `add_self` is true.
        See :meth:`add_child` for a description of `before`.

        If `deep` is set, all descendants are copied recursively.
        """
        if add_self:
            return target.add_child(self, before=before, deep=deep)
        assert before is None
        res = None
        for child in self.children:
            n = target.add_child(child, before=None, deep=deep)
            res = res or n  # Return the first new node
        return res

    def _add_from(
        self, other: Node, *, predicate: PredicateCallbackType = None
    ) -> None:
        """Append copies of all source descendants to self.

        See also :ref:`iteration-callbacks`.
        """
        if predicate:
            return self._add_filtered(other, predicate)

        assert not self._children
        for child in other.children:
            new_child = self.add_child(child.data, data_id=child._data_id)
            if child.children:
                # if child.has_children():
                new_child._add_from(child, predicate=None)
        return

    def _add_filtered(self, other: Node, predicate: PredicateCallbackType) -> None:
        """Append a filtered copy of `other` and its descendants as children.

        See also :ref:`iteration-callbacks`.
        """
        # Stack of parent node objects 2-tuples (is_existing, node), used to
        # create optional parents on demand.
        # If existing, `node` references this tree. Otherwise, `node` references
        # the `other` tree.
        parent_stack = [(True, self)]

        def _create_parents() -> Node:
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

        def _visit(other: Node) -> None:
            """Return True if any descendant returned True."""

            # print("_visit", parent_stack, other)
            for n in other.children:
                parent_stack.append((False, n))

                res = call_predicate(predicate, n)
                if isinstance(res, SkipBranch):
                    if res.and_self is False:
                        # Add the node itself if user explicitly returned
                        # `SkipBranch(and_self=False)`
                        p = _create_parents()
                        p.add_child(n)
                elif isinstance(res, StopTraversal):
                    raise res
                elif isinstance(res, SelectBranch):
                    # Unconditionally copy whole branch: no need to visit children
                    p = _create_parents()
                    p._add_from(n)
                elif res in (None, False):  # Add only if has a `true` descendant
                    _visit(n)
                elif res is True:  # Add this node (and also check children)
                    p = _create_parents()
                    p.add_child(n)
                    _visit(n)

                parent_stack.pop()
            return

        try:
            _visit(other)
        except StopTraversal:
            pass
        return

    def filtered(self, predicate: PredicateCallbackType) -> Tree:
        """Return a filtered copy of this node and descendants as tree.

        See also :ref:`iteration-callbacks`.
        """
        return self.copy(add_self=True, predicate=predicate)

    def filter(self, predicate: PredicateCallbackType) -> None:
        """In-place removal of mismatching nodes.

        See also :ref:`iteration-callbacks`.
        """

        def _visit(parent: Node) -> bool:
            """Return True if any descendant returned True."""
            remove_nodes = []
            must_keep = None

            for n in parent.children:
                res = call_predicate(predicate, n)
                if res in (None, False):  # Keep only if has a `true` descendant
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
                        remove_nodes = n.children
                    else:
                        remove_nodes.append(n)
                elif isinstance(res, StopTraversal):
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
        self, obj: List[Dict], *, mapper: Optional[DeserializeMapperType] = None
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
                child.from_dict(child_items)
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
        children = self._children
        if children:
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
        method=IterMethod.PRE_ORDER,
        memo=None,
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
            raise NotImplementedError(f"Unsupported traversal method {method!r}.")

        if memo is None:
            memo = {}

        try:
            # Level-order is non-recursive
            if method == IterMethod.LEVEL_ORDER:
                if add_self:
                    if call_traversal_cb(callback, self, memo) is False:
                        return
                self._visit_level(callback, memo)
                return
            # Otherwise pre- or post-order
            if add_self and method != IterMethod.POST_ORDER:
                if call_traversal_cb(callback, self, memo) is False:
                    return

            for c in self._children:
                handler(c, callback, memo)

            if add_self and method == IterMethod.POST_ORDER:
                if call_traversal_cb(callback, self, memo) is False:
                    return
        except StopTraversal as e:
            return e.value

    def _iter_pre(self) -> Iterator[Node]:
        """Depth-first, pre-order traversal."""
        children = self._children
        if children:
            for c in children:
                yield c
                yield from c._iter_pre()
        return

    def _iter_post(self) -> Iterator[Node]:
        """Depth-first, post-order traversal."""
        children = self._children
        if children:
            for c in self._children:
                yield from c._iter_post()
                yield c
        return

    def _iter_level(self, *, revert=False, toggle=False) -> Iterator[Node]:
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

    def _iter_level_rtl(self) -> Iterator[Node]:
        """Breadth-first (aka level-order) traversal, right-to-left."""
        return self._iter_level(revert=True, toggle=False)

    def _iter_zigzag(self) -> Iterator[Node]:
        """ZigZag traversal."""
        return self._iter_level(revert=False, toggle=True)

    def _iter_zigzag_rtl(self) -> Iterator[Node]:
        """ZigZag traversal, right-to-left."""
        return self._iter_level(revert=True, toggle=True)

    def iterator(
        self, method=IterMethod.PRE_ORDER, *, add_self=False
    ) -> Iterator[Node]:
        """Generator that walks the hierarchy."""
        try:
            handler = getattr(self, f"_iter_{method.value}")
        except AttributeError:
            raise NotImplementedError(f"Unsupported traversal method {method!r}.")

        if add_self and method != IterMethod.POST_ORDER:
            yield self

        yield from handler()

        if add_self and method == IterMethod.POST_ORDER:
            yield self

    #: Implement ``for subnode in node: ...`` syntax to iterate descendant nodes.
    __iter__ = iterator

    def _search(self, match, *, max_results=None, add_self=False) -> Iterator[Node]:
        if callable(match):
            cb_match = match
        elif type(match) is str:
            pattern = re.compile(pattern=match)
            cb_match = lambda node: pattern.fullmatch(node.name)  # noqa: E731
        elif isinstance(match, (list, tuple)):
            pattern = re.compile(pattern=match[0], flags=match[1])
            cb_match = lambda node: pattern.fullmatch(node.name)  # noqa: E731
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
        self, data=None, *, match=None, data_id=None, add_self=False, max_results=None
    ) -> List[Node]:
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

    def find_first(self, data=None, *, match=None, data_id=None) -> Node | None:
        """Return the first matching node or `None`.

        See also :ref:`iteration-callbacks`.
        """
        res = self.find_all(data, match=match, data_id=data_id, max_results=1)
        return res[0] if res else None

    #: Alias for :meth:`find_first`
    find = find_first

    def sort_children(self, *, key=None, reverse=False, deep=False) -> None:
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

    def _render_lines(self, *, repr=None, style=None, add_self=True) -> Iterator[str]:
        if type(style) not in (list, tuple):
            try:
                style = CONNECTORS[style or self.tree.DEFAULT_CONNECTOR_STYLE]
            except KeyError:
                raise ValueError(
                    f"Invalid style {style!r}. Expected: {'|'.join(CONNECTORS.keys())}"
                )

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

    def format_iter(self, *, repr=None, style=None, add_self=True) -> Iterator[str]:
        """This variant of :meth:`format` returns a line generator."""
        if style == "list":
            for n in self.iterator(add_self=add_self):
                if callable(repr):
                    yield repr(n)
                else:
                    yield repr.format(node=n)
            return
        yield from self._render_lines(repr=repr, style=style, add_self=add_self)

    def format(self, *, repr=None, style=None, add_self=True, join="\n") -> str:
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

    def to_dict(self, *, mapper: Optional[SerializeMapperType] = None) -> Dict:
        """Return a nested dict of this node and its children."""
        res = {
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
        cls, data: dict | str, key_map: KeyMapType, value_map: ValueMapType
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
    def _make_list_entry(cls, node: Node) -> dict:
        node_data = node._data
        is_custom_id = node._data_id != hash(node_data)

        # If data is more complex than a simple string, or if we use a custom
        # data_id, we store data as a dict instead of a str:
        if type(node_data) is str:
            if not is_custom_id:
                # Special case: node.data is a plain string without custom ID
                return node_data
            data = {
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
        mapper: Optional[SerializeMapperType] = None,
        key_map: Optional[KeyMapType] = None,
        value_map: Optional[ValueMapType] = None,
    ) -> Iterator[Dict]:
        """Yield children as parent-referencing list.

        ```py
        [(parent_key, data)]
        ```
        """
        calc_id = self._tree.calc_data_id
        #: For nodes with multiple occurrences: index of the first one
        #: For typed nodes, we must also check if the `kind` matches, before
        #: simply store a reference.
        clone_idx_and_kind_map = {}
        parent_id_map = {self._node_id: 0}

        if mapper is None:
            mapper = self._tree.serialize_mapper

        key_map = {} if key_map is None else key_map

        if value_map is None:
            value_map = {}
        else:
            # Convert value_map entries from lists to dicts for faster lookup
            # of the index.
            # E.g. `{'t': ['person', 'dept']}` -> {'t': {'person': 0, 'dept': 1}}`
            value_map = {
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
            data = call_mapper(mapper, node, data)

            # Compress data if requested
            if key_map or value_map:
                self._compress_entry(data, key_map, value_map)

            yield (parent_idx, data)
        return

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
        self, *, add_self: bool = True, node_mapper: RDFMapperCallbackType = None
    ):
        """Return an instance of ``rdflib.Graph``.

        See :ref:`graphs` for details.
        """
        return node_to_rdf(self, add_self=add_self, node_mapper=node_mapper)
