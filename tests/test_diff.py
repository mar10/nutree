# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from nutree import diff_node_formatter

from . import fixture


class TestDiff:
    def test_diff(self):

        tree_0 = fixture.create_tree(name="T0", print=True)

        tree_1 = fixture.create_tree(name="T1", print=False)

        tree_1["a2"].add("a21")
        tree_1["a11"].remove()
        tree_1.add_child("C")
        tree_1["b1"].move_to(tree_1["C"])
        tree_1.print()

        tree_2 = tree_0.diff(tree_1)

        tree_2.print(repr=diff_node_formatter)

        assert fixture.check_content(
            tree_2,
            """
            Tree<"diff('T0', 'T1')">
            ├── A
            │   ├── a1
            │   │   ├── a11 - [Removed]
            │   │   ╰── a12
            │   ╰── a2
            │       ╰── a21 - [Added]
            ├── B
            │   ╰── b1 - [Moved away]
            ╰── C - [Added]
                ╰── b1 - [Moved here]
                    ╰── b11
            """,
            repr=diff_node_formatter,
        )

        tree_2 = tree_0.diff(tree_1, ordered=True)

        assert fixture.check_content(
            tree_2,
            """
            Tree<"diff('T0', 'T1')">
            ├── A
            │   ├── a1 - [Renumbered]
            │   │   ├── a11 - [Removed]
            │   │   ╰── a12 - [Order -1]
            │   ╰── a2
            │       ╰── a21 - [Added]
            ├── B
            │   ╰── b1 - [Moved away]
            ╰── C - [Added]
                ╰── b1 - [Moved here]
                    ╰── b11
            """,
            repr=diff_node_formatter,
        )

        tree_2 = tree_0.diff(tree_1, reduce=True)

        assert fixture.check_content(
            tree_2,
            """
            Tree<"diff('T0', 'T1')">
            ├── A
            │   ├── a1
            │   │   ╰── a11 - [Removed]
            │   ╰── a2
            │       ╰── a21 - [Added]
            ├── B
            │   ╰── b1 - [Moved away]
            ╰── C - [Added]
                ╰── b1 - [Moved here]
            """,
            repr=diff_node_formatter,
        )
