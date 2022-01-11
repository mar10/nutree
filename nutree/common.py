# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt and contributors; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Stress-test your web app.
"""
import warnings
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Union

if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
    from .tree import Node

PredicateCallbackType = Callable[["Node"], Union[None, bool]]
MatchCallbackType = Callable[["Node"], bool]
TraversalCallbackType = Callable[
    ["Node", Any], Union[None, bool, "StopTraversal", "SkipChildren"]
]


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


class IterationControl(Exception):
    """Common base class for tree iteration controls."""


class SkipChildren(IterationControl):
    """Raised or returned by traversal callbacks to skip the current node's descendants."""


class StopTraversal(IterationControl):
    """Raised or returned by traversal callbacks to stop iteration.

    Optionally, a return value may be passed.
    Note that if a callback returns ``False``, this will be converted to an
    ``StopTraversal(None)`` exception.
    """

    def __init__(self, value=None):
        self.value = value


#: Node connector prefixes, for use with ``style`` argument.
CONNECTORS = {
    "space2": ("  ", "  ", "  ", "  "),
    "space4": ("    ", " |  ", "    ", "    "),
    "ascii22": ("  ", "| ", "`-", "+-"),
    "ascii32": ("   ", "|  ", "`- ", "+- "),
    "ascii42": ("    ", " |  ", " `- ", " +- "),
    "ascii43": ("    ", "|   ", "`-- ", "+-- "),
    "lines32": ("   ", "│  ", "└─ ", "├─ "),
    "lines42": ("    ", " │  ", " └─ ", " ├─ "),
    "lines43": ("    ", " │  ", " └──", " ├──"),
    "round21": ("  ", "│ ", "╰ ", "├ "),
    "round22": ("  ", "│ ", "╰─", "├─"),
    "round32": ("   ", "│  ", "╰─ ", "├─ "),
    "round42": ("    ", " │  ", " ╰─ ", " ├─ "),
    "round43": ("    ", "│   ", "╰── ", "├── "),
}

#: Default connector prefixes ``style`` argument.
DEFAULT_CONNECTOR_STYLE = "round43"

#: Default value for ``repr`` argument.
# DEFAULT_REPR = "{node.data}"
DEFAULT_REPR = "{node.data!r}"


def _call_traversal_cb(fn, node, memo):
    """Call the function and handle result and exceptions.

    This method calls `fn(node, memo)` and converts all returned or raised
    IterationControl responses to a canonical result:

    - Return `False` if the method returns SkipChildren or an instance of
      SkipChildren.
    - Raise `StopTraversal(value)` if the method returns False, StopTraversal, or an
      instance of StopTraversal.
    - If a form of StopIteration is returned, we treat as StopTraversal, but
      emit a warning.
    - Other return values are ignored and converted to None.
    """
    try:
        res = fn(node, memo)
        if res is SkipChildren or isinstance(res, SkipChildren):
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
                f"False, SkipChildren, or StopTraversal: {res!r}."
            )
    except SkipChildren:
        return False
    except StopIteration as e:
        # raise RuntimeError("Should raise StopTraversal instead")
        warnings.warn(
            "Should raise StopTraversal instead of StopIteration", RuntimeWarning
        )
        raise StopTraversal(e.value)
    return None
