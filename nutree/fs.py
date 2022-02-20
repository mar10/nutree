# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Methods and classes to support file system related functionality.
"""
from pathlib import Path

from nutree.tree import Node, Tree


class FileSystemEntry:
    def __init__(self, name, is_dir, size, mdate):
        self.name = name
        self.is_dir = is_dir
        self.size = int(size)
        self.mdate = float(mdate)

    def __repr__(self):
        if self.is_dir:
            return f"[{self.name}]"
        return f"{self.name!r}, {self.size:,} bytes"

    @staticmethod
    def serialize_mapper(node, data):
        """Callback for use with :meth:`~nutree.tree.Tree.save`."""
        inst = node.data
        if inst.is_dir:
            data.update({"n": inst.name, "d": True})
        else:
            data.update({"n": inst.name, "s": inst.size})
        return data

    @staticmethod
    def deserialize_mapper(parent, data):
        """Callback for use with :meth:`~nutree.tree.Tree.load`."""
        v = data["v"]
        if "d" in v:
            return FileSystemEntry(v["n"], True, 0)
        return FileSystemEntry(v["n"], False, v["s"])


def load_tree_from_fs(path: str) -> Tree:
    """Scan a filesystem folder and store as tree."""
    path = Path(path)
    tree = Tree(path)

    def visit(node: Node, pth: Path):
        for c in pth.iterdir():
            if c.is_dir():
                o = FileSystemEntry(f"{c.name}", True, 0, 0)
                pn = node.add(o)
                if "." not in c.name:
                    # Skip system folders
                    visit(pn, c)
            elif c.is_file():
                stat = c.stat()
                o = FileSystemEntry(c.name, False, stat.st_size, stat.st_mtime)
                node.add(o)

    visit(tree._root, path)
    return tree
