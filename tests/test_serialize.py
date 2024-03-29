# (c) 2021-2023 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
# ruff: noqa: T201, T203 `print` found

import json
import pprint
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Tuple

import pytest

from nutree import Node, Tree
from nutree.common import FILE_FORMAT_VERSION
from nutree.diff import DiffClassification, diff_node_formatter
from nutree.typed_tree import ANY_KIND, TypedNode, TypedTree

from . import fixture


def _get_fp_result(fp, *, do_print=True, assert_len: int) -> Tuple[str, dict]:
    fp.seek(0)
    text = fp.read()
    data = json.loads(text)
    if do_print:
        print("text", text)
        pprint.pprint(data)
    if assert_len:
        generator_len = len(data["meta"]["$generator"])
        extra_len = generator_len - len("nutree/1.0.0")
        assert len(text) - extra_len == assert_len
    return text, data


class TestSerialize:
    def setup_method(self):
        self.tree = None  # Tree("fixture")

    def teardown_method(self):
        self.tree = None

    def test_serialize_plain_str(self):
        tree = fixture.create_tree()

        b = tree["B"]
        a11 = tree["a11"]
        clone = b.prepend_child(a11)
        assert clone.is_clone()

        with tempfile.TemporaryFile("r+t") as fp:
            # Serialize
            tree.save(fp, meta={"foo": "bar"})
            _text, _data = _get_fp_result(fp, assert_len=200)
            # Deserialize
            fp.seek(0)
            meta_2 = {}
            tree_2 = Tree.load(fp, file_meta=meta_2)

        assert isinstance(tree_2, Tree)
        assert all(isinstance(n, Node) for n in tree_2)
        assert meta_2["$format_version"] == FILE_FORMAT_VERSION
        assert meta_2["$generator"].startswith("nutree/")
        assert meta_2["foo"] == "bar"
        assert fixture.trees_equal(tree, tree_2)

        # print(tree.format(repr="{node}"))
        # print(tree_2.format(repr="{node}"))

        assert tree.count == tree_2.count
        assert tree.first_child() is not tree_2.first_child()
        assert tree.first_child() == tree_2.first_child()

        a11 = tree_2.find("a11")
        assert a11.is_clone(), "Restored clone"
        assert len(tree_2.find_all("a11")) == 2

        assert tree._self_check()
        assert tree_2._self_check()

    def test_serialize_compressed(self):
        tree = fixture.create_tree()
        tree.add_child("äöüß: \u00e4\u00f6\u00fc\u00df")
        tree.add_child("emoji: 😀")

        with fixture.WritableTempFile("r+t") as temp_file:
            tree.save(temp_file.name, compression=zipfile.ZIP_DEFLATED)
            tree_2 = Tree.load(temp_file.name)
        assert fixture.trees_equal(tree, tree_2)

        with fixture.WritableTempFile("r+t") as temp_file:
            tree.save(temp_file.name, compression=zipfile.ZIP_BZIP2)
            tree_2 = Tree.load(temp_file.name)
        assert fixture.trees_equal(tree, tree_2)

        with fixture.WritableTempFile("r+t") as temp_file:
            tree.save(temp_file.name, compression=zipfile.ZIP_LZMA)
            tree_2 = Tree.load(temp_file.name)
        assert fixture.trees_equal(tree, tree_2)

    def _test_serialize_objects(self, *, mode: str):
        """Save/load an object tree with clones.

        Tree<'2009255653136'>
        ├── Node<'Department<Development>', data_id={012-345}>
        │   ├── Node<'Person<Alice, 23>', data_id={123-456}>
        │   ├── Node<'Person<Bob, 32>', data_id={234-456}>
        │   ╰── Node<'Person<Charleen, 43>', data_id={345-456}>
        ╰── Node<'Department<Marketing>', data_id={012-456}>
            ├── Node<'Person<Charleen, 43>', data_id={345-456}>
            ╰── Node<'Person<Dave, 54>', data_id={456-456}>
        """

        def _calc_id(tree, data):
            # print("calc_id", data)
            if isinstance(data, (fixture.Person, fixture.Department)):
                return data.guid
            return hash(data)

        def serialize_mapper(node: Node, data: dict) -> dict:
            if isinstance(node.data, fixture.Department):
                # _calc_id() already makes sure that the 'data_id' is set to `guid`
                # data["guid"] = node.data.guid
                data["type"] = "dept"
                data["name"] = node.data.name
            elif isinstance(node.data, fixture.Person):
                data["type"] = "person"
                data["name"] = node.data.name
                data["age"] = node.data.age
            return data

        def deserialize_mapper(parent, data):
            node_type = data["type"]
            # print("deserialize_mapper", data)
            if node_type == "person":
                data = fixture.Person(
                    name=data["name"], age=data["age"], guid=data["data_id"]
                )
            elif node_type == "dept":
                data = fixture.Department(name=data["name"], guid=data["data_id"])
            # print(f"deserialize_mapper -> {data}")
            return data

        # Use a tree
        tree = Tree(calc_data_id=_calc_id)
        fixture.create_tree(style="objects", clones=True, tree=tree)

        # print(tree._nodes_by_data_id)
        assert tree["{123-456}"].data.name == "Alice"
        alice = tree["{123-456}"].data
        assert tree[alice].data is alice

        with tempfile.TemporaryFile("r+t") as fp:
            if mode == "verbose":
                # Serialize
                tree.save(fp, mapper=serialize_mapper, key_map=False)
                text, data = _get_fp_result(fp, assert_len=474)
                assert '"data_id":"{012-345}"' in text
                assert '"data_id":"{123-456}"' in text
                assert (
                    '[0,{"data_id":"{012-345}","type":"dept","name":"Development"}]'
                    in text
                )
                assert (
                    '[1,{"data_id":"{123-456}","type":"person","name":"Alice","age":23}]'
                    in text
                )
                assert data["nodes"][0][1]["type"] == "dept"
                print("text", text)
            elif mode == "default":
                # Serialize
                tree.save(fp, mapper=serialize_mapper)
                text, data = _get_fp_result(fp, assert_len=475)
                assert '"i":"{012-345}"' in text
                assert '"i":"{123-456}"' in text
                assert data["nodes"][0][1]["i"] == "{012-345}"  # Department
                assert data["nodes"][0][1]["type"] == "dept"
                assert data["nodes"][1][1]["i"] == "{123-456}"  # Person
                assert data["nodes"][1][1]["type"] == "person"
            elif mode == "key_map":
                # Serialize
                key_map = {"type": "t", "name": "n", "age": "a", "data_id": "i"}
                tree.save(fp, mapper=serialize_mapper, key_map=key_map)
                text, data = _get_fp_result(fp, assert_len=453)
                assert '"i":"{012-345}"' in text
                assert '"i":"{123-456}"' in text
                assert data["nodes"][0][1]["i"] == "{012-345}"  # Department
                assert data["nodes"][0][1]["t"] == "dept"
                assert data["nodes"][1][1]["i"] == "{123-456}"  # Person
                assert data["nodes"][1][1]["t"] == "person"
            elif mode == "value_map":
                # Serialize
                key_map = {"type": "t", "name": "n", "age": "a", "data_id": "i"}
                value_map = {"type": ["person", "dept"]}
                tree.save(
                    fp,
                    mapper=serialize_mapper,
                    key_map=key_map,
                    value_map=value_map,
                )
                text, data = _get_fp_result(fp, assert_len=455)
                assert '"i":"{012-345}"' in text
                assert '"i":"{123-456}"' in text
                assert data["nodes"][0][1]["i"] == "{012-345}"  # Department
                assert data["nodes"][0][1]["t"] == 1
                assert data["nodes"][1][1]["i"] == "{123-456}"  # Person
                assert data["nodes"][1][1]["t"] == 0
            else:
                raise ValueError(f"Invalid mode: {mode!r}")

            # Deserialize
            fp.seek(0)
            meta_2 = {}
            tree_2 = Tree.load(fp, mapper=deserialize_mapper, file_meta=meta_2)
            tree_2.name = "tree_2"
            tree_2.print(repr="{node}")

        assert isinstance(tree_2, Tree)
        assert all(isinstance(n, Node) for n in tree_2)
        assert meta_2["$format_version"] == FILE_FORMAT_VERSION
        assert meta_2["$generator"].startswith("nutree/")
        assert fixture.trees_equal(tree, tree_2)
        assert tree.count == tree_2.count
        assert tree.first_child() is not tree_2.first_child()
        # TODO: implement `__eq__` for `Person` and `Department`
        # assert tree.first_child() == tree_2.first_child()

        # TODO: also make a test-case, where the mapper returns a data_id,
        #       so that `tree.first_child() == tree_2.first_child()`
        # assert tree.first_child() == tree_2.first_child()

        alice_2 = tree_2.find(match=".*Alice.*")
        assert alice_2.data.guid == "{123-456}"

        charleen_2 = tree_2.find(match=".*Charleen.*")
        assert charleen_2.is_clone(), "Restored clone"
        # assert len(tree_2.find_all("Charleen")) == 2

        assert tree._self_check()
        assert tree_2._self_check()

    def test_serialize_objects_verbose(self):
        self._test_serialize_objects(mode="verbose")

    def test_serialize_objects_default(self):
        self._test_serialize_objects(mode="default")

    def test_serialize_objects_key_map(self):
        self._test_serialize_objects(mode="key_map")

    def test_serialize_objects_value_map(self):
        self._test_serialize_objects(mode="value_map")

    def test_serialize_typed_tree_plain_str(self):
        tree = fixture.create_typed_tree(clones=True)
        assert isinstance(tree, TypedTree)

        with tempfile.TemporaryFile("r+t") as fp:
            # Serialize
            tree.save(fp, meta={"foo": "bar"})
            _text, _data = _get_fp_result(fp, assert_len=418)
            # Deserialize
            fp.seek(0)
            meta_2 = {}
            tree_2 = TypedTree.load(fp, file_meta=meta_2)

        assert isinstance(tree_2, TypedTree)
        assert all(isinstance(n, TypedNode) for n in tree_2)
        assert meta_2["$generator"].startswith("nutree/")
        assert meta_2["$format_version"] == FILE_FORMAT_VERSION
        assert meta_2["foo"] == "bar"
        assert fixture.trees_equal(tree, tree_2)

        # print(tree.format(repr="{node}"))
        # print(tree_2.format(repr="{node}"))

        assert tree.count == tree_2.count
        assert tree.first_child(kind=ANY_KIND) is not tree_2.first_child(kind=ANY_KIND)
        assert tree.first_child(kind=ANY_KIND) == tree_2.first_child(kind=ANY_KIND)

        fail1 = tree_2.find("fail1")
        assert fail1.is_clone(), "Restored clone"
        assert len(tree_2.find_all("fail1")) == 2

        assert tree._self_check()
        assert tree_2._self_check()

    def _test_serialize_typed_tree_objects(self, *, mode: str):
        """Save/load an object tree with clones.

        TypedTree<'fixture'>
        ├── TypedNode<kind=org_unit, Department<Development>, data_id='{012-345}'>
        │   ├── TypedNode<kind=manager, Person<Alice, 23>, data_id='{123-456}'>
        │   ├── TypedNode<kind=member, Person<Bob, 32>, data_id='{234-456}'>
        │   ╰── TypedNode<kind=member, Person<Charleen, 43>, data_id='{345-456}'>
        ╰── TypedNode<kind=org_unit, Department<Marketing>, data_id='{345-456}'>
            ├── TypedNode<kind=member, Person<Charleen, 43>, data_id='{345-456}'>
            ╰── TypedNode<kind=manager, Person<Dave, 54>, data_id='{456-456}'>
        """

        def _calc_id(tree, data):
            # print("calc_id", data)
            if isinstance(data, (fixture.Person, fixture.Department)):
                return data.guid
            return hash(data)

        def serialize_mapper(node, data):
            if isinstance(node.data, fixture.Department):
                # _calc_id() already makes sure that the 'data_id' is set to `guid`
                # data["guid"] = node.data.guid
                data["type"] = "dept"
                data["name"] = node.data.name
            elif isinstance(node.data, fixture.Person):
                data["type"] = "person"
                data["name"] = node.data.name
                data["age"] = node.data.age
            return data

        def deserialize_mapper(parent, data):
            node_type = data["type"]
            # print("deserialize_mapper", data)
            if node_type == "person":
                data = fixture.Person(
                    name=data["name"], age=data["age"], guid=data["data_id"]
                )
            elif node_type == "dept":
                data = fixture.Department(name=data["name"], guid=data["data_id"])
            # print(f"deserialize_mapper -> {data}")
            return data

        # Use a TypedTree
        tree = TypedTree(calc_data_id=_calc_id, name="fixture")
        fixture.create_typed_tree(style="objects", clones=True, tree=tree)

        # print(tree._nodes_by_data_id)
        assert tree["{123-456}"].data.name == "Alice"
        alice = tree["{123-456}"].data
        assert tree[alice].data is alice

        with tempfile.TemporaryFile("r+t") as fp:
            if mode == "verbose":
                # Serialize
                tree.save(fp, mapper=serialize_mapper, key_map=False, value_map=False)
                text, data = _get_fp_result(fp, assert_len=576)
                assert '"data_id":"{012-345}"' in text
                assert '"data_id":"{123-456}"' in text
                assert (
                    '[0,{"data_id":"{012-345}","kind":"org_unit","type":"dept","name":"Development"}]'
                    in text
                )
                assert (
                    '[1,{"data_id":"{123-456}","kind":"manager","type":"person","name":"Alice","age":23}]'
                    in text
                )
                assert data["nodes"][0][1]["type"] == "dept"
                print("text", text)
            elif mode == "default":
                # Serialize
                tree.save(fp, mapper=serialize_mapper)
                text, data = _get_fp_result(fp, assert_len=576)
                assert '"i":"{012-345}"' in text
                assert '"i":"{123-456}"' in text
                assert data["nodes"][0][1]["i"] == "{012-345}"  # Department
                assert data["nodes"][0][1]["type"] == "dept"
                assert data["nodes"][1][1]["i"] == "{123-456}"  # Person
                assert data["nodes"][1][1]["type"] == "person"

            elif mode == "key_map":
                # Serialize
                key_map = {
                    "type": "t",
                    "name": "n",
                    "age": "a",
                    "data_id": "i",
                    "kind": "k",
                }
                tree.save(fp, mapper=serialize_mapper, key_map=key_map, value_map=False)
                text, data = _get_fp_result(fp, assert_len=548)
                assert '"i":"{012-345}"' in text
                assert '"i":"{123-456}"' in text
                assert data["nodes"][0][1]["i"] == "{012-345}"  # Department
                assert data["nodes"][0][1]["t"] == "dept"
                assert data["nodes"][1][1]["i"] == "{123-456}"  # Person
                assert data["nodes"][1][1]["t"] == "person"

            elif mode == "value_map":
                # Serialize
                key_map = {"type": "t", "name": "n", "age": "a", "data_id": "i"}
                value_map = {"type": ["person", "dept"]}
                tree.save(
                    fp,
                    mapper=serialize_mapper,
                    key_map=key_map,
                    value_map=value_map,
                )
                text, data = _get_fp_result(fp, assert_len=548)
                assert '"i":"{012-345}"' in text
                assert '"i":"{123-456}"' in text
                assert data["nodes"][0][1]["i"] == "{012-345}"  # Department
                assert data["nodes"][0][1]["t"] == 1
                assert data["nodes"][1][1]["i"] == "{123-456}"  # Person
                assert data["nodes"][1][1]["t"] == 0

            else:
                raise ValueError(f"Invalid mode: {mode!r}")

            # Deserialize
            fp.seek(0)
            meta_2 = {}
            tree_2 = TypedTree.load(fp, mapper=deserialize_mapper, file_meta=meta_2)
            tree_2.name = "tree_2"
            tree_2.print(repr="{node}")

        assert isinstance(tree_2, TypedTree)
        assert all(isinstance(n, TypedNode) for n in tree_2)
        assert meta_2["$format_version"] == FILE_FORMAT_VERSION
        assert meta_2["$generator"].startswith("nutree/")
        assert fixture.trees_equal(tree, tree_2)
        assert tree.count == tree_2.count
        assert tree.first_child(kind=ANY_KIND) is not tree_2.first_child(kind=ANY_KIND)
        # TODO: implement `__eq__` for `Person` and `Department`
        # assert tree.first_child() == tree_2.first_child()

        # TODO: also make a test-case, where the mapper returns a data_id,
        #       so that `tree.first_child() == tree_2.first_child()`
        # assert tree.first_child() == tree_2.first_child()

        alice_2 = tree_2.find(match=".*Alice.*")
        assert alice_2.data.guid == "{123-456}"

        charleen_2 = tree_2.find(match=".*Charleen.*")
        assert charleen_2.is_clone(), "Restored clone"
        # assert len(tree_2.find_all("Charleen")) == 2

        assert tree._self_check()
        assert tree_2._self_check()

    def test_serialize_typed_tree_objects_verbose(self):
        self._test_serialize_typed_tree_objects(mode="verbose")

    def test_serialize_typed_tree_objects_default(self):
        self._test_serialize_typed_tree_objects(mode="default")

    def test_serialize_typed_tree_objects_key_map(self):
        self._test_serialize_typed_tree_objects(mode="key_map")

    def test_serialize_typed_tree_objects_value_map(self):
        self._test_serialize_typed_tree_objects(mode="value_map")

    def test_serialize_typed_tree_derived(self):
        """Save/load an object tree with clones, using  derived custom tree."""

        class MyTree(TypedTree):
            # TODO: when Py38 is dropped:
            # DEFAULT_KEY_MAP = TypedTree.DEFAULT_KEY_MAP
            #                       | { "type": "t", "name": "n", "age": "a", }
            DEFAULT_KEY_MAP = {
                "data_id": "i",
                "str": "s",
                "kind": "k",
                "type": "t",
                "name": "n",
                "age": "a",
            }
            DEFAULT_VALUE_MAP = {"type": ["person", "dept"]}

            def calc_data_id(tree, data):
                if hasattr(data, "guid"):
                    return data.guid
                return hash(data)

            def serialize_mapper(self, node: Node, data: dict):
                if isinstance(node.data, fixture.Department):
                    data["type"] = "dept"
                    data["name"] = node.data.name
                elif isinstance(node.data, fixture.Person):
                    data["type"] = "person"
                    data["name"] = node.data.name
                    data["age"] = node.data.age
                return data

            @staticmethod
            def deserialize_mapper(parent: Node, data: dict):
                node_type = data["type"]
                print("deserialize_mapper", data)
                if node_type == "person":
                    data = fixture.Person(
                        name=data["name"], age=data["age"], guid=data["data_id"]
                    )
                elif node_type == "dept":
                    data = fixture.Department(name=data["name"], guid=data["data_id"])
                print(f"deserialize_mapper -> {data}")
                return data

        # Use a TypedTree
        tree = MyTree(name="MyTree")
        fixture.create_typed_tree(style="objects", clones=True, tree=tree)

        # print(tree._nodes_by_data_id)
        assert tree["{123-456}"].data.name == "Alice"
        alice = tree["{123-456}"].data
        assert tree[alice].data is alice

        with tempfile.TemporaryFile("r+t") as fp:
            # Serialize
            tree.save(fp)
            # Check raw result file
            text, data = _get_fp_result(fp, assert_len=551)
            assert '"i":"{012-345}"' in text
            assert '"i":"{123-456}"' in text
            assert data["nodes"][0][1]["i"] == "{012-345}"  # Department
            assert data["nodes"][0][1]["t"] == 1
            assert data["nodes"][1][1]["i"] == "{123-456}"  # Person
            assert data["nodes"][1][1]["k"] == 1
            assert data["nodes"][1][1]["t"] == 0

            # Deserialize
            fp.seek(0)
            meta_2 = {}
            tree_2 = tree.load(fp, file_meta=meta_2)
            tree_2.name = "tree_2"
            tree_2.print(repr="{node}")

        assert isinstance(tree_2, TypedTree)
        assert all(isinstance(n, TypedNode) for n in tree_2)
        assert meta_2["$format_version"] == FILE_FORMAT_VERSION
        assert meta_2["$generator"].startswith("nutree/")
        assert fixture.trees_equal(tree, tree_2)
        assert tree.count == tree_2.count
        assert tree.first_child(kind=ANY_KIND) is not tree_2.first_child(kind=ANY_KIND)
        # TODO: implement `__eq__` for `Person` and `Department`
        # assert tree.first_child() == tree_2.first_child()

        # TODO: also make a test-case, where the mapper returns a data_id,
        #       so that `tree.first_child() == tree_2.first_child()`
        # assert tree.first_child() == tree_2.first_child()

        alice_2 = tree_2.find(match=".*Alice.*")
        assert alice_2.data.guid == "{123-456}"

        charleen_2 = tree_2.find(match=".*Charleen.*")
        assert charleen_2.is_clone(), "Restored clone"
        # assert len(tree_2.find_all("Charleen")) == 2

        assert tree._self_check()
        assert tree_2._self_check()

    def test_graph(self):
        tree = TypedTree("fixture")

        alice = tree.add("Alice")
        bob = tree.add("Bob")

        alice.add("Carol", kind="friends")

        alice.add("Bob", kind="family")
        bob.add("Alice", kind="family")
        bob.add("Dan", kind="friends")

        # carol.add(bob, kind="friends")

        assert fixture.check_content(
            tree,
            """
            TypedTree<*>
            +- child → Alice
            |  +- friends → Carol
            |  `- family → Bob
            `- child → Bob
               +- family → Alice
               `- friends → Dan
           """,
        )

        # with fixture.WritableTempFile("w", suffix=".png") as temp_file:

        #     tree.to_dotfile(
        #         # temp_file.name,
        #         "/Users/martin/Downloads/tree.png",
        #         format="png",
        #         add_root=False,
        #         # node_mapper=node_mapper,
        #         # edge_mapper=edge_mapper,
        #         # unique_nodes=False,
        #     )
        #     assert False


