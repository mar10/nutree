# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt and contributors; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Stress-test your web app.
"""

from enum import Enum

# if TYPE_CHECKING:  # Imported by type checkers, but prevent circular includes
#     from .tree import Node, Tree


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


class IterationControl:
    """Common base class for tree iteration controls."""


class SkipNode(IterationControl):
    """Raised or returned to skip current node, but continue with children and siblings."""


class SkipBranch(IterationControl):
    """Raised or returned to skip current node and children, but continue with siblings."""


class SkipAll(IterationControl):
    """Raised or returned to stop iteration."""
