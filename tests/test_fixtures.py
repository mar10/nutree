# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found
# pyright: reportRedeclaration=false
# pyright: reportOptionalMemberAccess=false

from . import fixture


class TestBasics:
    def test_generate_tree(self):
        tree = fixture.generate_tree([3, 4, 2])
        tree.print()
        assert tree.count == 39
