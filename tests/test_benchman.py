# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found
# ruff: noqa: E501 Line too long

import sys
from pathlib import Path

import pytest

from tests.benchman.benchman import BenchmarkManager

from . import fixture

benchmark = pytest.mark.skipif(
    "--benchmarks" not in sys.argv,
    reason="`--benchmarks` not set",
)


# @benchmark
class TestBenchManager:
    def test_bench_index(self, capsys):
        """ """
        bm = BenchmarkManager(
            project_name="nutree", project_root=Path(__file__).parent.parent
        )
        results = ["Benchmark results"]
        tree = fixture.create_tree_simple(print=False)

        bm.run_timings(
            "access node",
            """\
                _ = tree["a1"]
            """,
            globals=locals(),
            variant="by index",
        )
        bm.run_timings(
            "access node",
            """\
                _ = tree.find("a1")
            """,
            globals=locals(),
            variant="find() ",
        )
        bm.run_timings(
            "access node",
            """\
                _ = tree.find_all("a1")
            """,
            globals=locals(),
            variant="find_all() ",
        )

        with capsys.disabled():
            print(f"\n{bm}")
            bm.print_results()
            # print("\n  - ".join(results))
        raise
