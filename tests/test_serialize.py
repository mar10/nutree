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

        Tree<'4409537248'>
        ├── Node<'Department<Development>', data_id=275596153>
        │   ├── Node<'Person<Alice, 23>', data_id=275596168>
        │   ├── Node<'Person<Bob, 32>', data_id=275596177>
        │   ╰── Node<'Person<Charleen, 43>', data_id=275596195>
        ╰── Node<'Department<Marketing>', data_id=275596186>
            ├── Node<'Person<Charleen, 43>', data_id=275596195>
            ╰── Node<'Person<Dave, 54>', data_id=275596204>
        """
        tree = Tree()

        dev = tree.add(fixture.Department("Development"))
        dev.add(fixture.Person("Alice", 23))
        dev.add(fixture.Person("Bob", 32))
        markt = tree.add(fixture.Department("Marketing"))
        charleen = markt.add(fixture.Person("Charleen", 43))
        markt.add(fixture.Person("Dave", 54))
        dev.add(charleen)

        # print(tree.format())
        print(tree.format(repr="{node}"))

        def serialize_mapper(node, data):
            if isinstance(node.data, fixture.Department):
                data["type"] = "dept"
                data["name"] = node.data.name
            elif isinstance(node.data, fixture.Person):
                data["type"] = "person"
                data["name"] = node.data.name
                data["age"] = node.data.age
            return data

        def deserialize_mapper(parent, data):
            node_type = data["type"]
            if node_type == "person":
                data = fixture.Person(name=data["name"], age=data["age"])
            elif node_type == "dept":
                data = fixture.Department(name=data["name"])
            return data

        with tempfile.TemporaryFile("r+t") as fp:
            # Serialize
            tree.save(fp, mapper=serialize_mapper)
            # Deserialize
            fp.seek(0)
            tree_2 = Tree.load(fp, mapper=deserialize_mapper)

        # print(obj)
        print(tree_2.format())

        assert fixture.trees_equal(tree, tree_2)

        assert tree.count == tree_2.count
        assert tree.first_child is not tree_2.first_child

        # TODO: also make a test-case, where the mapper returns a data_id,
        #       so that `tree.first_child == tree_2.first_child`
        # assert tree.first_child == tree_2.first_child

        charleen_2 = tree_2.find(match=".*Charleen.*")
        assert charleen_2.is_clone(), "Restored clone"
        # assert len(tree_2.find_all("Charleen")) == 2

        assert tree._self_check()
        assert tree_2._self_check()
