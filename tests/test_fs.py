# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found
# pyright: reportRedeclaration=false
# pyright: reportOptionalMemberAccess=false

import os
import shutil
from pathlib import Path

import pytest
from nutree.fs import FileSystemTree, load_tree_from_fs

from . import fixture


class TestFS:
    @pytest.mark.skipif(os.name == "nt", reason="windows has different eol size")
    def test_fs_linux(self):
        path = Path(__file__).parent / "fixtures"

        # We check for unix line endings/file sizes (as used on travis)
        tree = load_tree_from_fs(path)
        assert fixture.check_content(
            tree,
            """
            FileSystemTree<*>
            ├── 'file_1.txt', 13 bytes, 2022-04-14 21:35:21
            ╰── [folder_1]
                ╰── 'file_1_1.txt', 15 bytes, 2022-04-14 21:35:21
            """,
        )

        tree = load_tree_from_fs(path, sort=False)
        assert "[folder_1]" in fixture.canonical_repr(tree)

    @pytest.mark.skipif(os.name != "nt", reason="windows has different eol size")
    def test_fs_windows(self):
        path = Path(__file__).parent / "fixtures"
        # Cheap test only,
        tree = load_tree_from_fs(path)
        assert "[folder_1]" in fixture.canonical_repr(tree)

        tree = load_tree_from_fs(path, sort=False)
        assert "[folder_1]" in fixture.canonical_repr(tree)

    def test_fs_serialize(self):
        KEEP_FILES = True
        path = Path(__file__).parent / "fixtures"
        # Cheap test only,
        tree = load_tree_from_fs(path)

        with fixture.WritableTempFile("r+t", suffix=".json") as temp_file:
            tree.save(
                temp_file.name,
                mapper=tree.serialize_mapper,
            )

            if KEEP_FILES:  # save to tests/temp/...
                shutil.copy(
                    temp_file.name,
                    Path(__file__).parent / "temp/test_serialize_fs.json",
                )

            tree_2 = FileSystemTree.load(temp_file.name, mapper=tree.deserialize_mapper)

        assert fixture.trees_equal(tree, tree_2, ignore_tree_name=True)
