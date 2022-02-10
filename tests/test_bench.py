# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
# from nutree import AmbigousMatchError, IterMethod, Node, Tree
import sys

import pytest

from nutree import IterMethod, Node

from . import fixture

benchmark = pytest.mark.skipif(
    "--benchmarks" not in sys.argv,
    reason="`--benchmarks` not set",
)


@benchmark
class TestBenchmarks:
    def test_index(self, capsys):
        """ """

        results = ["Benchmark results"]
        tree = fixture.create_tree()

        results.append(
            fixture.run_timings(
                "access tree[key]",
                """\
            _ = tree["a1"]
        """,
                globals=locals(),
                time_unit="nsec",
            )
        )

        results.append(
            fixture.run_timings(
                "tree.find()",
                """\
            _ = tree.find("a1")
        """,
                globals=locals(),
            )
        )

        results.append(
            fixture.run_timings(
                "tree.find_all()",
                """\
            _ = tree.find_all("a1")
        """,
                globals=locals(),
            )
        )

        with capsys.disabled():
            print("\n  - ".join(results))

    def test_properties(self, capsys):
        """ """

        results = ["Benchmark results"]
        tree = fixture.create_tree()
        node = tree.first_child

        results.append(
            fixture.run_timings(
                "access node.data (property)",
                """\
            _ = node.data
        """,
                globals=locals(),
            )
        )

        results.append(
            fixture.run_timings(
                "access node._data (attribute)",
                """\
            _ = node._data
        """,
                globals=locals(),
            )
        )

        with capsys.disabled():
            print("\n  - ".join(results))

    def test_iter(self, capsys):
        """ """

        results = ["Benchmark results"]
        tree = fixture.create_tree()
        node = tree.first_child

        results.append(
            fixture.run_timings(
                "for _ in tree: ...",
                """\
            for _ in tree: pass
        """,
                globals=locals(),
            )
        )

        results.append(
            fixture.run_timings(
                "for _ in tree.iterator(): ...",
                """\
            for _ in tree.iterator(): pass
        """,
                globals=locals(),
            )
        )

        ORDER = IterMethod.LEVEL_ORDER
        results.append(
            fixture.run_timings(
                f"for _ in tree.iterator({ORDER}): ...",
                """\
            for _ in tree.iterator(ORDER): pass
        """,
                globals=locals(),
            )
        )

        ORDER = IterMethod.RANDOM_ORDER
        results.append(
            fixture.run_timings(
                f"for _ in tree.iterator({ORDER}): ...",
                """\
            for _ in tree.iterator(ORDER): pass
        """,
                globals=locals(),
            )
        )

        ORDER = IterMethod.UNORDERED
        results.append(
            fixture.run_timings(
                f"for _ in tree.iterator({ORDER}): ...",
                """\
            for _ in tree.iterator(ORDER): pass
        """,
                globals=locals(),
            )
        )

        results.append(
            fixture.run_timings(
                "tree.visit(lambda node, memo: None)",
                """\
            tree.visit(lambda node, memo: None)
        """,
                globals=locals(),
            )
        )

        with capsys.disabled():
            print("\n  - ".join(results))


@benchmark
class TestMemory:
    def test_node_size(self, capsys):
        """ """
        from pympler.asizeof import asized, asizeof

        results = ["Memory results"]
        tree = fixture.generate_tree([10, 9])
        assert len(tree) == 100
        # tree.print()

        node_count = len(tree)
        tree_size = asizeof(tree)
        node_size = tree_size / node_count

        results.append(
            f"Tree 10x9: {node_count:,} nodes, {tree_size:,} bytes, node-size: {node_size:.1f} bytes"
        )

        print(asized(tree.first_child, detail=1).format())

        tree = fixture.generate_tree([100, 100, 99])
        assert len(tree) == 1000100

        node_count = len(tree)
        tree_size = asizeof(tree)
        node_size = tree_size / node_count

        results.append(
            f"Tree 100x100x99: {node_count:,} nodes, {tree_size:,} bytes, node-size: {node_size:.1f} bytes"
        )
        with capsys.disabled():
            print("\n  - ".join(results))

    # def test_tree_mem(self, capsys):
    #     """ """
    #     from pympler import tracker

    #     results = ["Memory results"]

    #     tr = tracker.SummaryTracker()
    #     tr.print_diff()
    #     tree = fixture.generate_tree([10, 5])
    #     tr.print_diff()

    #     tree.clear()
    #     tr.print_diff()

    #     tree = None
    #     tr.print_diff()

    #     assert len(tree) == 60

    #     with capsys.disabled():
    #         print("\n  - ".join(results))

    # def test_tree_mem_2(self, capsys):
    #     """ """
    #     from pympler import classtracker

    #     results = ["Memory results"]

    #     tr = classtracker.ClassTracker()
    #     tr.track_class(Node)
    #     tr.create_snapshot()

    #     tree = fixture.generate_tree([10, 5])

    #     tr.create_snapshot()
    #     tr.stats.print_summary()

    #     tree.clear()

    #     tree = None

    #     assert len(tree) == 60

    #     with capsys.disabled():
    #         print("\n  - ".join(results))
