# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
Run this to generate sample images and files.
"""
# pragma: no cover
# ruff: noqa: T201, T203 `print` found

from __future__ import annotations

from pathlib import Path

from nutree.diff import DiffClassification, diff_node_formatter
from nutree.node import Node

from tests import fixture


def write_str_diff_png():
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
            # attr_def["label"] = "X"

        # # attr_def["label"] = "\E"
        # # attr_def["label"] = "child of"
        # attr_def["penwidth"] = 1.0
        # # attr_def["weight"] = 1.0

    tree_2.to_dotfile(
        Path(__file__).parent / "temp/tree_diff.png",
        format="png",
        # add_root=False,
        # unique_nodes=False,
        graph_attrs={"label": "Diff T0/T1"},
        node_attrs={"style": "filled", "fillcolor": "#e0e0e0"},
        edge_attrs={},
        node_mapper=node_mapper,
        edge_mapper=edge_mapper,
    )


def write_object_diff_png():
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

    tree_2 = tree_0.diff(tree_1, reduce=False)

    tree_2.print(repr=diff_node_formatter)

    UNIQUE_NODES = True

    def node_mapper(node: Node, attr_def: dict):
        # https://graphviz.org/docs/nodes/

        dc = node.get_meta("dc")
        if isinstance(node.data, fixture.OrgaUnit):
            attr_def["label"] = str(node.data)

        if (
            UNIQUE_NODES
            and node.get_meta("dc_modified")
            and dc == DiffClassification.MOVED_TO
        ):
            # We only display the first node that the iterator hits.
            # If it is modified, we want to make sure, we display the label of
            # the new status
            for n in node.get_clones():
                if n.get_meta("dc") == DiffClassification.MOVED_HERE:
                    attr_def["label"] = str(n.data)

        if isinstance(node.data, fixture.Department):
            attr_def["shape"] = "box"

        if dc == DiffClassification.ADDED:
            attr_def["color"] = "#00c000"
            attr_def["fillcolor"] = "#d0f8d0"
        elif dc == DiffClassification.REMOVED:
            attr_def["color"] = "#c00000"
            attr_def["fillcolor"] = "#f8d0d0"

        if node.get_meta("dc_modified"):
            attr_def["fillcolor"] = "#fff0d0"  # "gold" "#FFD700"

    def edge_mapper(node: Node, attr_def: dict):
        # https://renenyffenegger.ch/notes/tools/Graphviz/examples/index
        # https://graphviz.org/docs/edges
        dc = node.get_meta("dc")
        if dc in (DiffClassification.ADDED, DiffClassification.MOVED_HERE):
            attr_def["color"] = "#00C000"
        elif dc in (DiffClassification.REMOVED, DiffClassification.MOVED_TO):
            attr_def["style"] = "dashed"
            attr_def["color"] = "#C00000"
            # attr_def["label"] = "X"

        if node.get_meta("dc_modified"):
            attr_def["arrowhead"] = "diamond"

    tree_2.to_dotfile(
        Path(__file__).parent / "temp/tree_diff_obj.png",
        format="png",
        # add_root=False,
        unique_nodes=UNIQUE_NODES,
        graph_attrs={"label": "Diff T0/T1"},
        node_attrs={"style": "filled", "fillcolor": "#ffffff"},
        edge_attrs={},
        node_mapper=node_mapper,
        edge_mapper=edge_mapper,
    )


if __name__ == "__main__":
    write_object_diff_png()
