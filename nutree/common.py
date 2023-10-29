# (c) 2021-2023 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Functions and declarations used by the :mod:`nutree.tree` and :mod:`nutree.node`
modules.
"""
from __future__ import annotations

import warnings
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Type, Union

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from .node import Node
    from .tree import Tree

#: Used as ID for the system root node
ROOT_ID: str = "__root__"

#: File format version used by `tree.save()` as `meta.$format_version`
FILE_FORMAT_VERSION: str = "1.0"

#: Type of ``Node.data_id``
DataIdType = Union[str, int]

#: Type of ``Tree(..., calc_data_id)```
CalcIdCallbackType = Callable[["Tree", Any], DataIdType]

#: Type of ``Tree(..., factory)```
NodeFactoryType = Type["Node"]


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
    """Raised or returned by traversal callbacks unconditionally accept all
    descendants."""


class StopTraversal(IterationControl):
    """Raised or returned by traversal callbacks to stop iteration.

    Optionally, a return value may be passed.
    Note that if a callback returns ``False``, this will be converted to an
    ``StopTraversal(None)`` exception.
    """

    def __init__(self, value=None):
        self.value = value


PredicateCallbackType = Callable[["Node"], Union[None, bool, IterationControl]]
MapperCallbackType = Callable[["Node", dict], Union[None, dict]]
# MatchCallbackType = Callable[["Node"], bool]
TraversalCallbackType = Callable[
    ["Node", Any], Union[None, bool, "StopTraversal", "SkipBranch"]
]

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
}


def get_version() -> str:
    from nutree import __version__

    return __version__


def call_mapper(fn, node: Node, data: dict) -> Any:
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


def call_predicate(fn, node):
    """Call the function and normalize result and exceptions.

    Handles `PredicateCallbackType`:
    Call `fn(node)` and converts all raised
    IterationControl responses to a canonical result.
    """
    if fn is None:
        return None
    try:
        res = fn(node)
    except IterationControl as e:
        return e  # SkipBranch, SelectBranch, StopTraversal
    except StopIteration as e:  # Also accept this builtin exception
        return StopTraversal(e.value)
    return res


def call_traversal_cb(fn, node, memo):
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
        if res is SkipBranch or isinstance(res, SkipBranch):
            return False
        elif res is StopTraversal or isinstance(res, StopTraversal):
            raise res
        elif res is False:
            raise StopTraversal
        elif res is StopIteration or isinstance(res, StopIteration):
            # Converts wrong syntax in exception handler...
            raise res
        elif res is not None:
            raise ValueError(
                "callback should not return values except for "
                f"False, SkipBranch, or StopTraversal: {res!r}."
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
        raise StopTraversal(e.value)
    return None
