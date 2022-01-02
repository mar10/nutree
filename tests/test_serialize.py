# -*- coding: utf-8 -*-
# (c) 2021-2022 Martin Wendt and contributors; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import json
import tempfile

from nutree import Tree

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
