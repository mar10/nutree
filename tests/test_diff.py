# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """

from nutree import diff_node_formatter

from . import fixture


class TestDiff:
    def test_diff(self):
        tree_0 = fixture.create_tree_simple(name="T0", print=True)

        tree_1 = fixture.create_tree_simple(name="T1", print=False)

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

    def test_diff_objects(self):
        tree_0 = fixture.create_tree_objects(name="T0", print=True)
        tree_1 = tree_0.copy()

        # Modify 2nd tree
        bob_node = tree_1.find(match=".*Bob.*")
        assert bob_node
        dave_node = tree_1.find(match=".*Dave.*")
        assert dave_node
        dev_node = tree_1.find(match=".*Development.*")
        assert dev_node
        mkt_node = tree_1.find(match=".*Marketing.*")
        assert mkt_node
        alice_node = tree_1.find(match=".*Alice.*")
        assert alice_node

        newman = fixture.Person("Newman", age=65)

        bob_node.remove()
        alice_node.move_to(mkt_node)
        dev_node.add(newman)
        dave_node.data.age = 55  # type: ignore
        tree_1.print()

        tree_2 = tree_0.diff(tree_1)

        tree_2.print(repr=diff_node_formatter)

        assert fixture.check_content(
            tree_2,
            """
            Tree<'2009255653136'>
            ├── Node<'Department<Development>', data_id=125578508105>
            │   ├── Node<'Person<Alice, 23>', data_id={123-456}>
            │   ├── Node<'Person<Bob, 32>', data_id={234-456}>
            │   ╰── Node<'Person<Charleen, 43>', data_id={345-456}>
            ╰── Node<'Department<Marketing>', data_id=125578508063>
                ├── Node<'Person<Charleen, 43>', data_id={345-456}>
                ╰── Node<'Person<Dave, 54>', data_id={456-456}>
            """,
            repr=diff_node_formatter,
        )
        raise
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
