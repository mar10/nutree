# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt and contributors; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
# from nutree import AmbigousMatchError, IterMethod, Node, Tree
import sys

import pytest

from nutree.common import IterMethod

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
