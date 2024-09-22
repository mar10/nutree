"""
Generic tree generator for test data.
"""

import datetime

import pytest
from nutree.common import GenericNodeData
from nutree.tree import Tree
from nutree.tree_generator import (
    BlindTextRandomizer,
    DateRangeRandomizer,
    RangeRandomizer,
    SampleRandomizer,
    SparseBoolRandomizer,
    TextRandomizer,
    ValueRandomizer,
    fab,
)
from nutree.typed_tree import TypedTree

from tests import fixture


class TestBase:
    def test_simple(self):
        structure_def = {
            "name": "fmea",
            #: Types define the default properties of the nodes
            "types": {
                #: Default properties for all node types
                "*": {":factory": GenericNodeData},
                #: Specific default properties for each node type
                "function": {"icon": "bi bi-gear"},
                "failure": {"icon": "bi bi-exclamation-triangle"},
                "cause": {"icon": "bi bi-tools"},
                "effect": {"icon": "bi bi-lightning"},
            },
            #: Relations define the possible parent / child relationships between
            #: node types and optionally override the default properties.
            "relations": {
                "__root__": {
                    "function": {
                        ":count": 3,
                        "title": "Function {hier_idx}",
                        "date": DateRangeRandomizer(
                            datetime.date(2020, 1, 1), datetime.date(2020, 12, 31)
                        ),
                        "date2": DateRangeRandomizer(
                            datetime.date(2020, 1, 1), 365, probability=0.99
                        ),
                        "value": ValueRandomizer("foo", probability=0.5),
                        "expanded": SparseBoolRandomizer(probability=0.5),
                        "state": SampleRandomizer(["open", "closed"], probability=0.99),
                    },
                },
                "function": {
                    "failure": {
                        ":count": RangeRandomizer(1, 3),
                        "title": "Failure {hier_idx}",
                    },
                },
                "failure": {
                    "cause": {
                        ":count": RangeRandomizer(1, 3, probability=0.99),
                        "title": "Cause {hier_idx}",
                    },
                    "effect": {
                        ":count": RangeRandomizer(1, 3),
                        "title": "Effect {hier_idx}",
                    },
                },
            },
        }
        tree = Tree.build_random_tree(structure_def)
        tree.print()
        assert type(tree) is Tree
        assert tree.calc_height() == 3

        tree2 = TypedTree.build_random_tree(structure_def)
        tree2.print()
        assert type(tree2) is TypedTree
        assert tree2.calc_height() == 3

        # Save and load with GenericNodeData mappers
        with fixture.WritableTempFile("r+t") as temp_file:
            tree.save(
                temp_file.name,
                compression=True,
                mapper=GenericNodeData.serialize_mapper,
            )
            tree3 = Tree.load(temp_file.name, mapper=GenericNodeData.deserialize_mapper)
        tree3.print()
        assert fixture.trees_equal(tree, tree3)

    def test_fabulist(self):
        if not fab:
            pytest.skip("fabulist not installed")

        structure_def = {
            "name": "fmea",
            #: Types define the default properties of the nodes
            "types": {
                #: Default properties for all node types (optional, default
                #: is GenericNodeData)
                "*": {":factory": GenericNodeData},
                #: Specific default properties for each node type
                "function": {"icon": "bi bi-gear"},
                "failure": {"icon": "bi bi-exclamation-triangle"},
                "cause": {"icon": "bi bi-tools"},
                "effect": {"icon": "bi bi-lightning"},
            },
            #: Relations define the possible parent / child relationships between
            #: node types and optionally override the default properties.
            "relations": {
                "__root__": {
                    "function": {
                        ":count": 3,
                        "title": TextRandomizer(("{idx}: Provide $(Noun:plural)",)),
                        "details": BlindTextRandomizer(dialect="ipsum"),
                        "expanded": True,
                    },
                },
                "function": {
                    "failure": {
                        ":count": RangeRandomizer(1, 3),
                        "title": TextRandomizer("$(Noun:plural) not provided"),
                    },
                },
                "failure": {
                    "cause": {
                        ":count": RangeRandomizer(1, 3),
                        "title": TextRandomizer("$(Noun:plural) not provided"),
                    },
                    "effect": {
                        ":count": RangeRandomizer(1, 3),
                        "title": TextRandomizer("$(Noun:plural) not provided"),
                    },
                },
            },
        }
        tree = TypedTree.build_random_tree(structure_def)
        tree.print()

        assert type(tree) is TypedTree


class TestRandomizers:
    def test_range(self):
        r = RangeRandomizer(1, 3)
        for v in (r.generate() for _ in range(100)):
            assert isinstance(v, int)
            assert 1 <= v <= 3

        r = RangeRandomizer(1.0, 3.0)
        for v in (r.generate() for _ in range(100)):
            assert isinstance(v, float)
            assert 1 <= v <= 3
