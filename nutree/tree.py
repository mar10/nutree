# -*- coding: utf-8 -*-
import json
import threading
from typing import IO, Any, Dict, Generator, List, Union

from .common import AmbigousMatchError, IterMethod
from .node import Node

_DELETED_TAG = "<deleted>"


# ------------------------------------------------------------------------------
# - Tree
# ------------------------------------------------------------------------------
class Tree:
    """"""

    def __init__(self, name: str = None, *, factory=None, calc_data_id=None):
        self._lock = threading.RLock()
        self.name = str(id(self) if name is None else name)
        self._node_factory = factory or Node
        self._root = _SystemRootNode(self)
        self._node_by_id = {}
        self._nodes_by_data_id = {}
        #: Optional callback that calculates data_ids from data objects
        #: hash(data) is used by default
        self._calc_data_id_hook = calc_data_id

    def __repr__(self):
        return f"Tree<{self.name!r}>"

    def __contains__(self, data):
        # TODO: treat data as data_id?
        return self._calc_data_id(data) in self._nodes_by_data_id

    def __len__(self):
        """Return the number of nodes (also makes empty trees falsy)."""
        return self.count

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, type, value, traceback):
        self._lock.release()
        return

    def __getitem__(self, data: object) -> "Node":
        """Implement `tree[data]` lookup.

        Note that AmbigousMatchError is raised if multiple matches are found.
        Use tree.find_all() or tree.find_first() instead to resolve this.
        """
        # Treat data as data_id
        if isinstance(data, Node):
            raise ValueError(f"Expected data instance or data_id: {data}")
        elif type(data) in (int, str) and data in self._nodes_by_data_id:
            res = self.find_all(data_id=data)
        else:
            res = self.find_all(data)

        if not res:
            raise KeyError(f"{data!r}")
        if len(res) == 1:
            return res[0]
        raise AmbigousMatchError(
            f"{data!r} has {len(res)} occurrences. "
            "Use tree.find_all() or tree.find_first() to resolve this."
        )

    def __eq__(self, other) -> bool:
        raise NotImplementedError("Use `is` or `tree.compare()` instead.")

    # def __iadd__(self, other) -> None:
    #     """Support `tree += node(s)` syntax"""
    #     self._root += other

    def iterator(self, method: IterMethod = IterMethod.PRE_ORDER, *, predicate=None):
        return self._root.iterator(method=method, predicate=predicate)

    __iter__ = iterator

    def _calc_data_id(self, data) -> int:
        """Called internally to calculate `data_id` for a `data` object.

        This value is used to llokup nodes by data, identify clones, and for
        (de)serlialization. It defaults to ``hash(data)`` but may be overloaded
        when the data objects have meaningful keys that should be used instead.
        """
        # Note By default, the __hash__() values of str and bytes objects are “salted”
        # with an unpredictable random value. Although they remain constant within an
        # individual Python process, they are not predictable between repeated invocations
        # of Python.
        if self._calc_data_id_hook:
            return self._calc_data_id_hook(self, data)
        return hash(data)

    @property
    def count(self):
        """Return the total number of nodes."""
        return len(self._node_by_id)

    @property
    def first_child(self):
        """Return the first top-level node."""
        return self._root.first_child

    @property
    def last_child(self):
        """Return the last top-level node."""
        return self._root.last_child

    def format(self, *, repr=None, style=None, title=None):
        prefix = ""
        if title is None:
            title = Node._CONNECTORS[style or Node.DEFAULT_STYLE][0]
        if title:
            prefix = f"{self}\n" if title is True else f"{title}\n"
        return prefix + self._root.format(repr=repr, style=style)

    def print(self, *, repr=None, style=None, title=None):
        """Convenience method that simply runs `print(self.format())`."""
        print(self.format(repr=repr, style=style, title=title))

    def add_child(self, child: Any, *, data_id=None, node_id=None, before=None):
        return self._root.add_child(
            child, data_id=data_id, node_id=node_id, before=before
        )

    #: Alias for `add_child`
    add = add_child

    def copy(self, *, name=None, predicate=None) -> "Tree":
        """Return a shallow copy of the tree.

        New `Tree` and `Node` instances are created. They reference the original
        data objects.
        """
        if name is None:
            name = f"Copy of {self}"
        new_tree = Tree(name)
        with self:
            new_tree._root.copy_from(self._root, predicate=predicate)
        return new_tree

    def clear(self) -> None:
        """Remove all nodes from the tree"""
        self._root.remove_children()

    def _register(self, node: "Node"):
        assert node._tree is self
        # node._tree = self
        assert node._node_id and node._node_id not in self._node_by_id, f"{node}"
        self._node_by_id[node._node_id] = node
        try:
            self._nodes_by_data_id[node._data_id].append(node)
        except KeyError:
            self._nodes_by_data_id[node._data_id] = [node]

    def _unregister(self, node, *, clear=True):
        """Unlink node from this tree (children must be unregistered first)."""
        assert node._node_id in self._node_by_id, f"{node}"
        del self._node_by_id[node._node_id]

        clones = self._nodes_by_data_id[node._data_id]
        clones.remove(node)
        if not clones:
            del self._nodes_by_data_id[node._data_id]

        node._tree = None
        node._parent = None
        if clear:
            node._data = _DELETED_TAG
            node._data_id = None
            node._node_id = None
            node._children = None
        return

    def find_all(
        self, data=None, *, match=None, data_id=None, max_results: int = None
    ) -> List["Node"]:
        if data is not None:
            assert data_id is None
            data_id = self._calc_data_id(data)

        if data_id is not None:
            assert match is None
            res = self._nodes_by_data_id.get(data_id)
            if res:
                return res[max_results:] if max_results else res
            return []
        elif match is not None:
            return self._root.find_all(match=match, max_results=max_results)
        raise NotImplementedError

    def find_first(
        self, data=None, *, match=None, data_id=None, node_id=None
    ) -> Union["Node", None]:
        if data is not None:
            assert data_id is None
            data_id = self._calc_data_id(data)

        if data_id is not None:
            assert match is None
            assert node_id is None
            res = self._nodes_by_data_id.get(data_id)
            return res[0] if res else None
        elif match is not None:
            assert node_id is None
            return self._root.find_first(match=match)
        elif node_id is not None:
            return self._node_by_id.get(node_id)
        raise NotImplementedError

    #: Alias for find_first
    find = find_first

    def to_dict(self, *, mapper=None) -> List[Dict]:
        """Call ``node.to_dict()`` for all childnodes and return list of results."""
        res = []
        with self:
            for n in self._root._children:
                res.append(n.to_dict(mapper=mapper))
        return res

    @classmethod
    def from_dict(cls, obj: List[Dict], *, mapper=None) -> "Tree":
        new_tree = Tree()
        new_tree._root.from_dict(obj, mapper=mapper)
        return new_tree

    def to_list_iter(self, *, mapper=None) -> Generator[Dict, None, None]:
        """Yield a parent-referencing list of child nodes."""
        return self._root.to_list_iter(mapper=mapper)

    def save(self, fp: IO[str], *, mapper=None) -> None:
        """Store in a compact JSON file stream."""
        with self:
            iter = self.to_list_iter(mapper=mapper)
            # Materialize so we can lock the snapshot.
            # Also because json.dump() does not supprt streaming
            # TODO: Use s.th. like https://github.com/daggaz/json-stream ?
            json.dump(list(iter), fp)
        return

    @classmethod
    def _from_list(cls, obj: List[Dict], *, mapper=None) -> "Tree":
        tree = Tree()
        node_idx_map = {0: tree._root}
        for idx, (parent_idx, data) in enumerate(obj, 1):
            parent = node_idx_map[parent_idx]
            # print(idx, parent_idx, data, parent)
            if type(data) is str:
                n = parent.add(data)
            elif type(data) is int:
                first_clone = node_idx_map[data]
                n = parent.add(first_clone)
            elif mapper:
                data = mapper(parent, data)
                n = parent.add(data)
            else:
                raise RuntimeError("Need mapper")  # pragma: no cover

            node_idx_map[idx] = n

        return tree

    @classmethod
    def load(cls, fp: IO[str], *, mapper=None) -> "Tree":
        """Load from a JSON file stream."""
        obj = json.load(fp)
        return cls._from_list(obj, mapper=mapper)

    def on(self, event_name: str, callback):
        raise NotImplementedError

    def _self_check(self):
        """Internal method to check data structure sanity.

        This is slow: only use for debugging, e.g. ``assert tree._self_check``.
        """
        node_list = []
        for node in self:
            node_list.append(node)
            assert node._tree is self, node
            assert node in node._parent._children, node
            # assert node._data_id == self._calc_data_id(node.data), node
            assert node._data_id in self._nodes_by_data_id, node
            assert node._node_id == id(node), f"{node}: {node._node_id} != {id(node)}"
            assert (
                node._children is None or len(node._children) > 0
            ), f"{node}: {node._children}"

        assert len(self._node_by_id) == len(node_list)

        clone_count = 0
        for data_id, nodes in self._nodes_by_data_id.items():
            clone_count += len(nodes)
            for node in nodes:
                assert node._node_id in self._node_by_id, node
                assert node._data_id == data_id, node
        assert clone_count == len(node_list)
        return True


class _SystemRootNode(Node):
    """Invisible system root node."""

    def __init__(self, tree: Tree):

        self._tree: Tree = tree
        self._parent = None
        self._node_id = self._data_id = self._data = "__root__"
        self._children = []
