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

        tree_2 = tree_0.diff(tree_1, compare=False)

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
        tree_1 = tree_0.copy(name="T1")

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

        newman = fixture.Person("Newman", age=67, guid="{567-567}")

        bob_node.remove()
        alice_node.move_to(mkt_node, before=True)
        dev_node.add(newman, data_id=newman.guid)
        # tree_1 contains nodes thar reference the same data objects as tree_0
        # In order to simulate a change, we need to instantiate a new Person object
        # and patch the node.
        dave_0 = dave_node.data
        dave_1 = fixture.Person(dave_0.name, guid=dave_0.guid, age=55)
        dave_node._data = dave_1

        alice_0 = alice_node.data
        alice_1 = fixture.Person("Alicia", guid=alice_0.guid, age=23)
        alice_node._data = alice_1

        tree_1.print(repr="{node}")

        def compare_cb(node_0, node_1, node_2):
            if node_0.data.name != node_1.data.name:
                return True
            if getattr(node_0.data, "age", None) != getattr(node_1.data, "age", None):
                return True
            return False

        tree_2 = tree_0.diff(tree_1, compare=compare_cb)

        tree_2.print(repr=diff_node_formatter)

        assert fixture.check_content(
            tree_2,
            """
            Tree<*>
            ├── Department<Development>
            │   ├── Person<Newman, 67> - [Added]
            │   ├── Person<Alice, 23> - [Moved away], [Modified]
            │   ╰── Person<Bob, 32> - [Removed]
            ╰── Department<Marketing>
                ├── Person<Alicia, 23> - [Moved here], [Modified]
                ├── Person<Charleen, 43>
                ╰── Person<Dave, 55> - [Modified]
            """,
            repr=diff_node_formatter,
        )

        tree_2 = tree_0.diff(tree_1, ordered=True)

        assert fixture.check_content(
            tree_2,
            """
            Tree<*>
            ├── Department<Development>
            │   ├── Person<Newman, 67> - [Added]
            │   ├── Person<Alice, 23> - [Moved away], [Modified]
            │   ╰── Person<Bob, 32> - [Removed]
            ╰── Department<Marketing> - [Renumbered]
                ├── Person<Alicia, 23> - [Moved here], [Modified]
                ├── Person<Charleen, 43> - [Order +1]
                ╰── Person<Dave, 55> - [Modified], [Order +1]
            """,
            repr=diff_node_formatter,
        )

        tree_2 = tree_0.diff(tree_1, reduce=True)

        assert fixture.check_content(
            tree_2,
            """
            Tree<*>
            ├── Department<Development>
            │   ├── Person<Newman, 67> - [Added]
            │   ├── Person<Alice, 23> - [Moved away], [Modified]
            │   ╰── Person<Bob, 32> - [Removed]
            ╰── Department<Marketing>
                ├── Person<Alicia, 23> - [Moved here], [Modified]
                ╰── Person<Dave, 55> - [Modified]
            """,
            repr=diff_node_formatter,
        )
