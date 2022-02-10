# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Declare the :class:`~nutree.node.Node` class.
"""
import re
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Union

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from .tree import Tree

from .common import (
    CONNECTORS,
    DEFAULT_CONNECTOR_STYLE,
    DEFAULT_REPR,
    AmbigousMatchError,
    IterMethod,
    StopTraversal,
    TraversalCallbackType,
    UniqueConstraintError,
    _call_traversal_cb,
)
from .dot import node_to_dot


# ------------------------------------------------------------------------------
# - Node
# ------------------------------------------------------------------------------
class Node:
    """
    A Node represents a single element in the tree.
    It is a shallow wrapper around a user data instance, that adds navigation,
    modification, and other functionality.
    """

    # Slots may reduce node size (about 20% smaller):
    __slots__ = (
        "__weakref__",  # Allow weak references to Nodes
        "_children",
        "_data_id",
        "_data",
        "_node_id",
        "_parent",
        "_tree",
    )

    def __init__(self, data, *, parent: "Node", data_id=None, node_id=None):
        self._data = data
        self._parent: Node = parent

        tree = parent._tree
        self._tree: "Tree" = tree
        self._children: List[Node] = None

        if data_id is None:
            self._data_id = tree._calc_data_id(data)
        else:
            self._data_id = data_id

        if node_id is None:
            self._node_id: int = id(self)
        else:
            self._node_id = node_id

        tree._register(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.name!r}, data_id={self.data_id}>"

    def __eq__(self, other) -> bool:
        """Implement ``node == other`` syntax to compare embedded data.

        If `other` is a :class:`Node` instance, ``self.data == other.data`` is
        evaluated.
        Otherwise ``self.data == other`` is compared.

        Use ``node is other`` syntax instead to check if two nodes are truely
        identical.
        """
        if isinstance(other, Node):
            return self._data == other._data
        return self._data == other

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
    def tree(self) -> "Tree":
        """Return container :class:`~nutree.tree.Tree` instance."""
        return self._tree

    @property
    def parent(self) -> "Node":
        """Return parent node or None for toplevel nodes."""
        p = self._parent
        return p if p._parent else None

    @property
    def children(self) -> List["Node"]:
        """Return list of direct child nodes (list may be empty)."""
        c = self._children
        return [] if c is None else c

    @property
    def data(self) -> Any:
        """Return the wrapped data instance (use :meth:`~nutree.tree.Tree.set_data()` to modify)."""
        return self._data

    @property
    def data_id(self):
        """Return the wrapped data instance's id (use :meth:`~nutree.tree.Tree.set_data()` to modify)."""
        return self._data_id

    @property
    def node_id(self):
        """Return the node's unique key."""
        return self._node_id

    def rename(self, new_name: str) -> None:
        """Set `self.data` to a new string (assuming plain string node)."""
        if type(self._data) is str:
            return self.set_data(new_name)
        raise ValueError("Can only rename plain string nodes")

    def set_data(self, data, *, data_id=None, with_clones: bool = None) -> None:
        """Change node's `data` and/or `data_id` and update bookeeping."""
        if not data and not data_id:
            raise ValueError("Missing data or data_id")

        tree = self._tree

        if data is None or data is self._data:
            new_data = None
        else:
            new_data = data
            if data_id is None:
                data_id = tree._calc_data_id(data)

        if data_id is None or data_id == self._data_id:
            new_data_id = None
        else:
            new_data_id = data_id

        node_map = tree._nodes_by_data_id
        cur_nodes = node_map[self._data_id]
        has_clones = len(cur_nodes) > 1

        if has_clones and with_clones is None:
            raise AmbigousMatchError(
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

    @property
    def first_child(self) -> Union["Node", None]:
        """First direct childnode or None if no children exist."""
        return self._children[0] if self._children else None

    @property
    def last_child(self) -> Union["Node", None]:
        """Last direct childnode or None if no children exist."""
        return self._children[-1] if self._children else None

    @property
    def first_sibling(self) -> "Node":
        """Return first sibling (may be self)."""
        return self._parent._children[0]

    @property
    def prev_sibling(self) -> Union["Node", None]:
        """Predecessor or None, if node is first sibling."""
        if self.is_first_sibling():
            return None
        idx = self._parent._children.index(self)
        return self._parent._children[idx - 1]

    @property
    def next_sibling(self) -> Union["Node", None]:
        """Return successor or None, if node is last sibling."""
        if self.is_last_sibling():
            return None
        idx = self._parent._children.index(self)
        return self._parent._children[idx + 1]

    @property
    def last_sibling(self) -> "Node":
        """Return last node, that share own parent (may be `self`)."""
        return self._parent._children[-1]

    def get_siblings(self, add_self=False) -> List["Node"]:
        """Return a list of all sibling entries of self (excluding self) if any."""
        if add_self:
            return self._parent._children
        return [n for n in self._parent._children if n is not self]

    def get_clones(self, add_self=False) -> List["Node"]:
        """Return a list of all nodes that reference the same data if any."""
        clones = self._tree._nodes_by_data_id[self._data_id]
        if add_self:
            return clones
        return [n for n in clones if n is not self]

    @property
    def depth(self) -> int:
        """Return the number of parents (return 1 for toplevel nodes)."""
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
        """Return depth of node, i.e. number of parents (1 for toplevel nodes)."""
        depth = 0
        pe = self._parent
        while pe is not None:
            depth += 1
            pe = pe._parent
        return depth

    def calc_height(self) -> int:
        """Return the maximum depth of all descendants (0 for leaves)."""
        height = 0

        def _ch(n, h):
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
        """Return true if this node is the first sibling, i.e. the first child of its parent."""
        return self is self._parent._children[0]

    def is_last_sibling(self) -> bool:
        """Return true if this node is the last sibling, i.e. the last child of its parent."""
        return self is self._parent._children[-1]

    def has_children(self) -> bool:
        """Return true if this node has one or more children."""
        return bool(self._children)

    def get_top(self) -> "Node":
        """Return toplevel ancestor (may be self)."""
        root = self
        while root._parent._parent:
            root = root._parent
        return root

    def is_descendant_of(self, other: "Node") -> bool:
        """Return true if this node is direct or indirect child of `other`."""
        parent = self._parent
        while parent is not None and parent._parent is not None:
            if parent is other:
                return True
            parent = parent._parent
        return False

    def is_ancestor_of(self, other: "Node") -> bool:
        """Return true if this node is a parent, grandparent, ... of `other`."""
        return other.is_descendant_of(self)

    def get_common_ancestor(self, other: "Node") -> Union["Node", None]:
        """Return the nearest node that contains `self` and `other` (may be None)."""
        if self._tree is other._tree:
            other_parent_set = {
                n._node_id for n in other.get_parent_list(add_self=True)
            }
            for parent in self.get_parent_list(add_self=True, top_down=False):
                if parent._node_id in other_parent_set:
                    return parent
        return None

    def get_parent_list(self, *, add_self=False, top_down=True) -> List["Node"]:
        """Return ordered list of all parent nodes."""
        res = []
        parent = self if add_self else self._parent
        while parent is not None and parent._parent is not None:
            res.append(parent)
            parent = parent._parent
        if top_down:
            res.reverse()
        return res

    def get_path(self, *, add_self=True, separator="/", repr="{node.name}") -> str:
        """Return a breadcrumb string, e.g. '/A/a1/a12'."""
        res = (
            repr.format(node=p)
            for p in self.get_parent_list(add_self=add_self, top_down=True)
        )
        return separator + separator.join(res)

    # --------------------------------------------------------------------------

    def add_child(
        self,
        child: Union["Node", Any],
        *,
        before: Union["Node", bool, int, None] = None,
        data_id=None,
        node_id=None,
    ) -> "Node":
        """Append or insert a new subnode.

        If `child` is an existing Node instance, a copy of this node will be
        created that references the same `child.data` object. |br|
        Otherwise, `child` itself will become the `data` object of the new node.

        The source node may come from the same or from a foreign tree. |br|
        Note that adding the same data below one parent is not allowed.

        If this node has no children yet, the new node is created as first child.
        Otherwise, it will be appended to the existing children by default. |br|
        The `before` option may be used to  specifiy the position:

            - False, None: append the new node as last child
            - True, 0: prepend the new node as first child
            - <int>: prepend the new node before the existing child with this index
            - <Node>: prepend the new node before this childnode

        Args:
            child (Node|Any):
                Either an existing Node or a data object.
            before (bool|int|Node|None):
                Optional position.
            data_id (str|int|None):
                Default `None` will to calculate from `hash(node.data)`.
            node_id (str|int|None):
                Optional custom unique node key (defaults to `hash(node)`)
        Returns:
            the new :class:`node.Node` instance
        """
        if isinstance(child, Node):
            if child._tree is self._tree:
                if child._parent is self._parent:
                    raise UniqueConstraintError(f"Same parent not allowed: {child}")
            else:
                pass
                # raise NotImplementedError("Cross-tree adding")
            if data_id and data_id != child._data_id:
                raise UniqueConstraintError(f"data_id conflict: {child}")
            node = Node(child.data, parent=self, data_id=data_id, node_id=node_id)
        else:
            node = Node(child, parent=self, data_id=data_id, node_id=node_id)

        children = self._children
        if children is None:
            assert before in (None, True, int, False)
            self._children = [node]
        elif before is True:  # prepend
            children.insert(0, node)
        elif type(before) is int:
            children.insert(before, node)
        elif before:
            assert before._parent is self
            idx = children.index(before)  # raises ValueError
            children.insert(idx, node)
        else:
            children.append(node)

        return node

    #: Alias for :meth:`add_child`
    add = add_child

    def append_child(self, child: Union["Node", object], *, data_id=None, node_id=None):
        """Append a new subnode.

        This is a shortcut for :meth:`add_child` with ``before=None``.
        """
        return self.add_child(child, data_id=data_id, node_id=node_id, before=None)

    def prepend_child(self, child, *, data_id=None, node_id=None):
        """Prepend a new subnode.

        This is a shortcut for :meth:`add_child` with ``before=True``.
        """
        return self.add_child(
            child, data_id=data_id, node_id=node_id, before=self.first_child
        )

    def prepend_sibling(self, child, *, data_id=None, node_id=None) -> "Node":
        """Add a new node before `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        return self._parent.add_child(
            child, data_id=data_id, node_id=node_id, before=self
        )

    def append_sibling(self, child, *, data_id=None, node_id=None) -> "Node":
        """Add a new node after `self`.

        This method calls :meth:`add_child` on ``self.parent``.
        """
        next_node = self.next_sibling
        return self._parent.add_child(
            child, data_id=data_id, node_id=node_id, before=next_node
        )

    def move(
        self,
        new_parent: Union["Node", "Tree"],
        *,
        before: Union["Node", bool, None] = None,
    ):
        """Move this node before or after `otherNode` ."""
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

    def remove(self) -> None:
        """Remove this node."""
        self.remove_children()
        pc = self._parent._children
        pc.remove(self)
        if not pc:  # store None instead of `[]`
            pc = self._parent._children = None
        self._tree._unregister(self)

    def remove_children(self):
        """Remove all children of this node, making it a leaf node."""
        _unregister = self._tree._unregister
        for n in self._iter_post():
            _unregister(n)
        self._children = None
        return

    def to_tree(self, *, add_self=True, predicate=None) -> "Tree":
        """Return a new :class:`~nutree.tree.Tree` instance from this branch.

        See also :meth:`copy_from`.
        """
        new_tree = self._tree.__class__()
        if add_self:
            root = new_tree.add(self)
        else:
            root = new_tree._root
        root.copy_from(self, predicate=predicate)
        return new_tree

    def copy_from(self, src_node: "Node", *, predicate=None):
        """Append copies of all source children to self."""
        assert not self._children
        for child in src_node._children:
            if predicate and predicate(child) is False:
                continue
            new_child = self.add_child(child.data, data_id=child._data_id)
            if child.has_children():
                new_child.copy_from(child, predicate=predicate)
        return

    def from_dict(self, obj: List[Dict], *, mapper=None):
        """Append copies of all source children to self."""
        assert not self._children
        for item in obj:
            if mapper:
                # mapper may add item['data_id']
                data = mapper(parent=self, item=item)
            else:
                data = item["data"]

            child = self.append_child(
                data, data_id=item.get("data_id"), node_id=item.get("node_id")
            )
            child_items = item.get("children")
            if child_items:
                child.from_dict(child_items)
        return

    def _visit_pre(self, callback, memo):
        """Depth-first, pre-order traversal."""
        # Call callback and skip children if SkipChildren was returned.
        # Also a StopTraversal(value) exception may be raised.
        if _call_traversal_cb(callback, self, memo) is False:
            return

        children = self._children
        if children:
            for c in children:
                c._visit_pre(callback, memo)
        return

    def _visit_post(self, callback, memo):
        """Depth-first, post-order traversal."""
        # Callback may raise StopTraversal (also if callback returns false)
        # but SkipChildren is not supported with post-order traversal
        children = self._children
        if children:
            for c in self._children:
                c._visit_post(callback, memo)
        _call_traversal_cb(callback, self, memo)

    def _visit_level(self, callback, memo):
        """Breadth-first (aka level-order) traversal."""
        # Note that this is non-recursive.
        children = self._children
        while children:
            next_level = []
            for c in children:
                if _call_traversal_cb(callback, c, memo) is False:
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
    ):
        """Call `callback(node, memo)` for all subnodes.

        The callback may return :class:`SkipChildren` (or an instance
        thereof) to omit childnodes but continue traversal otherwise.
        Raising `SkipChildren` has the same effect. |br|
        Note that skipping of children is only available ...

        The callback may return ``False`` or :class:`StopIteration` to immediately
        interrupt traversal.
        Raising `StopTraversal(value)` has the same effect but also allows to
        specify a return value for the visit method.

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
            raise NotImplementedError(f"Unsupported traversal method '{method}'.")

        if memo is None:
            memo = {}

        try:
            # Level-order is non-recursive
            if method == IterMethod.LEVEL_ORDER:
                if add_self:
                    if _call_traversal_cb(callback, self, memo) is False:
                        return
                self._visit_level(callback, memo)
                return
            # Otherwise pre- or post-order
            if add_self and method != IterMethod.POST_ORDER:
                if _call_traversal_cb(callback, self, memo) is False:
                    return

            for c in self._children:
                handler(c, callback, memo)

            if add_self and method == IterMethod.POST_ORDER:
                if _call_traversal_cb(callback, self, memo) is False:
                    return
        except StopTraversal as e:
            return e.value

    def _iter_pre(self):
        """Depth-first, pre-order traversal."""
        children = self._children
        if children:
            for c in children:
                yield c
                yield from c._iter_pre()
        return

    def _iter_post(self):
        """Depth-first, post-order traversal."""
        children = self._children
        if children:
            for c in self._children:
                yield from c._iter_post()
                yield c
        return

    def _iter_level(self):
        """Breadth-first (aka level-order) traversal."""
        children = self._children
        while children:
            next_level = []
            for c in children:
                yield c
                if c._children:
                    next_level.extend(c._children)
            children = next_level
        return

    def iterator(
        self, method=IterMethod.PRE_ORDER, *, add_self=False
    ) -> Generator["Node", None, None]:
        """Generator that walks the hierarchy."""
        try:
            handler = getattr(self, f"_iter_{method.value}")
        except AttributeError:
            raise NotImplementedError(f"Unsupported traversal method '{method}'.")

        if add_self and method != IterMethod.POST_ORDER:
            yield self

        yield from handler()

        if add_self and method == IterMethod.POST_ORDER:
            yield self

    #: Implement ``for subnode in node:`` syntax to iterate nodes.
    __iter__ = iterator

    def _filter(self, match, *, max_results=None, add_self=False):
        if callable(match):
            cb_match = match
        elif type(match) is str:
            pattern = re.compile(pattern=match)
            cb_match = lambda node: pattern.fullmatch(node.name)
        elif isinstance(match, (list, tuple)):
            pattern = re.compile(pattern=match[0], flags=match[1])
            cb_match = lambda node: pattern.fullmatch(node.name)
        else:
            cb_match = lambda node: node._data is match

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
    ):
        """Return a list of matching nodes (list may be empty)."""
        if data:
            assert data_id is None
            data_id = self._tree._calc_data_id(data)
        if data_id:
            assert match is None
            return [
                n for n in self.iterator(add_self=add_self) if n._data_id == data_id
            ]
        return [
            n for n in self._filter(match, add_self=add_self, max_results=max_results)
        ]

    def find_first(self, data=None, *, match=None, data_id=None):
        """Return the first matching node or `None`."""
        res = self.find_all(data, match=match, data_id=data_id, max_results=1)
        return res[0] if res else None

    #: Alias for :meth:`find_first`
    find = find_first

    def sort_children(self, *, key=None, reverse=False, deep=False):
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

    def _get_prefix(self, style, lstrip):
        s0, s1, s2, s3 = style

        parts = []
        depth = 0
        for p in self.get_parent_list():
            depth += 1
            if depth <= lstrip:
                continue
            if p.is_last_sibling():
                parts.append(s0)  # "    "
            else:
                parts.append(s1)  # " |  "

        if depth >= lstrip:
            if self.is_last_sibling():
                parts.append(s2)  # " ╰─ "
            else:
                parts.append(s3)  # " ├─ "

        return "".join(parts)

    def _render_lines(self, *, repr=None, style=None, add_self=True):
        if type(style) not in (list, tuple):
            try:
                style = CONNECTORS[style or DEFAULT_CONNECTOR_STYLE]
            except KeyError:
                raise ValueError(
                    f"Invalid style '{style}'. Expected: {'|'.join(CONNECTORS.keys())}"
                )

        if repr is None:
            repr = DEFAULT_REPR

        # Find out if we need to strip some of the leftmost prefixes.
        # If this was called for a normal node, we strip all parent levels
        # (and also the own prefix when `add_self` is false).
        # If this was called for the system root node, we do the same, but we
        # never render self, because the the title is rendered by the caller.
        lstrip = self.depth
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

    def format_iter(self, *, repr=None, style=None, add_self=True):
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
        r"""Return a pretty string representation of the node hiererachy.

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

    def to_dict(self, *, mapper=None) -> Dict:
        """Return a nested dict of this node and its children."""
        res = {
            "data": str(self.data),
        }
        # Add custom data_id if any
        # data_id = hash(self._data)
        data_id = self._tree._calc_data_id(self._data)
        if data_id != self._data_id:
            res["data_id"] = data_id
        if mapper:
            res = mapper(self, res)
        if self._children:
            res["children"] = cl = []
            for n in self._children:
                cl.append(n.to_dict(mapper=mapper))
        return res

    def to_list_iter(self, *, mapper=None) -> Generator[Dict, None, None]:
        """Yield children as parent-referencing list.

        ```py
        [(parent_key, data)]
        ```
        """
        calc_id = self._tree._calc_data_id
        #: For nodes with multiple occurrences: index of the first one
        clone_idx_map = {}
        parent_id_map = {self._node_id: 0}

        for id_gen, node in enumerate(self, 1):
            # Compact mode: use integer sequence as keys
            # Store idx with original id for later parent-ref. We only have to
            # do this of nodes that have children though:
            node_id = node._node_id
            if node._children:
                parent_id_map[node_id] = id_gen

            parent_id = node._parent._node_id
            parent_idx = parent_id_map[parent_id]

            data = node._data
            data_id = calc_id(data)
            # data_id = hash(data)

            # If node is a 2nd occurence of a clone, only store the index of the
            # first occurence and do not call the mapper
            clone_idx = clone_idx_map.get(data_id)
            if clone_idx:
                yield (parent_idx, clone_idx)
                continue
            elif node.is_clone():
                clone_idx_map[data_id] = id_gen

            # If data is more complex than a simple string, or if we use a custom
            # data_id, we store data as a dict instead of a str:
            if type(data) is str:
                if data_id != node._data_id:
                    data = {
                        "str": data,
                        "id": data_id,
                    }
                # else: data is stored as-is, i.e. plain string instead of dict
            else:
                data = {
                    # "id": data_id,
                }
            # Let caller serialize custom data objects
            if mapper:
                data = mapper(node, data)

            yield (parent_idx, data)
        return

    def to_dot(
        self,
        *,
        add_self=False,
        single_inst=True,
        node_mapper=None,
        edge_mapper=None,
    ) -> Generator[str, None, None]:
        """Generate DOT formatted output.

        Args:
            mapper (method):
            add_self (bool):
            single_inst (bool):
        """
        res = node_to_dot(
            self,
            add_self=add_self,
            single_inst=single_inst,
            node_mapper=node_mapper,
            edge_mapper=edge_mapper,
        )
        return res
