# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Functions and declarations used by the :mod:`nutree.tree` and :mod:`nutree.node`
modules.
"""
# MyPy incorrctly flags 'Exception must be derived from BaseException'
# mypy: disable-error-code="misc"

from __future__ import annotations

import io
import sys
import warnings
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Callable,
    Literal,
    Union,
)

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from nutree.node import Node
    from nutree.tree import Tree

    # TTree = TypeVar("TTree", bound=Tree)
    # TNode = TypeVar("TNode", bound=Node)


#: A sentinel object that can be used to detect if a parameter was passed.
# sentinel = unittest.mock.sentinel

#: Used as ID for the system root node
ROOT_DATA_ID: str = "__root__"
ROOT_NODE_ID: int = 0

#: File format version used by `tree.save()` as `meta.$format_version`
FILE_FORMAT_VERSION: str = "1.0"

#: Currently used Python version as string
PYTHON_VERSION = ".".join([str(s) for s in sys.version_info[:3]])


class TreeError(RuntimeError):
    """Base class for all `nutree` errors."""


class UniqueConstraintError(TreeError):
    """Thrown when trying to add the same node_id to the same parent"""


class AmbiguousMatchError(TreeError):
    """Thrown when a single-value lookup found multiple matches."""


class IterMethod(Enum):
    """Traversal order."""

    #: Depth-first, pre-order
    PRE_ORDER = "pre"
    #: Depth-first, post-order
    POST_ORDER = "post"
    #: Breadth-first (aka level-order)
    LEVEL_ORDER = "level"
    #: Breadth-first (aka level-order) right-to-left
    LEVEL_ORDER_RTL = "level_rtl"
    #: ZigZag order
    ZIGZAG = "zigzag"
    #: ZigZag order
    ZIGZAG_RTL = "zigzag_rtl"
    #: Random order traversal
    RANDOM_ORDER = "random"
    #: Fastest traversal in unpredictable order.
    #: It may appear to be the order of node insertion, but do not rely on this!
    UNORDERED = "unordered"


class IterationControl(Exception):
    """Common base class for tree iteration controls."""


class SkipBranch(IterationControl):
    """Raised or returned by traversal callbacks to skip the current node's descendants.

    If `and_self` is true, some iterators will consider the node itself, but
    still skip the descendants. For example :meth:`~nutree.tree.Tree.copy` and
    :meth:`~nutree.tree.Tree.find_all`.
    If `and_self` is false, some iterators will consider the node's children only.
    """

    def __init__(self, *, and_self=None):
        self.and_self = and_self


class SelectBranch(IterationControl):
    """Raised or returned by traversal callbacks to unconditionally accept all
    descendants."""


class StopTraversal(IterationControl):
    """Raised or returned by traversal callbacks to stop iteration.

    Optionally, a return value may be passed.
    Note that if a callback returns ``False``, this will be converted to a
    ``StopTraversal(None)`` exception.
    """

    def __init__(self, value=None):
        self.value = value


#: Type of ``Node.data_id``
DataIdType = Union[str, int]

#: Type of ``Tree(..., calc_data_id)```
CalcIdCallbackType = Callable[["Tree", Any], DataIdType]

#: Type of ``format(..., repr=)```
ReprArgType = Union[str, Callable[["Node"], str]]

#: A dict of scalar values
FlatJsonDictType = dict[str, Union[str, int, float, bool, None]]

#: Type of ``tree.save(..., key_map)``
KeyMapType = dict[str, str]

#: Type of ``tree.save(..., value_map)``
#: E.g. `{'t': ['person', 'dept']}`
ValueMapType = dict[str, list[str]]

#: E.g. `{'t': {'person': 0, 'dept': 1}}`
ValueDictMapType = dict[str, dict[str, int]]

#: Generic callback for `tree.to_dot()`, ...
MapperCallbackType = Callable[["Node", dict], Union[None, Any]]

#: Callback for `tree.save()`
SerializeMapperType = Callable[["Node", dict], Union[None, dict]]

#: Callback for `tree.load()`
DeserializeMapperType = Callable[["Node", dict], Union[str, object]]

#: Generic callback for `tree.filter()`, `tree.copy()`, ...
PredicateCallbackType = Callable[
    ["Node"], Union[None, bool, IterationControl, type[IterationControl]]
]

#:
MatchArgumentType = Union[str, PredicateCallbackType, list, tuple, Any]

#:
TraversalCallbackType = Callable[
    ["Node", Any],
    Union[
        None,
        bool,
        SkipBranch,
        StopTraversal,
        type[SkipBranch],
        type[StopTraversal],
        type[StopIteration],
    ],
]
#: Callback for `tree.sort(key=...)`
SortKeyType = Callable[["Node"], Any]
# SortKeyType = Callable[[Node], SupportsLess]

#: Node connector prefixes, for use with ``format(style=...)`` argument.
CONNECTORS = {
    "space1": (" ", " ", " ", " "),
    "space2": ("  ", "  ", "  ", "  "),
    "space3": ("   ", "   ", "   ", "   "),
    "space4": ("    ", " |  ", "    ", "    "),
    "ascii11": (" ", "|", "`", "-"),
    "ascii21": ("  ", "| ", "` ", "- "),
    "ascii22": ("  ", "| ", "`-", "+-"),
    "ascii32": ("   ", "|  ", "`- ", "+- "),
    "ascii42": ("    ", " |  ", " `- ", " +- "),
    "ascii43": ("    ", "|   ", "`-- ", "+-- "),
    "lines11": (" ", "│", "└", "├"),
    "lines21": ("  ", "│ ", "└ ", "├ "),
    "lines22": ("  ", "│ ", "└─", "├─"),
    "lines32": ("   ", "│  ", "└─ ", "├─ "),
    "lines42": ("    ", " │  ", " └─ ", " ├─ "),
    "lines43": ("    ", "│   ", "└── ", "├── "),
    "lines43r": ("    ", " │  ", " └──", " ├──"),
    "round11": (" ", "│", "╰", "├"),
    "round21": ("  ", "│ ", "╰ ", "├ "),
    "round22": ("  ", "│ ", "╰─", "├─"),
    "round32": ("   ", "│  ", "╰─ ", "├─ "),
    "round42": ("    ", " │  ", " ╰─ ", " ├─ "),
    "round43": ("    ", "│   ", "╰── ", "├── "),
    "round43r": ("    ", " │  ", " ╰──", " ├──"),
    # Compact styles
    "lines32c": (" ", "│", "└─ ", "├─ ", "└┬ ", "├┬ "),
    "lines43c": ("  ", "│ ", "└── ", "├── ", "└─┬ ", "├─┬ "),
    "round32c": (" ", "│", "╰─ ", "├─ ", "╰┬ ", "├┬ "),
    "round43c": ("  ", "│ ", "╰── ", "├── ", "╰─┬ ", "├─┬ "),
}

# ------------------------------------------------------------------------------
# Generic data object to be used when nutree.Node instances
# ------------------------------------------------------------------------------


class DictWrapper:
    """Wrap a Python dict so it can be added to the tree.

    Makes the dict hashable and comparable with `==`, so it can be used added to
    the tree and can be checked for modifications during tree diffing.

    Initialized with a dictionary of values. The values can be accessed
    via the `node.data` attribute like `node.data["KEY"]`.

    See :ref:`generic-node-data` for details.
    """

    __slots__ = ("_dict",)

    def __init__(self, dict_inst: dict | None = None, **values) -> None:
        self._dict: dict = {}
        if dict_inst is not None:
            # A dictionary was passed: store a reference to that instance
            if not isinstance(dict_inst, dict):
                raise TypeError("dict_inst must be a dictionary or None")
            if values:
                raise ValueError("Cannot pass both dict_inst and **values")
            self._dict = dict_inst
        else:
            # Single keyword arguments are passed (probably from unpacked dict):
            # store them in a new dictionary
            self._dict = values

    def __repr__(self):
        return f"{self.__class__.__name__}<{self._dict}>"

    def __hash__(self):
        # We return the id of the dict object, which is unique and stable.
        # Calculating a hash from the dict content is too expensive and would
        # not work anyway, since the result is used as a key in a reference map
        # and would not be adjusted, when the dict content changes.
        # It is good enough however to detect if the same dict instance is added
        # multiple times to the same tree.
        return id(self._dict)

    def __eq__(self, other):
        if isinstance(other, DictWrapper):
            d2 = other._dict
        elif isinstance(other, dict):
            d2 = other
        else:
            return False

        d = self._dict
        if d is d2:
            return True
        if set(d) != set(d2):
            return False
        for k, v in d.items():
            if d2[k] != v:
                return False
        return True

    def __setitem__(self, key, value):
        """Allow to access values as items.

        Example::

            `node.data["foo"] = 1` instead of `node.data._dict["foo"] = 1`.
        """
        self._dict[key] = value

    def __getitem__(self, key):
        """Allow to access values as items.

        E.g. ``foo = node.data["foo"]`` instead of `` foo = node.data._dict["foo"]``.
        """
        return self._dict[key]

    # def __getattr__(self, name: str) -> Any:
    #     """Allow to access values as attributes.

    #     Assuming the DictWrapper instance is stored in a Node.data instance,
    #     this allows to access the values like this::

    #             node.data.NAME

    #     If forward_attrs is enabled, this also allows to access the values like this::

    #             node.NAME

    #     See :ref:`generic-node-data`.
    #     """
    #     try:
    #         return self._dict[name]
    #     except KeyError:
    #         raise AttributeError(name) from None

    @classmethod
    def serialize_mapper(cls, nutree_node: Node, data: dict) -> Union[None, dict]:
        """Serialize the data object to a dictionary.

        Example::

            tree.save(file_path, mapper=DictWrapper.serialize_mapper)

        """
        assert isinstance(nutree_node.data, DictWrapper)
        return nutree_node.data._dict.copy()

    @classmethod
    def deserialize_mapper(cls, nutree_node: Node, data: dict) -> Union[str, object]:
        """Serialize the data object to a dictionary.

        Example::

            tree = Tree.load(file_path, mapper=DictWrapper.deserialize_mapper)
        """
        return cls(**data)


