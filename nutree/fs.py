# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Methods and classes to support file system related functionality.
"""

from operator import attrgetter, itemgetter
from pathlib import Path
from typing import Optional, Union

from nutree.tree import Node, Tree


class FileSystemEntry:
    def __init__(
        self,
        name: str,
        *,
        is_dir: bool = False,
        size: Optional[int] = None,
        mdate: Optional[float] = None,
    ):
        self.name = name
        self.is_dir = is_dir
        if is_dir:
            assert size is None
            size = 0
        else:
            assert size is not None
        self.size = int(size)
        self.mdate = float(mdate) if mdate is not None else None

    def __repr__(self):
        if self.is_dir:
            return f"[{self.name}]"
        return f"{self.name!r}, {self.size:,} bytes"


class FileSystemTree(Tree):
    def serialize_mapper(self, node: Node, data: dict):
        """Callback for use with :meth:`~nutree.tree.Tree.save`."""
        inst = node.data
        if inst.is_dir:
            data.update({"n": inst.name, "d": True})
        else:
            data.update({"n": inst.name, "s": inst.size})
        return data

    @staticmethod
    def deserialize_mapper(parent: Node, data: dict):
        """Callback for use with :meth:`~nutree.tree.Tree.load`."""
        v = data["v"]
        if "d" in v:
            return FileSystemEntry(v["n"], is_dir=True, size=0)
        return FileSystemEntry(v["n"], is_dir=False, size=v["s"])


def load_tree_from_fs(path: Union[str, Path], *, sort: bool = True) -> Tree:
    """Scan a filesystem folder and store as tree.

    Args:
        sort: Pass true to sort alphabetical and files before directories.
        Especially useful when comparing unit test fixtures.
    """
    path = Path(path)
    tree = FileSystemTree(str(path))

    def visit(node: Node, pth: Path):
        if sort:
            dirs = []
            files = []
            for c in pth.iterdir():
                if c.is_dir():
                    o = FileSystemEntry(f"{c.name}", is_dir=True)
                    dirs.append((c, o))
                elif c.is_file():
                    stat = c.stat()
                    o = FileSystemEntry(c.name, size=stat.st_size, mdate=stat.st_mtime)
                    files.append(o)
            # Files first, sorted by name
            for o in sorted(files, key=attrgetter("name")):
                node.add(o)
            # Followed by dirs, sorted by path
            for c, o in sorted(dirs, key=itemgetter(0)):
                pn = node.add(o)
                visit(pn, c)
            return

        for c in pth.iterdir():
            if c.is_dir():
                o = FileSystemEntry(f"{c.name}", is_dir=True)
                pn = node.add(o)
                visit(pn, c)
            elif c.is_file():
                stat = c.stat()
                o = FileSystemEntry(c.name, size=stat.st_size, mdate=stat.st_mtime)
                node.add(o)

    visit(tree._root, path)
    return tree
