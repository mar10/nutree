# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt and contributors; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Stress-test your web app.
"""
import re
from enum import Enum
from typing import TYPE_CHECKING, Dict, Generator, List, Union

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from .tree import Tree


class TreeError(RuntimeError):
    """Base class for all `nutree` errors."""


class UniqueConstraintError(TreeError):
    """Thrown when trying to add the same node_id to the same parent"""


class AmbigousMatchError(TreeError):
    """Thrown when a single-value lookup found multiple matches."""


class IterMethod(Enum):
    """Traversal order."""

    #: Depth-first, pre-order
    PRE_ORDER = "pre"
    #: Depth-first, post-order
    POST_ORDER = "post"
    #: Breadth-first (aka level-order)
    LEVEL_ORDER = "level"


# ------------------------------------------------------------------------------
# - Node
# ------------------------------------------------------------------------------
class Node:
    """"""

    def __init__(self, data, *, parent: "Node", data_id=None, node_id=None):
        self.data = data
        self._parent: Node = parent
        tree = parent.tree
        self.tree: "Tree" = tree
        self.children: List[Node] = None

        if data_id is None:
            self.data_id = tree._calc_data_id(data)
        else:
            self.data_id = data_id

        if node_id is None:
            self.node_id: int = id(self)
        else:
            self.node_id = node_id

        tree._register(self)

    def __repr__(self) -> str:
        return f"Node<{self.name!r}, data_id={self.data_id}>"
        # return f"Node<{self.name!r}, key={self.node_id}, data_id={self.data_id}>"

    def __eq__(self, other) -> bool:
        if isinstance(other, Node):
            return self.data == other.data
        return self.data == other

    # def __len__(self) -> int:
    #     raise NotImplementedError("Use `len(node.data)` or `len(node.children)`.")

    @property
    def name(self) -> str:
        return f"{self.data}"

    def rename(self, name) -> None:
        if type(self.data) is str:
            return self.set_data(name)
        raise ValueError("Can only rename plain string nodes")

    def set_data(self, data, *, data_id=None) -> None:
        return

    @property
    def parent(self) -> "Node":
        p = self._parent
        return p if p._parent else None

    # @property
    # def children(self) -> List["Node"]:
    #     """Return list of direct child nodes (list may be empty)."""
    #     c = self._children
    #     return [] if c is None else c

    # def get_children(self) -> List["Node"]:
    #     """Return list of direct child nodes (list may be empty)."""
    #     c = self.children
    #     return [] if c is None else c

    @property
    def first_child(self) -> Union["Node", None]:
        """First direct child node or None if no children exist."""
        return self.children[0] if self.children else None

    @property
    def last_child(self) -> Union["Node", None]:
        """Last direct child node or None if no children exist."""
        return self.children[-1] if self.children else None

    @property
    def first_sibling(self) -> "Node":
        """Return first sibling (may be self)."""
        return self._parent.children[0]

    @property
    def prev_sibling(self) -> Union["Node", None]:
        """Predecessor or None, if node is first sibling."""
        if self.is_first_sibling():
            return None
        idx = self._parent.children.index(self)
        return self._parent.children[idx - 1]

    @property
    def next_sibling(self) -> Union["Node", None]:
        """Return successor or None, if node is last sibling."""
        if self.is_last_sibling():
            return None
        idx = self._parent.children.index(self)
        return self._parent.children[idx + 1]

    @property
    def last_sibling(self) -> "Node":
        """Return last node, that share own parent (may be `self`)."""
        return self._parent.children[-1]

    def get_siblings(self, include_self=False) -> List["Node"]:
        """Return a list of all sibling entries of self (excluding self)."""
        if include_self:
            return self._parent.children
        return [n for n in self._parent.children if n is not self]

    @property
    def level(self) -> int:
        """Return the number of parents (1 means top-level node)."""
        return self.count_parents()

    # --------------------------------------------------------------------------

    def is_top_level(self) -> bool:
        """Return true if this node has no parent."""
        return self._parent._parent is None

    def is_leaf(self) -> bool:
        """Return true if this node is an end node."""
        return not self.children

    def is_clone(self) -> bool:
        """Return true if this node's data is refernced at least one more time."""
        return bool(len(self.tree._nodes_by_data_id.get(self.data_id)) > 1)

    def is_first_sibling(self) -> bool:
        """Return true if this node is the first sibling."""
        return self is self._parent.children[0]

    def is_last_sibling(self) -> bool:
        """Return true if this node is the last sibling."""
        return self is self._parent.children[-1]

    def has_children(self) -> bool:
        """Return true if this node has one or more children."""
        return bool(self.children)

    def get_top(self) -> "Node":
        """Return top-level ancestor (may be self)."""
        root = self
        while root._parent._parent:
            root = root._parent
        return root

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

    def get_path(self, *, add_self=True, separator="/", repr="{node.node_id}") -> str:
        """Return ordered list of all parent nodes."""
        res = []
        parent = self if add_self else self._parent
        while parent:
            node = parent
            parent = parent._parent
            if parent:
                res.append(repr.format(node=node))
        res.reverse()
        return separator + separator.join(res)

    def count_descendants(self, leaves_only=False) -> int:
        """Return number of descendant nodes, not counting self."""
        all = not leaves_only
        i = 0
        for node in self.iterator():
            if all or not node.children:
                i += 1
        return i

    def count_parents(self) -> int:
        """Return depth of node, i.e. number of parents (0 means root node)."""
        level = 0
        pe = self._parent
        while pe is not None:
            level += 1
            pe = pe._parent
        return level

    def get_index(self) -> int:
        """Return index in sibling list."""
        if not self._parent:
            return 0
        return self._parent.children.index(self)

    def add_child(self, child, *, before=None, data_id=None, node_id=None) -> "Node":
        """Append or insert a new sub node.

        If child is an existing Node instance, a copy will be created that
        references the same data object. Note that adding the same data below
        one parent is not allowed.

        child (Node|Any):
            Either an existing Node or a data object.
        data_id (str|int|None):
            Pass None to
        node_id (str|int|None):
        before (bool|Node|None):

        """
        if isinstance(child, Node):
            if child.tree is self.tree:
                if child._parent is self:
                    raise UniqueConstraintError(f"Same parent not allowed: {child}")
                if data_id and data_id != child.data_id:
                    raise UniqueConstraintError(f"data_id conflict: {child}")
            else:
                raise NotImplementedError("Cross-tree adding")
            node = Node(child.data, parent=self, data_id=data_id, node_id=node_id)
        else:
            node = Node(child, parent=self, data_id=data_id, node_id=node_id)

        children = self.children
        if children is None:
            assert before in (None, True, False)
            self.children = [node]
        elif before is True:  # prepend
            children.insert(0, node)
        elif before:
            assert before._parent is self
            idx = children.index(before)  # raises ValueError
            children.insert(idx, node)
        else:
            children.append(node)

        return node

    #: Alias for add_child
    add = add_child

    def append_child(self, child: Union["Node", object], *, data_id=None, node_id=None):
        """Append a new sub node."""
        return self.add_child(child, data_id=data_id, node_id=node_id, before=None)

    def prepend_child(self, child, *, data_id=None, node_id=None):
        """Prepend a new sub node."""
        return self.add_child(
            child, data_id=data_id, node_id=node_id, before=self.first_child
        )

    def prepend_sibling(self, child, *, data_id=None, node_id=None) -> "Node":
        return self._parent.add_child(
            child, data_id=data_id, node_id=node_id, before=self
        )

    def append_sibling(self, child, *, data_id=None, node_id=None) -> "Node":
        next_node = self.next_sibling
        return self._parent.add_child(
            child, data_id=data_id, node_id=node_id, before=next_node
        )

    def move(
        self,
        new_parent: Union["Node", "Tree"],
        *,
        before: Union["Node", bool, None] = None
    ):
        """Move this node before or after `otherNode` ."""
        if new_parent is None:
            new_parent = self.tree._root
        # elif isinstance(new_parent, Tree):
        #     new_parent = new_parent._root
        elif hasattr(new_parent, "_root"):  # it's a Tree
            new_parent = new_parent._root

        if new_parent.tree is not self.tree:
            raise NotImplementedError("Can only move nodes inside this tree")

        self._parent.children.remove(self)
        self._parent = new_parent

        target_siblings = new_parent.children
        if target_siblings is None:
            assert before in (None, True, False)
            new_parent.children = [self]
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
        """Remove this node.

        For ObjectTrees this is different from tree.remove(obj), because only
        this single node is removed, even if there are multiple instances.
        """
        self.remove_children()
        self.tree._unregister(self)
        self._parent.children.remove(self)

    def remove_children(self):
        """Remove all children of this node, making it a leaf node."""
        _unregister = self.tree._unregister
        for n in self._iter_post():
            _unregister(n)
        self.children = None
        return

    def copy_from(self, src_node: "Node", *, predicate=None):
        """Append copies of all source children to self."""
        assert not self.children
        for child in src_node.children:
            if predicate and predicate(child) is False:
                continue
            new_child = self.add_child(child.data, data_id=child.data_id)
            if child.has_children():
                new_child.copy_from(child, predicate=predicate)
        return

    def from_dict(self, obj: List[Dict], *, mapper=None):
        """Append copies of all source children to self."""
        assert not self.children
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

    def _iter_pre(self, *, predicate=None):
        """Depth-first, pre-order traversal."""
        children = self.children
        if children:
            for c in children:
                if predicate is None or predicate(c) is not False:
                    yield c
                    yield from c._iter_pre(predicate=predicate)
        return

    def _iter_post(self, *, predicate=None):
        """Depth-first, post-order traversal."""
        children = self.children
        if children:
            for c in self.children:
                if predicate is None or predicate(c) is not False:
                    yield from c._iter_post(predicate=predicate)
                    yield c
        return

    def _iter_level(self, *, predicate=None):
        """Breadth-first (aka level-order) traversal."""
        children = self.children
        while children:
            next_level = []
            for c in children:
                if predicate is None or predicate(c) is not False:
                    yield c
                    if c.children:
                        next_level.extend(c.children)
            children = next_level
        return

    def iterator(
        self, method=IterMethod.PRE_ORDER, *, predicate=None, include_self=False
    ) -> Generator["Node", None, None]:
        """Generator that walks the entry hierarchy."""
        try:
            handler = getattr(self, f"_iter_{method.value}")
        except AttributeError:
            raise NotImplementedError(f"Unsupported traversal method '{method}'.")
        if include_self:
            yield self
        yield from handler(predicate=predicate)

    __iter__ = iterator

    def filter(self, match, *, max_results=None, include_self=False):
        if callable(match):
            cb_match = match
        elif type(match) is str:
            pattern = re.compile(pattern=match)
            cb_match = lambda node: pattern.fullmatch(node.name)
        elif isinstance(match, (list, tuple)):
            pattern = re.compile(pattern=match[0], flags=match[1])
            cb_match = lambda node: pattern.fullmatch(node.name)
        else:
            cb_match = lambda node: node.data is match

        count = 0
        for node in self.iterator(include_self=include_self):
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
        match=None,
        data_id=None,
        include_self=False,
        max_results=None
    ):
        if data:
            assert data_id is None
            data_id = self.tree._calc_data_id(data)
        if data_id:
            assert match is None
            return [
                n
                for n in self.iterator(include_self=include_self)
                if n.data_id == data_id
            ]
        return [
            n
            for n in self.filter(
                match, include_self=include_self, max_results=max_results
            )
        ]

    def find_first(self, data=None, *, match=None, data_id=None):
        res = self.find_all(data, match=match, data_id=data_id, max_results=1)
        return res[0] if res else None

    #: Alias for find_first
    find = find_first

    def sort_children(self, *, cmp=None, node_id=None, reverse=False):
        raise NotImplementedError
        # if len(self.children) < 2:
        #     return
        # if node_id is None:
        #     node_id = lambda node: str(node.obj).lower()
        # self.children.sort(cmp, node_id, reverse)
        # return

    _CONNECTORS = {
        "space2": ("  ", "  ", "  ", "  ", "\n"),
        "space4": ("    ", " |  ", "    ", "    ", "\n"),
        "ascii22": ("  ", "| ", "`-", "+-", "\n"),
        "ascii32": ("   ", "|  ", "`- ", "+- ", "\n"),
        "ascii42": ("    ", " |  ", " `- ", " +- ", "\n"),
        "ascii43": ("    ", "|   ", "`-- ", "+-- ", "\n"),
        "lines32": ("   ", "│  ", "└─ ", "├─ ", "\n"),
        "lines42": ("    ", " │  ", " └─ ", " ├─ ", "\n"),
        "lines43": ("    ", " │  ", " └──", " ├──", "\n"),
        "round21": ("  ", "│ ", "╰ ", "├ ", "\n"),
        "round22": ("  ", "│ ", "╰─", "├─", "\n"),
        "round32": ("   ", "│  ", "╰─ ", "├─ ", "\n"),
        "round42": ("    ", " │  ", " ╰─ ", " ├─ ", "\n"),
        "round43": ("    ", "│   ", "╰── ", "├── ", "\n"),
        "serial": ("", "", "", "", ","),
    }
    DEFAULT_STYLE = "round43"
    DEFAULT_REPR = "{node.data!r}"

    def render_lines(self, *, repr=None, style=None):
        """Produces nodes as nicely formatted strings.

        Example:
            # Print the __repr__ of the data object:
            for s in tree.render_lines(repr="{node.data}"):
                print(s)
            # Print the __repr__ of the data object:
            for s in tree.render_lines(repr="{node.node_id}-{node.name}"):
                print(s)
        Example:
            def fmt(node):
                return
            tree.dump(lambda node: "%s" % node.obj)
        """
        if type(style) not in (list, tuple):
            style = self._CONNECTORS[style or self.DEFAULT_STYLE]
        if repr is None:
            repr = self.DEFAULT_REPR

        s0, s1, s2, s3, eol = style
        for n in self.iterator():
            s = []
            for p in n.get_parent_list():
                if p.is_last_sibling():
                    s.append(s0)  # "    "
                else:
                    s.append(s1)  # " |  "

            if n.is_last_sibling():
                s.append(s2)  # " `- "
            else:
                s.append(s3)  # " +- "

            if callable(repr):
                s.append(repr(n))
            else:
                s.append(repr.format(node=n))
            # s.append(eol)

            yield "".join(s)

        return

    def format(self, *, repr=None, style=None):
        """Print formatted branch to stdout.

        See render_lines() for custom formatting examples.
        """
        return "\n".join(self.render_lines(repr=repr, style=style))

    def to_dict(self, *, mapper=None) -> Dict:
        """Return a nested dict of this node and its children."""
        res = {
            "data": str(self.data),
        }
        # Add custom data_id if any
        data_id = hash(self.data)
        if data_id != self.data_id:
            res["data_id"] = data_id
        if mapper:
            mapper(self, res)
        if self.children:
            res["children"] = cl = []
            for n in self.children:
                cl.append(n.to_dict(mapper=mapper))
        return res

    def to_list_iter(self, *, mapper=None) -> Generator[Dict, None, None]:
        """Yield children as parent-referencing list.

        ```py
        [(parent_key, data)]
        ```
        """
        #: For nodes with multiple occurrences: index of the first one
        clone_idx_map = {}
        parent_id_map = {self.node_id: 0}
        for id_gen, node in enumerate(self, 1):
            # Compact mode: use integer sequence as keys
            # Store idx with original id for later parent-ref. We only have to
            # do this of nodes that have children though:
            node_id = node.node_id
            if node.children:
                parent_id_map[node_id] = id_gen

            parent_id = node._parent.node_id
            parent_idx = parent_id_map[parent_id]

            data = node.data
            data_id = hash(data)

            # If node is a 2nd occurence of a clone, only store the index of the
            # first occurence and do not call the mapper
            if clone_idx := clone_idx_map.get(data_id):
                yield (parent_idx, clone_idx)
                continue
            elif node.is_clone():
                clone_idx_map[data_id] = id_gen

            # If data is more complex than a simple string, or if we use a custom
            # data_id, we store data as a dict instead of a str:
            if type(data) is str:
                if data_id != node.data_id:
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