def get_version() -> str:
    from nutree import __version__

    return __version__


def check_python_version(min_version: tuple[Union[str, int], Union[str, int]]) -> bool:
    """Check for deprecated Python version."""
    if sys.version_info < min_version:
        min_ver = ".".join([str(s) for s in min_version[:3]])
        warnings.warn(
            f"Support for Python version less than `{min_ver}` is deprecated "
            f"(using {PYTHON_VERSION})",
            DeprecationWarning,
            stacklevel=2,
        )
        return False
    return True


def call_mapper(fn: MapperCallbackType | None, node: Node, data: dict) -> Any:
    """Call the function and normalize result and exceptions.

    Handles `MapperCallbackType`:
    Call `fn(node, data)` if defined and return the result.
    If `fn` is undefined or returns `None`, return `data`.
    """
    if fn is None:
        return data
    res = fn(node, data)
    if res is None:
        return data
    return res


def call_predicate(fn: Callable, node: Node) -> IterationControl | None | Any:
    """Call the function and normalize result and exceptions.

    Handles `PredicateCallbackType`:
    Call `fn(node)` and converts all raised
    IterationControl responses to a canonical result.
    """
    if fn is None:
        return None
    try:
        res = fn(node)
        if res in (SkipBranch, SelectBranch, StopTraversal):
            return res()
    except IterationControl as e:
        return e  # SkipBranch, SelectBranch, StopTraversal
    except StopIteration as e:  # Also accept this builtin exception
        return StopTraversal(e.value)
    return res


