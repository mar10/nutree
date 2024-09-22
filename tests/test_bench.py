# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found
# ruff: noqa: E501 Line too long

import sys
from pathlib import Path

import pytest
from nutree import IterMethod

from . import fixture

benchmark = pytest.mark.skipif(
    "--benchmarks" not in sys.argv,
    reason="`--benchmarks` not set",
)


@benchmark
class TestBenchmarks:
    def test_bench_index(self, capsys):
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

    def test_bench_properties(self, capsys):
        """ """

        results = ["Benchmark results"]
        tree = fixture.create_tree()
        node = tree.first_child()

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

    def test_bench_iter(self, capsys):
        """ """

        results = ["Benchmark results"]
        tree = fixture.create_tree()
        node = tree.first_child()

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
class TestCompress:
    """
    Tree: ~100,000 nodes, 3 levels

    Compression            | Size (Bytes) | Save (sec) | Load (sec)
    -----------------------+--------------+------------+-----------
    Uncompressed ('.json') |    2.000.733 |       1.24 |    0.37
    ZIP_DEFLATED ('.zip')  |      196.934 |       1.29 |    0.37
    ZIP_BZIP2 ('.bz2')     |      103.519 |       1.32 |    0.39
    ZIP_LZMA ('.lzma')     |       44.347 |       2.13 |    0.38
    """

    def test_bench_serialize(self, capsys):
        import zipfile  # noqa: F401

        results = ["Benchmark results"]
        directory = Path("~").expanduser()
        # with WritableTempFile("w", suffix=".gz") as temp_file:

        tree = fixture.generate_tree([10, 100, 100])

        path = directory / "test.json"
        results.append(
            fixture.run_timings(
                f"tree.save({path}, compression=False, nodes={len(tree):,})",
                f"""\
                tree.save("{path}", compression=False)
                """,
                repeat=1,
                number=1,
                globals=locals(),
            )
        )
        results.append(
            fixture.run_timings(
                f"tree.load({path}, nodes={len(tree):,})",
                f"""\
                tree.load("{path}")
                """,
                repeat=1,
                number=1,
                globals=locals(),
            )
        )
        # --- ZIP
        path = directory / "test.zip"
        results.append(
            fixture.run_timings(
                f"tree.save({path}, compression=ZIP, nodes={len(tree):,})",
                f"""\
                tree.save("{path}", compression=zipfile.ZIP_DEFLATED)
                """,
                repeat=1,
                number=1,
                globals=locals(),
            )
        )
        results.append(
            fixture.run_timings(
                f"tree.load({path}, nodes={len(tree):,})",
                f"""\
                tree.load("{path}")
                """,
                repeat=1,
                number=1,
                globals=locals(),
            )
        )
        # --- ZIP
        path = directory / "test.bz2"
        results.append(
            fixture.run_timings(
                f"tree.save({path}, compression=ZIP, nodes={len(tree):,})",
                f"""\
                tree.save("{path}", compression=zipfile.ZIP_BZIP2)
                """,
                repeat=1,
                number=1,
                globals=locals(),
            )
        )
        results.append(
            fixture.run_timings(
                f"tree.load({path}, nodes={len(tree):,})",
                f"""\
                tree.load("{path}")
                """,
                repeat=1,
                number=1,
                globals=locals(),
            )
        )
        # --- ZIP
        path = directory / "test.lzma"
        results.append(
            fixture.run_timings(
                f"tree.save({path}, compression=LZMA, nodes={len(tree):,})",
                f"""\
                tree.save("{path}", compression=zipfile.ZIP_LZMA)
                """,
                repeat=1,
                number=1,
                globals=locals(),
            )
        )
        results.append(
            fixture.run_timings(
                f"tree.load({path}, nodes={len(tree):,})",
                f"""\
                tree.load("{path}")
                """,
                repeat=1,
                number=1,
                globals=locals(),
            )
        )

        with capsys.disabled():
            print("\n  - ".join(results))


@benchmark
class TestMemory:
    def test_bench_node_size(self, capsys):
        """ """

        try:
            from pympler.asizeof import asized, asizeof
        except ImportError:
            raise pytest.skip("pympler not installed") from None

        results = ["Memory results"]
        tree = fixture.generate_tree([10, 9])
        assert len(tree) == 100
        # tree.print()

        node_count = len(tree)
        tree_size = asizeof(tree)
        node_size = tree_size / node_count

        results.append(
            f"Tree 10x9: {node_count:,} nodes, {tree_size:,} bytes, "
            f"node-size: {node_size:.1f} bytes"
        )

        print(asized(tree.first_child(), detail=1).format())

        tree = fixture.generate_tree([100, 100, 99])
        assert len(tree) == 1000100

        node_count = len(tree)
        tree_size = asizeof(tree)
        node_size = tree_size / node_count

        results.append(
            f"Tree 100x100x99: {node_count:,} nodes, {tree_size:,} bytes, "
            f"node-size: {node_size:.1f} bytes"
        )
        with capsys.disabled():
            print("\n  - ".join(results))

    # def test_bench_tree_mem(self, capsys):
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

    # def test_bench_tree_mem_2(self, capsys):
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
