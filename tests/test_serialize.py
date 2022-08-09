# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import json
import tempfile

from nutree import Node, Tree
from nutree.diff import DiffClassification, diff_node_formatter

from . import fixture


class TestSerialize:
    def setup_method(self):
        self.tree = None  # Tree("fixture")

    def teardown_method(self):
        self.tree = None

    def test_serialize_dict(self):
        tree = fixture.create_tree()

        with tempfile.TemporaryFile("r+t") as fp:
            # Serialize
            json.dump(tree.to_dict(), fp)
            # Deserialize
            fp.seek(0)
            obj = json.load(fp)
            tree_2 = Tree.from_dict(obj)

        assert fixture.trees_equal(tree, tree_2)

        assert tree.first_child is not tree_2.first_child
        assert tree.first_child == tree_2.first_child
        assert tree.count == tree_2.count

        assert tree._self_check()
        assert tree_2._self_check()

    def test_serialize_list(self):
        tree = fixture.create_tree()

        b = tree["B"]
        a11 = tree["a11"]
        clone = b.prepend_child(a11)
        assert clone.is_clone()

        with tempfile.TemporaryFile("r+t") as fp:
            # Serialize
            tree.save(fp)
            # Deserialize
            fp.seek(0)
            tree_2 = Tree.load(fp)

        assert fixture.trees_equal(tree, tree_2)

        # print(tree.format(repr="{node}"))
        # print(tree_2.format(repr="{node}"))

        assert tree.count == tree_2.count
        assert tree.first_child is not tree_2.first_child
        assert tree.first_child == tree_2.first_child

        a11 = tree_2.find("a11")
        assert a11.is_clone(), "Restored clone"
        assert len(tree_2.find_all("a11")) == 2

        assert tree._self_check()
        assert tree_2._self_check()

    def test_serialize_list_obj(self):
        """Save/load an object tree with clones.

        Tree<'2009255653136'>
        ├── Node<'Department<Development>', data_id=125578508105>
        │   ├── Node<'Person<Alice, 23>', data_id={123-456}>
        │   ├── Node<'Person<Bob, 32>', data_id={234-456}>
        │   ╰── Node<'Person<Charleen, 43>', data_id={345-456}>
        ╰── Node<'Department<Marketing>', data_id=125578508063>
            ├── Node<'Person<Charleen, 43>', data_id={345-456}>
            ╰── Node<'Person<Dave, 54>', data_id={456-456}>
        """

        def _calc_id(tree, data):
            if isinstance(data, fixture.Person):
                return data.guid
            return hash(data)

        # Use a tree
        tree = Tree(calc_data_id=_calc_id)
        fixture.create_tree(style="objects", clones=True, tree=tree)

        # print(tree._nodes_by_data_id)
        assert tree["{123-456}"].data.name == "Alice"
        alice = tree["{123-456}"].data
        assert tree[alice].data is alice

        def serialize_mapper(node, data):
            if isinstance(node.data, fixture.Department):
                data["type"] = "dept"
                data["name"] = node.data.name
            elif isinstance(node.data, fixture.Person):
                data["type"] = "person"
                data["name"] = node.data.name
                data["age"] = node.data.age
                data["guid"] = node.data.guid
            return data

        def deserialize_mapper(parent, data):
            node_type = data["type"]
            if node_type == "person":
                data = fixture.Person(
                    name=data["name"], age=data["age"], guid=data["guid"]
                )
            elif node_type == "dept":
                data = fixture.Department(name=data["name"])
            return data

        with tempfile.TemporaryFile("r+t") as fp:
            # Serialize
            tree.save(fp, mapper=serialize_mapper)
            # print output
            fp.seek(0)
            print(fp.read())
            # Deserialize
            fp.seek(0)
            tree_2 = Tree.load(fp, mapper=deserialize_mapper)

        assert fixture.trees_equal(tree, tree_2)

        assert tree.count == tree_2.count
        assert tree.first_child is not tree_2.first_child

        # TODO: also make a test-case, where the mapper returns a data_id,
        #       so that `tree.first_child == tree_2.first_child`
        # assert tree.first_child == tree_2.first_child

        alice_2 = tree_2.find(match=".*Alice.*")
        assert alice_2.data.guid == "{123-456}"

        charleen_2 = tree_2.find(match=".*Charleen.*")
        assert charleen_2.is_clone(), "Restored clone"
        # assert len(tree_2.find_all("Charleen")) == 2

        assert tree._self_check()
        assert tree_2._self_check()


class TestDot:
    def test_serialize_dot(self):
        """Save/load as  object tree with clones."""

        tree = fixture.create_tree(style="simple", clones=True, name="Root")

        # Avoid "Permission denied error" on Windows:
        # with tempfile.NamedTemporaryFile("w", suffix=".gv") as path:
        with fixture.WritableTempFile("w", suffix=".gv") as temp_file:
            tree.to_dotfile(temp_file.name)

        # with tempfile.NamedTemporaryFile("w", suffix=".png") as path:
        #     tree.to_dotfile(
        #         path.name,
        #         # "/Users/martin/Downloads/tree.png",
        #         format="png",
        #         add_root=False,
        #         # unique_nodes=False,
        #     )
        #     assert False

        res = [line for line in tree.to_dot()]
        assert len(res) == 25
        res = "\n".join(res)
        print(res)
        assert '__root__ [label="Root" shape="box"]' in res
        assert "__root__ -> " in res
        # assert False

    def test_serialize_dot_2(self):
        tree_0 = fixture.create_tree(name="T0", print=True)

        tree_1 = fixture.create_tree(name="T1", print=False)

        tree_1["a2"].add("a21")
        tree_1["a11"].remove()
        tree_1.add_child("C")
        tree_1["b1"].move(tree_1["C"])
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
