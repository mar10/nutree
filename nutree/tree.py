# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Declare the :class:`~nutree.tree.Tree` class.
"""

from __future__ import annotations

import copy
import json
import random
import threading
import warnings
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import (
    IO,
    Any,
    Generic,
    Literal,
    cast,
)

# typing.Self requires Python 3.11
from typing_extensions import Self, deprecated

from nutree.common import (
    FILE_FORMAT_VERSION,
    ROOT_DATA_ID,
    ROOT_NODE_ID,
    AmbiguousMatchError,
    CalcIdCallbackType,
    CycleDetectedError,
    DataIdType,
    DeserializeMapperType,
    DotMapperCallbackType,
    DuplicateNodeIdError,
    FlatJsonDictType,
    IterMethod,
    KeyMapType,
    MatchArgumentType,
    PredicateCallbackType,
    ReprArgType,
    SerializeMapperType,
    SortKeyType,
    TraversalCallbackType,
    UniqueConstraintError,
    ValueMapType,
    call_dot_mapper,
    check_python_version,
    get_version,
    open_as_compressed_output_stream,
    open_as_uncompressed_input_stream,
)
from nutree.diff import DiffCompareCallbackType, diff_tree
from nutree.dot import tree_to_dotfile
from nutree.mermaid import (
    MermaidDirectionType,
    MermaidEdgeMapperCallbackType,
    MermaidFormatType,
    MermaidNodeMapperCallbackType,
)
from nutree.node import Node, TData, TNode
from nutree.rdf import tree_to_rdf

_DELETED_TAG = "<deleted>"

#: Minimal Python version that is supported by nutree
MIN_PYTHON_VERSION_INFO = (3, 10)

check_python_version(MIN_PYTHON_VERSION_INFO)


# ------------------------------------------------------------------------------
# - _SystemRootNode
# ------------------------------------------------------------------------------
class _SystemRootNode(Node):
    """Invisible system root node."""

    def __init__(self, tree: Tree) -> None:
        self._tree: Tree = tree
        self._parent = None  # type: ignore
        self._node_id = ROOT_NODE_ID
        self._data_id = ROOT_DATA_ID
        self._data = tree.name
        self._children: list[Node] = []
        self._meta = None


# ------------------------------------------------------------------------------
# - Tree
# ------------------------------------------------------------------------------


class Tree(Generic[TData, TNode]):
    """
    Container for a hierarchy of :class:`~nutree.node.Node` objects.

    A tree wraps one invisible system root node; all visible top-level nodes are
    direct children of it. Trees provide methods to iterate, search, copy, filter,
    and serialize the hierarchy.

    Args:
        name: Optional name used when formatting or logging the tree.
        calc_data_id: Callback used to calculate data IDs. By default,
            ``hash(data)`` is used. See :meth:`calc_data_id`.
        forward_attrs: If true, expose attributes of ``node.data`` through the
            node. See :ref:`forward-attributes`.
        check_dag: If false, disable checks that prevent duplicate data below
            one parent and cycles. It is always enabled for
            :class:`~nutree.typed_tree.TypedTree`.
    """

    node_factory: type[TNode] = cast(type[TNode], Node)
    root_node_factory = _SystemRootNode

    #: Default connector prefixes ``format(style=...)`` argument.
    DEFAULT_CONNECTOR_STYLE = "round43"
    #: Default value for ``save(..., key_map=...)`` argument.
    DEFAULT_KEY_MAP: dict[str, str] = {"data_id": "i", "str": "s"}
    #: Default value for ``save(..., value_map=...)`` argument.
    DEFAULT_VALUE_MAP: dict[str, list[str]] = {}
    # #: Default value for ``save(..., mapper=...)`` argument.
    # DEFAULT_SERIALZATION_MAPPER = None
    # #: Default value for ``load(..., mapper=...)`` argument.
    # DEFAULT_DESERIALZATION_MAPPER = None

    def __init__(
        self,
        name: str | None = None,
        *,
        calc_data_id: CalcIdCallbackType | None = None,
        forward_attrs: bool = False,
        check_dag: bool = True,
    ) -> None:
        self._lock = threading.RLock()
        #: Tree name used for formatting output
        self.name: str = str(id(self) if name is None else name)
        self._root: Node = self.root_node_factory(self)  # type: ignore
        self._node_by_id: dict[int, TNode] = {}
        self._nodes_by_data_id: dict[DataIdType, list[TNode]] = {}
        # Optional callback that calculates data_ids from data objects
        # hash(data) is used by default
        self._calc_data_id_hook: CalcIdCallbackType | None = calc_data_id
        #: Enable aliasing when accessing node instances.
        self._forward_attrs: bool = forward_attrs
        # Enable cycle detection and prevent duplicate data for one parent
        # in `add_child()`. Note that is always enabled for TypedTree.
        self._check_dag = check_dag

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.name!r}>"

    def __delitem__(self, data: Any) -> None:
        """Implement ``del tree[data]`` syntax to remove nodes."""
        self[data].remove()

    def __enter__(self) -> Self:
        """Acquire the tree's reentrant lock for a ``with tree:`` block."""
        self._lock.acquire()
        return self

    def __exit__(
        self,
        type: type[BaseException] | None,
        value: BaseException | None,
        traceback: Any,
    ) -> None:
        self._lock.release()
        return

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError("Use `is` instead of `==`.")

    def __getitem__(self, data: object) -> TNode:
        """Look up a node using ``tree[data]`` syntax.

        `data` may be a Node, node_id, data_id or any data object.

        Lookup tries a node ID first, then a data ID, then the data object.
        If exactly one match is found, the corresponding node is returned;
        otherwise :class:`KeyError` or :class:`~nutree.common.AmbiguousMatchError`
        is raised.

        :class:`~nutree.common.AmbiguousMatchError` is raised if multiple matches
        are found.
        Use :meth:`find_all` or :meth:`find_first` instead to resolve this.

        Note: This is a flexible and concise way to access tree nodes. However,
        :meth:`find_all` or :meth:`find_first` may be faster and more explicit.
        """
        if isinstance(data, Node):
            data = id(data)

        # Support node_id lookup
        if isinstance(data, int):
            n = self._node_by_id.get(data)
            if n is not None:
                return n

        # Treat data as data_id
        if isinstance(data, (int, str)) and data in self._nodes_by_data_id:
            res = self.find_all(data_id=data)
        else:
            res = self.find_all(data)

        if not res:
            raise KeyError(f"{data!r}")
        elif len(res) > 1:
            raise AmbiguousMatchError(
                f"{data!r} has {len(res)} occurrences. "
                "Use tree.find_all() or tree.find_first() to resolve this."
            )
        return res[0]

    def __contains__(self, data: Any) -> bool:
        """Implement ``data in tree`` syntax to check for node existence.

        Uses the same lookup logic as :meth:`__getitem__`, but returns True/False
        instead of raising exceptions.
        """
        try:
            self[data]
        except KeyError:
            return False
        return True  # even for AmbiguousMatchError, we return True

    def __len__(self) -> int:
        """Make ``len(tree)`` return the number of all nodes (not just direct children).

        This also makes empty trees falsy.
        """
        return self.count

    def __reversed__(self):
        """Raise an error when trying to reverse the tree."""
        raise TypeError("Cannot reverse a tree")

    def calc_data_id(self, data: Any) -> DataIdType:
        """Called internally to calculate `data_id` for a `data` object.

        This value is used to lookup nodes by data, identify clones, and for
        (de)serialization. It defaults to ``hash(data)`` but may be overloaded
        when the data objects have meaningful keys that should be used instead.

        Note: By default, the __hash__() values of str and bytes objects are
        'salted' with an unpredictable random value. Although they remain constant
        within an individual Python process, they are not predictable between
        repeated invocations of Python.
        """
        if self._calc_data_id_hook:
            return self._calc_data_id_hook(self, data)  # type: ignore
        return hash(data)

    def _check_insert(self, node: TNode):
        """Raise error if inserting a node would violate DAG restrictions."""
        #  When this method is called from _register(), we can assume that
        # - check_dag is true,
        # - node.parent is set
        # - node already has at least one clone registered in self._nodes_by_data_id
        data_id = node._data_id
        if node._parent._children:
            for sibling in node._parent._children:
                if sibling._data_id == data_id:
                    raise UniqueConstraintError(
                        f"Node with data_id {data_id} already exists under same parent"
                        "Pass `check_dag=False` to the tree constructor to suppress "
                        "this restriction."
                    )
        for n in self._nodes_by_data_id[data_id]:
            if node.is_descendant_of(n):
                raise CycleDetectedError(
                    f"Inserting {node} would create a cycle with {n}"
                    "Pass `check_dag=False` to the tree constructor to suppress "
                    "this restriction."
                )

    def _register(self, node: TNode) -> None:
        assert node._tree is self
        assert node._node_id is not None
        if node._node_id in self._node_by_id:
            raise DuplicateNodeIdError(
                f"Node ID already registered: {node}"
            )  # pragma: no cover

        try:
            clone_list = self._nodes_by_data_id[node._data_id]  # may raise KeyError
            # if we get here, we are adding a clone and should check DAG compliance
            if self._check_dag and node._parent:
                self._check_insert(node)
            clone_list.append(node)
        except KeyError:
            self._nodes_by_data_id[node._data_id] = [node]
        self._node_by_id[node._node_id] = node

    def _unregister(self, node: TNode, *, clear: bool = True) -> None:
        """Unlink node from this tree (children must be unregistered first)."""
        assert node._node_id in self._node_by_id, f"{node}"
        del self._node_by_id[node._node_id]

        clones = self._nodes_by_data_id[node._data_id]
        # NOTE: `list.remove()` checks for equality ('=='), not identity!
        # This would remove the first clone, but not neccessarily `node`
        # clones.remove(node)
        for i, n in enumerate(clones):
            if n is node:
                clones.pop(i)
                break

        if not clones:
            del self._nodes_by_data_id[node._data_id]

        # Note: nulling the main attributes is not strictly neccessary, but
        # helps to detect bugs when accessing nodes after they were removed.
        # (We accept a violation of the type declarations in this case.)
        node._tree = None  # type: ignore
        node._parent = None  # type: ignore
        if clear:
            node._data = _DELETED_TAG
            node._data_id = None  # type: ignore
            node._node_id = None  # type: ignore
            node._children = None
            node._meta = None
        return

    @property
    def check_dag(self) -> bool:
        """Return true if cycle detection and duplicate data checks are enabled."""
        return self._check_dag

    @property
    def children(self) -> list[TNode]:
        """Return the direct child nodes, i.e. the top-level nodes."""
        return self.system_root.children

    def get_toplevel_nodes(self) -> list[TNode]:
        """Return the top-level nodes; an alias for :attr:`children`."""
        return self.system_root.children

    @property
    def system_root(self) -> TNode:
        return cast(TNode, self._root)

    @property
    def count(self) -> int:
        """Return the total number of nodes."""
        return len(self._node_by_id)

    @property
    def count_unique(self) -> int:
        """Return the number of unique data IDs in the tree.

        Multiple nodes that reference the same data object (clones) are counted
        once. This differs from :attr:`count`, which counts every node.
        """
        return len(self._nodes_by_data_id)

    def _set_data(
        self,
        node: TNode,
        data: TData,
        *,
        data_id: DataIdType | None = None,
        with_clones: bool | None = None,
    ) -> None:
        """Change node's `data` and/or `data_id` and update bookkeeping."""
        if not data and not data_id:
            raise TypeError("Missing data or data_id")

        if data is None or data is node._data:
            new_data = None
        else:
            new_data = data
            if data_id is None:
                data_id = self.calc_data_id(data)

        if data_id is None or data_id == node._data_id:
            new_data_id = None
        else:
            new_data_id = data_id

        node_map = self._nodes_by_data_id
        cur_nodes = node_map[node._data_id]
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
                    prev_clones = node_map[node._data_id]
                    del node_map[node._data_id]
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
                    node_map[node._data_id].remove(node)
                    try:  # are we adding to existing clones again?
                        node_map[new_data_id].append(node)
                    except KeyError:  # now a singleton with a new data_id
                        node_map[new_data_id] = [node]
                    node._data_id = new_data_id
                    if new_data:
                        node._data = new_data
            else:
                # data_id (and possibly data) changed for a *single* node
                del node_map[node._data_id]
                try:  # are we creating a clone now?
                    node_map[new_data_id].append(node)
                except KeyError:  # still a singleton, just a new data_id
                    node_map[new_data_id] = [node]
                node._data_id = new_data_id
                if new_data:
                    node._data = new_data
        elif new_data:
            # `data` changed, but `data_id` remains the same:
            # simply replace the reference
            if with_clones:
                for n in cur_nodes:
                    n._data = data
            else:
                node._data = new_data

        return

    @classmethod
    def serialize_mapper(
        cls, node: Node, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Used as default `mapper` argument for :meth:`save`."""
        return data

    @classmethod
    def deserialize_mapper(
        cls, parent: Node, data: dict[str, Any]
    ) -> str | object | None:
        """Used as default `mapper` argument for :meth:`load`."""
        raise NotImplementedError(
            f"Override this method or pass a mapper callback to evaluate {data}."
        )

    def first_child(self) -> TNode | None:
        """Return the first top-level node, or ``None`` if the tree is empty."""
        return self.system_root.first_child()

    def last_child(self) -> TNode | None:
        """Return the last top-level node, or ``None`` if the tree is empty."""
        return self.system_root.last_child()

    def get_random_node(self) -> TNode:
        """Return a random node.

        Note that there is also `IterMethod.RANDOM_ORDER`.
        """
        nbid = self._node_by_id
        return nbid[random.choice(list(nbid.keys()))]

    def calc_height(self) -> int:
        """Return the maximum depth of all nodes."""
        return self.system_root.calc_height()

    def visit(
        self,
        callback: TraversalCallbackType,
        *,
        method: IterMethod = IterMethod.PRE_ORDER,
        memo: Any = None,
    ) -> Any | None:
        """Call `callback(node, memo)` for all nodes.

        See Node's :meth:`~nutree.node.Node.visit` method and
        :ref:`iteration-callbacks` for details.
        """
        return self.system_root.visit(
            callback, add_self=False, method=method, memo=memo
        )

    def iterator(self, method: IterMethod = IterMethod.PRE_ORDER) -> Iterator[TNode]:
        """Traverse tree structure and yield nodes.

        See Node's :meth:`~nutree.node.Node.iterator` method for details.
        """
        if method == IterMethod.UNORDERED:
            return (n for n in self._node_by_id.values())
        elif method == IterMethod.RANDOM_ORDER:
            values = list(self._node_by_id.values())
            random.shuffle(values)
            return (n for n in values)
        return self.system_root.iterator(method=method)

    #: Implement ``for node in tree: ...`` syntax to iterate nodes depth-first.
    __iter__ = iterator

    def format_iter(
        self,
        *,
        repr: ReprArgType | None = None,
        style: str | None = None,
        title: str | bool | None = None,
    ) -> Iterator[str]:
        """This variant of :meth:`format` returns a line generator."""
        if title is None:
            title = False if style == "list" else True
        if title:
            yield f"{self}" if title is True else f"{title}"
        has_title = title is not False
        yield from self.system_root.format_iter(
            repr=repr, style=style, add_self=has_title
        )

    def format(
        self,
        *,
        repr: ReprArgType | None = None,
        style: str | None = None,
        title: str | bool | None = None,
        join: str = "\n",
    ) -> str:
        """Return a pretty string representation of the tree hierarchy.

        See Node's :meth:`~nutree.node.Node.format` method for details.
        """
        lines_iter = self.format_iter(repr=repr, style=style, title=title)
        return join.join(lines_iter)

    def print(
        self,
        *,
        repr: ReprArgType | None = None,
        style: str | None = None,
        title: str | bool | None = None,
        join: str = "\n",
        file: IO[str] | None = None,
    ) -> None:
        """Print the formatted tree to ``file``."""
        print(
            self.format(repr=repr, style=style, title=title, join=join),
            file=file,
        )

    def add_child(
        self,
        child: TNode | Self | TData,
        *,
        before: TNode | bool | int | None = None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> TNode:
        """Add a top-level node; an alias for :meth:`add`.

        See Node's :meth:`~nutree.node.Node.add_child` method for details.
        """
        return self.system_root.add_child(
            child,
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
        child: TNode | Self | TData,
        *,
        before: TNode | bool | int | None = None,
        deep: bool | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> TNode:
        """Add a top-level node; an alias for :meth:`add_child`.

        See Node's :meth:`~nutree.node.Node.add_child` method for details.
        """
        return self.system_root.add_child(
            child,
            before=before,
            deep=deep,
            data_id=data_id,
            node_id=node_id,
        )

    def copy(
        self,
        *,
        name: str | None = None,
        predicate: PredicateCallbackType | None = None,
    ) -> Self:
        """Return a shallow copy of this tree.

        New :class:`Tree` and :class:`Node` instances are created.
        The new nodes reference the original data objects.

        `predicate` may be passed to filter the result, which is equivalent to
        calling :meth:`~nutree.tree.Tree.filtered`.

        See Node's :meth:`~nutree.node.Node.copy_to` and :ref:`iteration-callbacks`
        method for details.

        See :meth:`~nutree.tree.Tree.deepcopy` for a variant that deep-copies
        the data objects.
        """
        if name is None:
            name = self.name

        new_tree = self.__class__(name, calc_data_id=self._calc_data_id_hook)

        with self:
            new_tree.system_root._add_from(self.system_root, predicate=predicate)
        return new_tree

    def __copy__(self) -> Self:
        """Return a shallow copy of this tree.

        Calling ``copy.copy(tree)`` is equivalent to ``tree.copy()``.

        New :class:`Tree` and :class:`Node` instances are created.
        The new nodes reference the original data objects.
        """
        return self.copy(name=self.name)

    def deepcopy(
        self,
        *,
        name: str | None = None,
        memo: dict[int, Any] | None = None,
    ) -> Self:
        """Return a deep copy of this tree.

        New :class:`Tree` and :class:`Node` instances are created.
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

        def _copy_children(source_parent: TNode, target_parent: TNode) -> None:
            for c in source_parent.children:
                new_data = copy.deepcopy(c.data, memo)

                # Let the new tree calculate the new data_id unless the original node
                # had a custom data_id, in which case we keep it
                if c.data_id == self.calc_data_id(c.data):
                    new_data_id = None
                else:
                    new_data_id = c.data_id
                new_node = target_parent.add(new_data, deep=False, data_id=new_data_id)

                _copy_children(c, new_node)

        with self:
            _copy_children(self.system_root, new_tree.system_root)

        return new_tree

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        """Return a deep copy of this tree.

        Calling ``copy.deepcopy(tree)`` is equivalent to ``tree.deepcopy()``.

        New :class:`Tree` and :class:`Node` instances are created.
        The new nodes reference deep-copied data objects.
        """
        return self.deepcopy(name=self.name, memo=memo)

    def copy_to(self, target: TNode | Self, *, deep: bool = True) -> None:
        """Copy this tree's nodes to another target.

        See Node's :meth:`~nutree.node.Node.copy_to` method for details.
        """
        with self:
            self.system_root.copy_to(target, add_self=False, before=None, deep=deep)

    def filter(self, predicate: PredicateCallbackType) -> None:
        """In-place removal of unmatching nodes.

        See also :ref:`iteration-callbacks`.
        """
        self.system_root.filter(predicate=predicate)

    def filtered(self, predicate: PredicateCallbackType) -> Self:
        """Return a filtered copy of this tree.

        See also :ref:`iteration-callbacks`.
        """
        if not predicate:
            raise TypeError("Predicate is required (use copy() instead)")
        return self.copy(predicate=predicate)

    def map(self, fn: Callable[[TData], TData]) -> Self:
        """Return a copy of this tree with mapped data.

        Using Python's built-in function ``map(fn, tree)`` would flatten all
        nodes and return a list of node objects. |br|
        In contrast, ``tree.map(fn)`` is intended to transform the node.data,
        while keeping the tree hierarchy intact.

        Note pitfall: a *shallow* copy of the tree is created first, and then
        ``fn(node.data)`` is called for each node.
        This means that the new tree's nodes reference the same data objects as
        the original tree, so if a data object is mutated, it will also affect
        the original tree. |br|
        If this is not desired, you can either make sure that ``fn`` returns a
        new data object, or alternatively make a deepcopy first:
        ``new_tree = tree.deepcopy().map(fn)``.
        """
        new_tree = self.copy()
        for node in new_tree:
            new_data = fn(node.data)
            if node.data is not new_data:
                node.set_data(data=new_data, with_clones=False)
        return new_tree

    def clear(self) -> None:
        """Remove all nodes from this tree."""
        self.system_root.remove_children()

    def find_all(
        self,
        data: Any = None,
        *,
        match: MatchArgumentType | None = None,
        data_id: DataIdType | None = None,
        max_results: int | None = None,
    ) -> list[TNode]:
        """Return a list of matching nodes (list may be empty).

        See also Node's :meth:`~nutree.node.Node.find_all` method and
        :ref:`iteration-callbacks`.
        """
        if data is not None:
            assert data_id is None
            data_id = self.calc_data_id(data)

        if data_id is not None:
            assert match is None
            res = self._nodes_by_data_id.get(data_id)
            if res:
                return res[max_results:] if max_results else res
            return []

        elif match is not None:
            return self.system_root.find_all(match=match, max_results=max_results)

        raise NotImplementedError

    def find_first(
        self,
        data: Any = None,
        *,
        match: MatchArgumentType | None = None,
        data_id: DataIdType | None = None,
        node_id: int | None = None,
    ) -> TNode | None:
        """Return the first matching node or `None`.

        Note that 'first' sometimes means 'one arbitrary' matching node, which
        is not necessarily the first node in a particular iteration order.
        See also Node's :meth:`~nutree.node.Node.find_first` method and
        :ref:`iteration-callbacks`.
        """
        if data is not None:
            if data_id is not None:
                raise TypeError("Cannot pass both `data` and `data_id`")
            data_id = self.calc_data_id(data)

        if data_id is not None:
            if match is not None or node_id is not None:
                raise TypeError(
                    "Cannot pass `data_id` together with `match` or `node_id`"
                )
            res = self._nodes_by_data_id.get(data_id)
            return res[0] if res else None
        elif match is not None:
            if node_id is not None:
                raise TypeError("Cannot pass `match` together with `node_id`")
            return self.system_root.find_first(match=match)
        elif node_id is not None:
            return self._node_by_id.get(node_id)
        raise NotImplementedError

    @deprecated("Use Tree.find_first() instead.")
    def find(self, *args, **kwargs):
        """Alias for :meth:`find_first`.

        .. deprecated:: 1.2
            Use :meth:`find_first` instead.
        """
        warnings.warn(
            "Tree.find() is deprecated since v1.2, use Tree.find_first() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.find_first(*args, **kwargs)

    def sort(
        self,
        *,
        key: SortKeyType | None = None,
        reverse: bool = False,
        deep: bool = True,
    ) -> None:
        """Sort child nodes recursively.

        `key` defaults to ``attrgetter("name")``, so children are sorted by
        their string representation.
        """
        self.system_root.sort_children(key=key, reverse=reverse, deep=deep)

    def sorted(
        self,
        *,
        key: SortKeyType | None = None,
        reverse: bool = False,
        deep: bool = True,
    ) -> Self:
        """Return a sorted copy of this node and descendants as tree.

        See also :ref:`iteration-callbacks`.
        """
        new_tree = self.copy()
        new_tree.sort(key=key, reverse=reverse, deep=deep)
        return new_tree

    def to_dict_list(
        self, *, mapper: SerializeMapperType | None = None
    ) -> list[dict[str, Any]]:
        """Call Node's :meth:`~nutree.node.Node.to_dict` method for all
        child nodes and return list of results."""
        res = []
        with self:
            for n in self.system_root._children:  # type: ignore
                res.append(n.to_dict(mapper=mapper))
        return res

    @classmethod
    def from_dict(
        cls, obj: list[dict[str, Any]], *, mapper: DeserializeMapperType | None = None
    ) -> Self:
        """Return a new :class:`Tree` instance from a list of dicts.

        See also :meth:`~nutree.tree.Tree.to_dict_list` and
        Node's :meth:`~nutree.node.Node.find_first` methods, and
        :ref:`iteration-callbacks`.
        """
        new_tree = cls()
        new_tree.system_root.from_dict(obj, mapper=mapper)
        return new_tree

    def to_list_iter(
        self,
        *,
        mapper: SerializeMapperType | None = None,
        key_map: KeyMapType | None = None,
        value_map: ValueMapType | None = None,
    ) -> Iterator[tuple[DataIdType, FlatJsonDictType | str | int]]:
        """Yield nodes as a compact, parent-referencing list.

        ``mapper`` serializes custom data objects. ``key_map`` and ``value_map``
        optionally replace repeated keys and values with compact representations.
        See :ref:`serialize`.
        """
        yield from self.system_root.to_list_iter(
            mapper=mapper, key_map=key_map, value_map=value_map
        )

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
        """Store this tree in compact JSON.

        ``target`` may be a file path, :class:`~pathlib.Path`, or text file
        object. ``mapper`` serializes custom data objects and ``meta`` adds
        fields to the file header.

        If ``compression`` is true, use gzip-compatible ZIP compression.
        Other supported values are ``ZIP_STORED``, ``ZIP_BZIP2``, and
        ``ZIP_LZMA``. Pass ``False`` to store uncompressed JSON. ``key_map`` and
        ``value_map`` control optional compact representations.

        See :ref:`serialize`, :meth:`to_list_iter`, and :meth:`load`.
        """
        if isinstance(target, (str, Path)):
            # with Path(target).open("wt", encoding="utf8") as fp:
            with open_as_compressed_output_stream(
                target, compression=compression
            ) as fp:
                return self.save(
                    target=fp,
                    mapper=mapper,
                    meta=meta,
                    key_map=key_map,
                    value_map=value_map,
                )
        # target is a file object now

        # print("key_map", key_map, self, self.DEFAULT_KEY_MAP)
        if key_map is True:
            key_map = self.DEFAULT_KEY_MAP
        elif key_map is False:
            key_map = {}

        if value_map is True:
            value_map = self.DEFAULT_VALUE_MAP
        elif value_map is False:
            value_map = {}

        header: dict[str, Any] = {
            "$generator": f"nutree/{get_version()}",
            "$format_version": FILE_FORMAT_VERSION,
        }
        if key_map:
            header["$key_map"] = key_map

        if value_map:
            header["$value_map"] = value_map

        if meta:
            header.update(meta)

        with self:
            # Materialize node list, so we can lock the snapshot.
            # Also because json.dump() does not support streaming anyway.
            # TODO: Use s.th. like https://github.com/daggaz/json-stream ?
            res = {
                "meta": header,
                "nodes": list(
                    self.to_list_iter(
                        mapper=mapper, key_map=key_map, value_map=value_map
                    )
                ),
            }

        json.dump(res, target, indent=None, separators=(",", ":"))
        return

    @classmethod
    def _uncompress_entry(
        cls,
        data: dict[str, Any] | str,
        inverse_key_map: dict[str, str],
        value_map: ValueMapType,
    ) -> None:
        # if isinstance(data, str):
        #     return
        assert isinstance(data, dict), data
        for key, value in list(data.items()):
            if key in inverse_key_map:
                long_key = inverse_key_map[key]
                data[long_key] = data.pop(key)
            else:
                long_key = key

            if isinstance(value, int) and long_key in value_map:
                data[long_key] = value_map[long_key][value]
        return

    @classmethod
    def _from_list(
        cls,
        obj: list[tuple[int, str | dict[str, Any]]],
        *,
        mapper: DeserializeMapperType | None = None,
    ) -> Self:
        tree = cls()  # Tree or TypedTree
        node_idx_map: dict[int, TNode] = {0: tree.system_root}
        if mapper is None:
            mapper = cls.deserialize_mapper

        for idx, (parent_idx, data) in enumerate(obj, 1):
            parent = node_idx_map[parent_idx]
            # print(idx, parent_idx, data, parent)
            if isinstance(data, str):
                n = parent.add(data)
            elif isinstance(data, int):
                first_clone = node_idx_map[data]
                n = parent.add(first_clone, data_id=first_clone.data_id)
            else:
                assert isinstance(data, dict), data
                data_id = data.get("data_id")
                data = call_dot_mapper(mapper, parent, data)
                n = parent.add(data, data_id=data_id)
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
        auto_uncompress: bool = True,
    ) -> Self:
        """Create a :class:`Tree` from a file path or JSON text stream.

        If ``file_meta`` is a dictionary, it is updated with the file's
        ``meta`` header. Compressed files are detected automatically unless
        ``auto_uncompress`` is false.

        See :meth:`save`.
        """
        if isinstance(target, (str, Path)):
            # Check for zip file
            # with Path(target).open("rt", encoding="utf8") as fp:
            with open_as_uncompressed_input_stream(
                target,
                auto_uncompress=auto_uncompress,
            ) as fp:
                return cls.load(target=fp, mapper=mapper, file_meta=file_meta)
        # target is a file object now

        obj = json.load(target)
        if (
            not isinstance(obj, dict)
            or "meta" not in obj
            or "nodes" not in obj
            or "$generator" not in obj["meta"]
            or "nutree/" not in str(obj["meta"]["$generator"])
        ):
            raise RuntimeError("Invalid file format")

        if isinstance(file_meta, dict):
            file_meta.update(obj["meta"])

        # Uncompress key/value maps
        key_map = obj["meta"].get("$key_map", {})
        inverse_key_map: dict[str, Any] = {v: k for k, v in key_map.items()}
        # print("inverse_key_map", inverse_key_map)

        value_map = obj["meta"].get("$value_map", {})
        # print("value_map", value_map)

        for _parent_idx, data in obj["nodes"]:
            # print("load data", data)
            if isinstance(data, dict):
                cls._uncompress_entry(data, inverse_key_map, value_map)
                # print("      -> ", data)

        nodes = obj["nodes"]
        return cls._from_list(nodes, mapper=mapper)

    def to_dot(
        self,
        *,
        add_root: bool = True,
        unique_nodes: bool = True,
        graph_attrs: dict[str, Any] | None = None,
        node_attrs: dict[str, Any] | None = None,
        edge_attrs: dict[str, Any] | None = None,
        node_mapper: DotMapperCallbackType | None = None,
        edge_mapper: DotMapperCallbackType | None = None,
    ) -> Iterator[str]:
        """Generate a DOT formatted graph representation.

        See Node's :meth:`~nutree.node.Node.to_dot` method for details.
        """
        yield from self.system_root.to_dot(
            add_self=add_root,
            unique_nodes=unique_nodes,
            graph_attrs=graph_attrs,
            node_attrs=node_attrs,
            edge_attrs=edge_attrs,
            node_mapper=node_mapper,
            edge_mapper=edge_mapper,
        )

    def to_dotfile(
        self,
        target: IO[str] | str | Path,
        *,
        format: str | None = None,
        add_root: bool = True,
        unique_nodes: bool = True,
        graph_attrs: dict[str, Any] | None = None,
        node_attrs: dict[str, Any] | None = None,
        edge_attrs: dict[str, Any] | None = None,
        node_mapper: DotMapperCallbackType | None = None,
        edge_mapper: DotMapperCallbackType | None = None,
    ) -> None:
        """Serialize a DOT formatted graph representation.

        ``format`` optionally converts the DOT output to a Graphviz format.
        See :ref:`graphs` for details.
        """
        tree_to_dotfile(
            self,
            target,
            format=format,
            add_root=add_root,
            unique_nodes=unique_nodes,
            graph_attrs=graph_attrs,
            node_attrs=node_attrs,
            edge_attrs=edge_attrs,
            node_mapper=node_mapper,
            edge_mapper=edge_mapper,
        )
        return

    def to_mermaid_flowchart(
        self,
        target: IO[str] | str | Path,
        *,
        as_markdown: bool = True,
        direction: MermaidDirectionType = "TD",
        title: str | bool | None = True,
        format: MermaidFormatType | None = None,
        mmdc_options: dict[str, Any] | None = None,
        add_root: bool = True,
        unique_nodes: bool = True,
        headers: Iterable[str] | None = None,
        root_shape: str | None = None,
        node_mapper: MermaidNodeMapperCallbackType | str | None = None,
        edge_mapper: MermaidEdgeMapperCallbackType | str | None = None,
    ) -> None:
        """Serialize a Mermaid flowchart representation.

        ``format`` optionally renders the flowchart using Mermaid CLI.
        See :ref:`graphs` for details.
        """
        self.system_root.to_mermaid_flowchart(
            target=target,
            as_markdown=as_markdown,
            direction=direction,
            title=title,
            format=format,
            mmdc_options=mmdc_options,
            add_self=add_root,
            unique_nodes=unique_nodes,
            headers=headers,
            root_shape=root_shape,
            node_mapper=node_mapper,
            edge_mapper=edge_mapper,
        )
        return

    def to_rdf_graph(self) -> Any:
        """Return an instance of ``rdflib.Graph``.

        See :ref:`graphs` for details.
        """
        return tree_to_rdf(self)

    def diff(
        self,
        other: Self,
        *,
        compare: DiffCompareCallbackType | bool = True,
        ordered: bool = False,
        reduce: bool = False,
    ) -> Tree:
        """Compare this tree with ``other`` and return an annotated union.

        The resulting tree contains a union of all nodes from this and the
        other tree.
        Additional metadata is added to the resulting nodes to classify changes
        from the perspective of this tree. For example a node that only exists
        in `other`, will have ``node.get_meta("dc") == DiffClassification.ADDED``
        defined.

        ``compare`` customizes node equality and should return ``True`` for
        equivalent nodes. If ``ordered`` is true, child order is compared too.
        If ``reduce`` is true, unchanged nodes are removed from the result.

        See :ref:`diff-and-merge` for details.
        """
        t = diff_tree(self, other, compare=compare, ordered=ordered, reduce=reduce)
        return t

    # def on(self, event_name: str, callback):
    #     raise NotImplementedError

    def _self_check(self) -> Literal[True]:
        """Internal method to check data structure sanity.

        This is slow: only use for debugging, e.g. ``assert tree._self_check()``.
        """
        node_list = []
        for node in self:
            node_list.append(node)
            assert node._tree is self, node
            assert node in node._parent._children, node  # type: ignore
            # assert node._data_id == self.calc_data_id(node.data), node
            assert node._data_id in self._nodes_by_data_id, node
            assert node._node_id == id(node), f"{node}: {node._node_id} != {id(node)}"
            assert node._children is None or len(node._children) > 0, (
                f"{node}: {node._children}"
            )

        assert len(self._node_by_id) == len(node_list)

        clone_count = 0
        for data_id, nodes in self._nodes_by_data_id.items():
            clone_count += len(nodes)
            for node in nodes:
                assert node._node_id in self._node_by_id, node
                assert node._data_id == data_id, node
        assert clone_count == len(node_list)
        return True

    @classmethod
    def build_random_tree(cls, structure_def: dict[str, Any]) -> Self:
        """Build a random tree for .

        Returns a new :class:`Tree` instance with random nodes, as defined by
        structure_def.
        If called like ``TypedTree.build_random_tree(structure_def)``, this
        method will return a :class:`~nutree.typed_tree.TypedTree` instance.

        See :ref:`randomize` for details.
        """
        from nutree.tree_generator import build_random_tree

        tt = build_random_tree(tree_class=cls, structure_def=structure_def)
        return cast(Self, tt)
