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
    def test_bench_index(self, benchman, capsys):
        """ """
        tree = fixture.create_tree_simple(print=False)
        size = len(tree)

        benchman.run_timings(
            "search",
            variant="by index",
            stmt="""\
                _ = tree["a1"]
            """,
            sample_size=size,
            globals=locals(),
        )
        benchman.run_timings(
            "search",
            variant="find() ",
            stmt="""\
                _ = tree.find("a1")
            """,
            sample_size=size,
            globals=locals(),
        )
        benchman.run_timings(
            "search s",
            variant="find_all() ",
            stmt="""\
                _ = tree.find_all("a1")
            """,
            sample_size=size,
            globals=locals(),
        )

        # with capsys.disabled():
        #     print(f"\n{benchman}")
        #     benchman.print_results()

    def test_bench_properties(self, benchman, capsys):
        """ """
        tree = fixture.create_tree_simple()
        node = tree.first_child()

        benchman.run_timings(
            "access node.data",
            variant="node.data (property)",
            stmt="""\
                _ = node.data
            """,
            globals=locals(),
        )

        benchman.run_timings(
            "access node.data",
            variant="node._data (attr)",
            stmt="""\
                _ = node._data
            """,
            globals=locals(),
        )

        # with capsys.disabled():
        #     print(f"\n{benchman}")
        #     benchman.print_results()

    def test_bench_iter(self, benchman, capsys):
        """ """
        tree = fixture.create_tree_simple()
        node = tree.first_child()
        size = len(tree)

        benchman.run_timings(
            "iterate",
            variant="for _ in tree: ...",
            stmt="""\
                for _ in tree: pass
            """,
            sample_size=size,
            globals=locals(),
        )

        benchman.run_timings(
            "iterate",
            variant="for _ in tree.iterator(): ...",
            stmt="""\
                for _ in tree.iterator(): pass
            """,
            sample_size=size,
            globals=locals(),
        )

        ORDER = IterMethod.LEVEL_ORDER
        benchman.run_timings(
            "iterate",
            variant=f"for _ in tree.iterator({ORDER}): ...",
            stmt="""\
                for _ in tree.iterator(ORDER): pass
            """,
            sample_size=size,
            globals=locals(),
        )

        ORDER = IterMethod.RANDOM_ORDER
        benchman.run_timings(
            "iterate",
            variant=f"for _ in tree.iterator({ORDER}): ...",
            stmt="""\
                for _ in tree.iterator(ORDER): pass
            """,
            sample_size=size,
            globals=locals(),
        )

        ORDER = IterMethod.UNORDERED
        benchman.run_timings(
            "iterate",
            variant=f"for _ in tree.iterator({ORDER}): ...",
            stmt="""\
                for _ in tree.iterator(ORDER): pass
            """,
            sample_size=size,
            globals=locals(),
        )

        benchman.run_timings(
            "iterate",
            variant="tree.visit(lambda node, memo: None)",
            stmt="""\
                tree.visit(lambda node, memo: None)
            """,
            sample_size=size,
            globals=locals(),
        )

        # with capsys.disabled():
        #     print(f"\n{benchman}")
        #     benchman.print_results()


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

    def test_bench_serialize(self, benchman, capsys):
        import zipfile  # noqa: F401

        directory = Path("~").expanduser()
        # with WritableTempFile("w", suffix=".gz") as temp_file:

        tree = fixture.generate_tree([10, 100, 100])
        # size = len(tree)

        path = directory / "test.json"
        benchman.run_timings(
            "serialize",
            variant=f"tree.save({path}, compression=False, nodes={len(tree):,})",
            stmt=f"""\
                tree.save("{path}", compression=False)
            """,
            repeat=1,
            iterations=1,
            globals=locals(),
        )

        benchman.run_timings(
            "serialize",
            variant=f"tree.load({path}, nodes={len(tree):,})",
            stmt=f"""\
                tree.load("{path}")
            """,
            repeat=1,
            iterations=1,
            globals=locals(),
        )

        # --- ZIP
        path = directory / "test.zip"
        benchman.run_timings(
            "serialize",
            variant=f"tree.save({path}, compression=ZIP, nodes={len(tree):,})",
            stmt=f"""\
                tree.save("{path}", compression=zipfile.ZIP_DEFLATED)
            """,
            repeat=1,
            iterations=1,
            globals=locals(),
        )

        benchman.run_timings(
            "serialize",
            variant=f"tree.load({path}, nodes={len(tree):,})",
            stmt=f"""\
                tree.load("{path}")
            """,
            repeat=1,
            iterations=1,
            globals=locals(),
        )

        # --- ZIP
        path = directory / "test.bz2"
        benchman.run_timings(
            "serialize",
            variant=f"tree.save({path}, compression=ZIP, nodes={len(tree):,})",
            stmt=f"""\
                tree.save("{path}", compression=zipfile.ZIP_BZIP2)
            """,
            repeat=1,
            iterations=1,
            globals=locals(),
        )

        benchman.run_timings(
            "serialize",
            variant=f"tree.load({path}, nodes={len(tree):,})",
            stmt=f"""\
                tree.load("{path}")
            """,
            repeat=1,
            iterations=1,
            globals=locals(),
        )

        # --- ZIP
        path = directory / "test.lzma"
        benchman.run_timings(
            "serialize",
            variant=f"tree.save({path}, compression=LZMA, nodes={len(tree):,})",
            stmt=f"""\
                tree.save("{path}", compression=zipfile.ZIP_LZMA)
            """,
            repeat=1,
            iterations=1,
            globals=locals(),
        )

        benchman.run_timings(
            "serialize",
            variant=f"tree.load({path}, nodes={len(tree):,})",
            stmt=f"""\
                tree.load("{path}")
            """,
            repeat=1,
            iterations=1,
            globals=locals(),
        )

        # with capsys.disabled():
        #     print(f"\n{benchman}")
        #     benchman.print_results()


@benchmark
class TestMemory:
    def test_bench_node_size(self, benchman, capsys):
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
            print(f"\n{benchman}")
            benchman.print_results()

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
