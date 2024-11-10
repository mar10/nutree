# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found
# ruff: noqa: E501 Line too long

import sys

import pytest

# from tests import benchman as unused  # noqa: F401
from . import fixture

benchmark = pytest.mark.skipif(
    "--benchmarks" not in sys.argv,
    reason="`--benchmarks` not set",
)


# @benchmark
class TestBenchManager:
    @pytest.mark.xfail(reason="just testing")
    def test_bench_index(self, capsys, benchman):
        """ """
        tree = fixture.create_tree_simple(print=False)

        benchman.run_timings(
            "access node",
            variant="by index",
            stmt="""\
                _ = tree["a1"]
            """,
            globals=locals(),
        )
        benchman.run_timings(
            "access node",
            variant="find() ",
            stmt="""\
                _ = tree.find("a1")
            """,
            globals=locals(),
        )
        benchman.run_timings(
            "access node",
            variant="find_all() ",
            stmt="""\
                _ = tree.find_all("a1")
            """,
            globals=locals(),
        )

        with capsys.disabled():
            print(f"\n{benchman}")
            benchman.print_results()

        raise
