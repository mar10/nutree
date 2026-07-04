# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """

from __future__ import annotations

# ruff: noqa: T201, T203 `print` found
from nutree import Tree

from . import fixture


class TestMiscUseCases:
    def test_create_from_dict(self):
        """https://stackoverflow.com/q/74650261"""
        input = {
            # child: parent
            "Marc": "Udo",
            "Lian": "Marc",
            "Dan": "Udo",
            "Jet": "Dan",
            "Joe": "Dan",
            "Alice": "Bob",
            "Bob": "Udo",
        }
        tree = Tree()
        for child, parent in input.items():
            if parent not in tree:
                tree.add(parent)
            tree[parent].add(child)

        assert fixture.check_content(
            tree,
            """
            Tree<*>
            ├── Udo
            │   ├── Marc
            │   │   ╰── Lian
            │   ├── Dan
            │   │   ├── Jet
            │   │   ╰── Joe
            │   ╰── Bob
            ╰── Bob
                ╰── Alice
            """,
        )
