"""
Current version number.

See https://www.python.org/dev/peps/pep-0440

Examples
    Pre-releases (alpha, beta, release candidate):
        '3.0.0a1', '3.0.0b1', '3.0.0rc1'
    Final Release:
        '3.0.0'
    Developmental release (to mark 3.0.0 as 'used'. Don't publish this):
        '3.0.0.dev1'
NOTE:
    When pywin32 is installed, number must be a.b.c for MSI builds?
    "3.0.0a4" seems not to work in this case!
"""

# flake8: noqa
__version__ = "1.0.0"

from nutree.common import (
    AmbiguousMatchError,
    DictWrapper,
    IterMethod,
    SelectBranch,
    SkipBranch,
    StopTraversal,
    TreeError,
    UniqueConstraintError,
)
from nutree.diff import DiffClassification, diff_node_formatter
from nutree.fs import load_tree_from_fs
from nutree.node import Node
from nutree.tree import Tree
from nutree.typed_tree import TypedNode, TypedTree

__all__ = [  # type: ignore
    Tree,
    Node,
    AmbiguousMatchError,
    diff_node_formatter,
    DiffClassification,
    DictWrapper,
    IterMethod,
    load_tree_from_fs,
    SelectBranch,
    SkipBranch,
    StopTraversal,
    TreeError,
    TypedNode,
    TypedTree,
    UniqueConstraintError,
]
