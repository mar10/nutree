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
from importlib.metadata import PackageNotFoundError, version as dist_version
from pathlib import Path
import re


def _detect_version() -> str:
    """Resolve package version from installed metadata or local pyproject.toml."""
    try:
        return dist_version("nutree")
    except PackageNotFoundError:
        pass

    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    try:
        text = pyproject.read_text(encoding="utf-8")
        match = re.search(r"^version\s*=\s*['\"]([^'\"]+)['\"]", text, re.MULTILINE)
        if match:
            return match.group(1)
    except OSError:
        pass

    return "0.0.0"


__version__ = _detect_version()

from nutree.common import (
    AmbiguousMatchError,
    CycleDetectedError,
    DictWrapper,
    DuplicateNodeIdError,
    IterMethod,
    SelectBranch,
    SkipBranch,
    StopTraversal,
    StructureError,
    TreeError,
    UniqueConstraintError,
)
from nutree.diff import DiffClassification, diff_node_formatter
from nutree.fs import load_tree_from_fs
from nutree.node import Node
from nutree.tree import Tree
from nutree.typed_tree import TypedNode, TypedTree

__all__ = [
    "AmbiguousMatchError",
    "CycleDetectedError",
    "DictWrapper",
    "diff_node_formatter",
    "DiffClassification",
    "DuplicateNodeIdError",
    "IterMethod",
    "load_tree_from_fs",
    "Node",
    "SelectBranch",
    "SkipBranch",
    "StopTraversal",
    "StructureError",
    "Tree",
    "TreeError",
    "TypedNode",
    "TypedTree",
    "UniqueConstraintError",
]
