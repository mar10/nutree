# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found

from pathlib import Path

from nutree import Node
from nutree.diff import DiffClassification, diff_node_formatter

from . import fixture


class TestDot:
    def test_dot_default(self):
        """Save/load as  object tree with clones."""

        tree = fixture.create_tree_simple(clones=True, name="Root")

        res = list(tree.to_dot())
        assert len(res) == 25
        res = "\n".join(res)
        print(res)
        assert 'digraph "Root" {' in res
        assert '"__root__" [label="Root" shape="box"]' in res
        assert '[label="b11"]' in res
        assert res.count('"__root__" -> ') == 2

    def test_dot_attrs(self):
        """Save/load as  object tree with clones."""

        tree = fixture.create_tree_simple(clones=True, name="Root")

        res = tree.to_dot(
            unique_nodes=False,
            graph_attrs={"label": "Simple Tree"},
            node_attrs={"shape": "box"},
            edge_attrs={"color": "red"},
        )
        res = list(res)
        assert len(res) == 31
        res = "\n".join(res)
        print(res)
        assert 'graph  [label="Simple Tree"]' in res
        assert 'node  [shape="box"]' in res
        assert 'edge  [color="red"]' in res
        assert '"0" [label="Root" shape="box"]' in res
        assert '"0" -> ' in res

    def test_dot_diff(self):
        tree_0 = fixture.create_tree_simple(name="T0", print=True)

        tree_1 = fixture.create_tree_simple(name="T1", print=False)

        tree_1["a2"].add("a21")
        tree_1["a11"].remove()
        tree_1.add_child("C")
        tree_1["b1"].move_to(tree_1["C"])
        tree_1.print()

        tree_2 = tree_0.diff(tree_1, reduce=False)

        tree_2.print(repr=diff_node_formatter)

        def node_mapper(node: Node, attr_def: dict):
            dc = node.get_meta("dc")
            if dc == DiffClassification.ADDED:
                attr_def["color"] = "#00c000"
            elif dc == DiffClassification.REMOVED:
                attr_def["color"] = "#c00000"

        def edge_mapper(node: Node, attr_def: dict):
            # https://renenyffenegger.ch/notes/tools/Graphviz/examples/index
            # https://graphs.grevian.org/reference
            # https://graphviz.org/doc/info/attrs.html
            dc = node.get_meta("dc")
            if dc in (DiffClassification.ADDED, DiffClassification.MOVED_HERE):
                attr_def["color"] = "#00C000"
            elif dc in (DiffClassification.REMOVED, DiffClassification.MOVED_TO):
                attr_def["style"] = "dashed"
                attr_def["color"] = "#C00000"
                attr_def["label"] = "X"
            # # attr_def["label"] = "\E"
            # # attr_def["label"] = "child of"
            # attr_def["color"] = "green"
            # # attr_def["style"] = "dashed"
            # attr_def["penwidth"] = 1.0
            # # attr_def["weight"] = 1.0

        # tree_2.to_dotfile(
        #     "/Users/martin/Downloads/tree_diff.png",
        #     format="png",
        #     # add_root=False,
        #     # unique_nodes=False,
        #     graph_attrs={"label": "Diff T0/T1"},
        #     node_attrs={"style": "filled", "fillcolor": "#e0e0e0"},
        #     edge_attrs={},
        #     node_mapper=node_mapper,
        #     edge_mapper=edge_mapper,
        # )
        # raise

        res = [
            line
            for line in tree_2.to_dot(
                graph_attrs={"label": "Diff T0/T1"},
                node_attrs={"style": "filled", "fillcolor": "#e0e0e0"},
                edge_attrs={},
                node_mapper=node_mapper,
                edge_mapper=edge_mapper,
            )
        ]
        res = "\n".join(res)
        print(res)
        assert 'node  [style="filled" fillcolor="#e0e0e0"]' in res
        assert '[label="C" color="#00c000"]' in res

    def test_serialize_dot(self):
        """Save/load as  object tree with clones."""

        tree = fixture.create_tree_simple(clones=True, name="Root")

        with fixture.WritableTempFile("w", suffix=".gv") as temp_file:
            tree.to_dotfile(temp_file.name)

            buffer = Path(temp_file.name).read_text()

        # print(buffer)
        assert '"__root__" [label="Root" shape="box"]' in buffer
        assert '"__root__" -> ' in buffer

    def test_serialize_png(self):
        """Save/load as  object tree with clones."""

        tree = fixture.create_tree_simple(clones=True, name="Root")

        with fixture.WritableTempFile("w", suffix=".gv") as temp_file:
            tree.to_dotfile(temp_file.name, format="png")

            target_path = Path(temp_file.name).with_suffix(".png")

        assert target_path.exists()