def call_traversal_cb(
    fn: TraversalCallbackType, node: Node, memo: Any
) -> Literal[False] | None:
    """Call the function and handle result and exceptions.

    This method calls `fn(node, memo)` and converts all returned or raised
    IterationControl responses to a canonical result:

    Handles `TraversalCallbackType`

    - Return `False` if the method returns SkipBranch or an instance of
      SkipBranch.
    - Raise `StopTraversal(value)` if the method returns False, StopTraversal, or an
      instance of StopTraversal.
    - If a form of StopIteration is returned, we treat as StopTraversal, but
      emit a warning.
    - Other return values are ignored and converted to None.
    """
    try:
        res = fn(node, memo)

        if res is None:
            return None
        elif res is SkipBranch or isinstance(res, SkipBranch):
            return False
        elif res is StopTraversal or isinstance(res, StopTraversal):
            raise res
        elif res is False:
            raise StopTraversal
        elif res is StopIteration or isinstance(res, StopIteration):
            # Converts wrong syntax in exception handler...
            raise res
        else:
            raise ValueError(
                "callback should not return values except for "
                f"None, False, SkipBranch, or StopTraversal: {res!r}."
            )
    except SkipBranch:
        return False
    except StopIteration as e:
        # raise RuntimeError("Should raise StopTraversal instead")
        warnings.warn(
            "Should raise StopTraversal instead of StopIteration",
            RuntimeWarning,
            stacklevel=3,
        )
        raise StopTraversal(e.value) from e
    return None


@contextmanager
def open_as_uncompressed_input_stream(
    path: str | Path,
    *,
    encoding: str = "utf8",
    auto_uncompress: bool = True,
) -> Iterator[IO[str]]:
    """Open a file for reading, decompressing if necessary.

    Decompression is done by checking for the magic header (independent of the
    file extension).

    Example::

        with open_as_uncompressed_stream("/path/to/foo.nutree") as fp:
            for line in fp:
                print(line)
    """
    path = Path(path)
    if auto_uncompress and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, mode="r") as zf:
            if len(zf.namelist()) != 1:
                raise ValueError(
                    f"ZIP file must contain exactly one file: {zf.namelist()}"
                )
            with zf.open(zf.namelist()[0], mode="r") as fp:
                yield io.TextIOWrapper(fp, encoding=encoding)
    else:
        with path.open(mode="r", encoding=encoding) as fp:
            yield fp
    return


@contextmanager
def open_as_compressed_output_stream(
    path: str | Path,
    *,
    compression: bool | int = True,
    encoding: str = "utf8",
) -> Iterator[IO[str]]:
    """Open a file for writing, ZIP-compressing if requested.

    Example::

        with open_as_compressed_stream("/path/to/foo.nutree") as fp:
            fp:
                print(line)
    """
    path = Path(path)
    if compression is False:
        with path.open("w", encoding=encoding) as fp:
            yield fp
    else:
        if compression is True:
            compression = zipfile.ZIP_BZIP2
        compression = int(compression)
        name = f"{path.name}.json"
        with zipfile.ZipFile(path, mode="w", compression=compression) as zf:
            with zf.open(name, mode="w") as fp:
                wrapper = io.TextIOWrapper(fp, encoding=encoding)
                yield wrapper
                wrapper.flush()
    return
