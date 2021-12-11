# -*- coding: utf-8 -*-
import json
import threading
from typing import IO, Any, Dict, Generator, List, Union

from .node import AmbigousMatchError, IterMethod, Node


# ------------------------------------------------------------------------------
# - Tree
# ------------------------------------------------------------------------------
class Tree:
    """"""

    def __init__(self, name: str = None, *, factory=None):
        self._lock = threading.RLock()
        self.name = str(id(self) if name is None else name)
        self._node_factory = factory or Node
        self._root = _SystemRootNode(self)
        self._node_by_id = {}
        self._nodes_by_data_id = {}
        #: true when at least one custom data_id was passed
        self._use_custom_data_ids = None

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
        # TODO: treat data as data_id?
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

    def iterator(self, method: IterMethod = IterMethod.PRE_ORDER, *, predicate=None):
        return self._root.iterator(method=method, predicate=predicate)

    __iter__ = iterator

    def _calc_data_id(self, data) -> int:
        # Note By default, the __hash__() values of str and bytes objects are “salted”
        # with an unpredictable random value. Although they remain constant within an
        # individual Python process, they are not predictable between repeated invocations
        # of Python.
        return hash(data)

    @property
    def count(self):
        return len(self._node_by_id)

    @property
    def first_child(self):
        return self._root.first_child

    @property
    def last_child(self):
        return self._root.last_child

    def format(self, *, repr=None, style=None, title=True):
        prefix = ""
        if title:
            prefix = f"{self}\n" if title is True else f"{title}\n"
        return prefix + self._root.format(repr=repr, style=style)

    def add_child(self, child: Any, *, data_id=None, node_id=None, before=None):
        return self._root.add_child(
            child, data_id=data_id, node_id=node_id, before=before
        )

    #: Alias for `add_child`
    add = add_child

    def copy(self, *, name=None, predicate=None) -> "Tree":
        if name is None:
            name = f"Copy of {self}"
        new_tree = Tree(name)
        with self:
            new_tree._root.copy_from(self._root, predicate=predicate)
        return new_tree

    def _register(self, node: "Node"):
        assert node.tree is self
        # node.tree = self
        assert node.node_id and node.node_id not in self._node_by_id, f"{node}"
        self._node_by_id[node.node_id] = node
        try:
            self._nodes_by_data_id[node.data_id].append(node)
        except KeyError:
            self._nodes_by_data_id[node.data_id] = [node]

    def _unregister(self, node, *, clear=True):
        """Unlink node from this tree."""
        assert node.node_id in self._node_by_id, f"{node}"
        del self._node_by_id[node.node_id]

        clones = self._nodes_by_data_id[node.data_id]
        clones.remove(node)
        if not clones:
            del self._nodes_by_data_id[node.data_id]

        node.tree = None
        if clear:
            node.data = "<deleted>"
            node.node_id = None
            node.data_id = None
            node.children = None
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

    def intersect(self, other):
        raise NotImplementedError

    def to_dict(self, *, mapper=None) -> List[Dict]:
        """Return a list of child node's `node.to_dict()`."""
        res = []
        with self:
            for n in self._root.children:
                res.append(n.to_dict(mapper=mapper))
        return res

    @classmethod
    def from_dict(cls, obj: List[Dict], *, mapper=None) -> "Tree":
        new_tree = Tree()
        new_tree._root.from_dict(obj)
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
        """Internal method to check data structure sanity."""
        node_list = []
        for node in self:
            node_list.append(node)
            assert node.tree is self, node
            # assert node.data_id == self._calc_data_id(node.data), node
            assert node.data_id in self._nodes_by_data_id, node
            assert node.node_id == id(node), f"{node}: {node.node_id} != {id(node)}"

        assert len(self._node_by_id) == len(node_list)

        count_2 = 0
        for data_id, nodes in self._nodes_by_data_id.items():
            count_2 += len(nodes)
            for node in nodes:
                assert node.node_id in self._node_by_id, node
                assert node.data_id == data_id, node
        assert count_2 == len(node_list)
        return True


class _SystemRootNode(Node):
    """Invisible system root node."""

    def __init__(self, tree: Tree):

        self.tree: Tree = tree
        self._parent = None
        self.node_id = self.data_id = self.data = "__root__"
        self.children = []