class TestToDictList:
    def test_to_dict_list(self):
        tree = fixture.create_typed_tree(clones=True)
        d = tree.to_dict_list()
        print(d)
        assert len(d) == 2, "two top nodes"
        assert isinstance(d, list)
        assert isinstance(d[0], dict)
        # TODO:
        assert isinstance(d[0]["data"], str)
        # assert "kind" in l[0]

    def test_serialize_to_dict_list(self):
        tree = fixture.create_tree()

        with tempfile.TemporaryFile("r+t") as fp:
            # Serialize
            json.dump(tree.to_dict_list(), fp)
            # Deserialize
            fp.seek(0)
            obj = json.load(fp)
            tree_2 = Tree.from_dict(obj)

        assert fixture.trees_equal(tree, tree_2)

        assert tree.first_child() is not tree_2.first_child()
        assert tree.first_child() == tree_2.first_child()
        assert tree.count == tree_2.count

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


class TestMermaid:
    def test_serialize_mermaid(self):
        """Save/load as object tree with clones."""
        KEEP_FILES = not fixture.is_running_on_ci() and False
        tree = fixture.create_tree(style="simple", clones=True, name="Root")

        with fixture.WritableTempFile("w", suffix=".md") as temp_file:
            tree.to_mermaid_flowchart(
                temp_file.name,
                # add_root=False,
                # headers=["classDef default fill:#f9f,stroke:#333,stroke-width:1px;"],
                # node_mapper=lambda node: f"{node}",
                # unique_nodes=False,
                # format="png",
                # mmdc_options={"--theme": "forest"},
            )
            if KEEP_FILES:  # save to tests/temp/...
                shutil.copy(
                    temp_file.name,
                    Path(__file__).parent / "temp/test_serialize_1.md",
                )

    def test_serialize_mermaid_typed(self):
        """Save/load as  object tree with clones."""
        KEEP_FILES = not fixture.is_running_on_ci() and False
        tree = fixture.create_typed_tree(style="simple", clones=True, name="Root")

        with fixture.WritableTempFile("w", suffix=".md") as temp_file:
            tree.to_mermaid_flowchart(
                temp_file.name,
                title="Typed Tree",
                direction="LR",
                # add_root=False,
                # node_mapper=lambda node: f"{node}",
            )
            if KEEP_FILES:  # save to tests/temp/...
                shutil.copy(
                    temp_file.name,
                    Path(__file__).parent / "temp/test_serialize_2.md",
                )

    @pytest.mark.xfail(reason="mmdc may not be installed")
    def test_serialize_mermaid_svg(self):
        """Save/load as typed object tree with clones."""
        KEEP_FILES = not fixture.is_running_on_ci() and False
        tree = fixture.create_typed_tree(style="simple", clones=True, name="Root")

        with fixture.WritableTempFile("w", suffix=".png") as temp_file:
            tree.to_mermaid_flowchart(
                temp_file.name,
                title="Typed Tree",
                direction="LR",
                format="svg",
                # add_root=False,
                # node_mapper=lambda node: f"{node}",
            )
            if KEEP_FILES:  # save to tests/temp/...
                shutil.copy(
                    temp_file.name,
                    Path(__file__).parent / "temp/test_serialize_2.png",
                )
