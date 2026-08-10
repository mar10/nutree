# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """

# ruff: noqa: T201, T203 `print` found

from __future__ import annotations

import copy

from nutree.typed_tree import TypedTree

from . import fixture

SIMPLE_TREE_REPR = """
                   Tree<*>
                   +- A
                   |  +- a1
                   |  |  +- a11
                   |  |  `- a12
                   |  `- a2
                   `- B
                      `- b1
                         `- b11
                   """
OBJ_TREE_REPR = """
                Tree<*>
                +- Department<Development>
                |  +- Person<Alice, 23>
                |  `- Person<Bob, 32>
                `- Department<Marketing>
                   +- Person<Charleen, 43>
                   `- Person<Dave, 54>
                """
TYPED_OBJ_TREE_REPR = """
                      TypedTree<*>
                      +- org_unit → Department<Development>
                      |  +- manager → Person<Alice, 23>
                      |  `- member → Person<Bob, 32>
                      `- org_unit → Department<Marketing>
                         +- member → Person<Charleen, 43>
                         `- manager → Person<Dave, 54>
                      """


class TestBasics:
    def test_tree_copy(self):
        tree = fixture.create_tree_objects()
        assert fixture.check_content(tree, OBJ_TREE_REPR)

        tree_copy = tree.copy()

        assert fixture.check_content(tree_copy, OBJ_TREE_REPR)

        # Check that the copied nodes are different objects, but have the same content
        for node, node_copy in zip(tree.iterator(), tree_copy.iterator(), strict=True):
            assert node is not node_copy
            assert node.data is node_copy.data

    def test_shallow_copy(self):
        tree = fixture.create_tree_objects()
        assert fixture.check_content(tree, OBJ_TREE_REPR)

        tree_copy = copy.copy(tree)

        assert fixture.check_content(tree_copy, OBJ_TREE_REPR)

        # Check that the copied nodes AND DATA are different objects
        for node, node_copy in zip(tree.iterator(), tree_copy.iterator(), strict=True):
            assert node is not node_copy
            assert node.data is node_copy.data

    def test_deepcopy(self):
        tree = fixture.create_tree_objects()
        assert fixture.check_content(tree, OBJ_TREE_REPR)

        tree_copy = copy.deepcopy(tree)

        assert fixture.check_content(tree_copy, OBJ_TREE_REPR)

        # Check that the copied nodes are different object, but have the same content
        for node, node_copy in zip(tree.iterator(), tree_copy.iterator(), strict=True):
            assert node is not node_copy
            assert node.data.name == node_copy.data.name
            assert node.data is not node_copy.data

    def test_typed_shallow_copy(self):
        tree = fixture.create_typed_tree_objects()
        assert fixture.check_content(tree, TYPED_OBJ_TREE_REPR)
        assert isinstance(tree, TypedTree)

        # tree_copy = copy.copy(tree)
        tree_copy = tree.copy()
        assert isinstance(tree_copy, TypedTree)

        assert fixture.check_content(tree_copy, TYPED_OBJ_TREE_REPR)

        # Check that the copied nodes AND DATA are different objects
        for node, node_copy in zip(tree.iterator(), tree_copy.iterator(), strict=True):
            assert node is not node_copy
            assert node.data is node_copy.data

    def test_typed_deepcopy(self):
        tree = fixture.create_typed_tree_objects()

        tree_copy = copy.deepcopy(tree)

        assert fixture.check_content(tree_copy, TYPED_OBJ_TREE_REPR)

        # Check that the copied nodes are different object, but have the same content
        for node, node_copy in zip(tree.iterator(), tree_copy.iterator(), strict=True):
            assert node is not node_copy
            assert node.data.name == node_copy.data.name
            assert node.data is not node_copy.data
