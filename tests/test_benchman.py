# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found
# ruff: noqa: E501 Line too long

import sys

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
        bm = BenchmarkManager()
        results = ["Benchmark results"]
        tree = fixture.create_tree()

        bm.run_timings(
            "access tree[key]",
            """\
                _ = tree["a1"]
            """,
            globals=locals(),
            time_unit="nsec",
            variant="by index",
        )

        with capsys.disabled():
            print("\n  - ".join(results))
        raise
