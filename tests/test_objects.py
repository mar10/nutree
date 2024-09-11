# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
# ruff: noqa: T201, T203 `print` found

import pytest

from nutree import Tree
from nutree.common import GenericNodeData


class Item:
    def __init__(self, name, price, count):
        self.name = name
        self.price = float(price)
        self.count = int(count)

    def __repr__(self):
        return f"Item<{self.name!r}, {self.price:.2f}$>"


class TestObjects:
    def setup_method(self):
        self.tree = Tree("fixture")

    def teardown_method(self):
        self.tree = None

    def test_objects(self):
        tree = self.tree

        n = tree.add("Records")
        let_it_be = Item("Let It Be", 12.34, 17)
        n.add(let_it_be)
        n.add(Item("Get Yer Ya-Ya's Out!", 23.45, 71))
        n = tree.add("Books")
        n.add(Item("The Little Prince", 3.21, 11))

        # print(f"{tree}\n" + tree.format(repr="{node.key}-{node.name}"))

        records = tree["Records"]
        assert records.name == "Records"
        print(tree.format(repr="{node.data}"))

        n = tree[let_it_be]
        assert n.data is let_it_be
        assert n.data.name == "Let It Be"
        assert n.name == repr(n.data)
        assert n.name == "Item<'Let It Be', 12.34$>"

        assert tree.find(match=".*Let It Be.*").data is let_it_be

        pony = Item("Dig A Pony", 0.99, 0)
        n.add(pony)

        get_back = Item("Get Back", 0.99, 0)
        n.add(get_back, data_id="123-456")

        print(tree.format(repr="{node.data}"))

        n = tree.find(pony)
        assert n.data is pony

        n = tree.find(get_back)
        assert n is None
        n = tree.find(data_id="123-000")
        assert n is None
        n = tree.find(data_id="123-456")
        assert n.data is get_back
        assert "Get Back" not in tree
        # FIXME: this should work
        # assert get_back in tree
        # assert "123-456" in tree

        with pytest.raises(ValueError):
            n.rename("foo")
        assert tree._self_check()

    def test_shadow_attrs_off(self):
        tree = Tree("fixture")

        records = tree.add("Records")
        let_it_be_item = Item("Let It Be", 12.34, 17)
        let_it_be_node = records.add(let_it_be_item)

        assert let_it_be_node.data is let_it_be_item
        assert let_it_be_node.data.name == "Let It Be"
        assert let_it_be_node.data.price == 12.34
        # Note caveat: `node.name` is not shadowed, but a native property:
        assert let_it_be_node.name == "Item<'Let It Be', 12.34$>"
        # Shadowing is off, so  `node.price` is off
        with pytest.raises(AttributeError):
            assert let_it_be_node.price == 12.34

    def test_shadow_attrs_true(self):
        tree = Tree("fixture", shadow_attrs=True)

        records = tree.add("Records")
        let_it_be_item = Item("Let It Be", 12.34, 17)
        let_it_be_node = records.add(let_it_be_item)

        assert let_it_be_node.data is let_it_be_item
        assert let_it_be_node.data.name == "Let It Be"
        assert let_it_be_node.data.price == 12.34

        # Note caveat: `node.name` is not shadowed, but a native property:
        assert let_it_be_node.name == "Item<'Let It Be', 12.34$>"
        with pytest.raises(AttributeError):
            let_it_be_node.name = "foo"

        # `node.price` is alliased to `node.data.price`
        assert let_it_be_node.price == 12.34

        # Shadow attributes are readonly
        with pytest.raises(AttributeError):
            let_it_be_node.price = 9.99


class TestGenericNodeData:
    def setup_method(self):
        self.tree = Tree("fixture")

    def teardown_method(self):
        self.tree = None

    def test_constructor(self):
        d: dict = {"a": 1, "b": 2}

        with pytest.raises(TypeError, match="dict_inst must be a dictionary"):
            _ = GenericNodeData("foo")

        with pytest.raises(TypeError):
            _ = GenericNodeData("foo", **d)

        with pytest.raises(TypeError):
            _ = GenericNodeData("foo", d)

        with pytest.raises(ValueError):
            _ = GenericNodeData(d, foo="bar")

        gnd = GenericNodeData(d)
        assert gnd._dict is d, "dict should be stored as reference"

        assert gnd.a == 1, "GenericNodeData should support attribute access"
        with pytest.raises(AttributeError):
            _ = gnd.foo

        assert gnd["a"] == 1, "GenericNodeData should support item access"
        with pytest.raises(KeyError):
            _ = gnd["foo"]

        gnd = GenericNodeData(**d)
        assert gnd._dict is not d, "unpacked dict should be stored as copy"

    def test_dict(self):
        tree = Tree(shadow_attrs=True)

        d: dict = {"a": 1, "b": 2}

        # We cannot simply add a dict, because it is unhashable
        with pytest.raises(TypeError, match="unhashable type: 'dict'"):
            _ = tree.add(d)

        # But we can wrap it in a GenericNodeData instance
        node = tree.add(GenericNodeData(d))

        # The dict is stored as reference

        assert isinstance(node.data, GenericNodeData)
        assert node.data._dict is d, "dict should be stored as reference"
        assert node.a == 1, "should support attribute access via shadowing"

        with pytest.raises(AttributeError):
            # should not allow access to non-existing attributes
            _ = node.foo

        with pytest.raises(TypeError, match="'Node' object is not subscriptable"):
            # should NOT support item access via indexing
            _ = node["a"]

        assert node.data.a == 1, "should support attribute access via data"

        with pytest.raises(AttributeError):
            # should not allow access to non-existing attributes
            _ = node.data.foo

        assert node.data["a"] == 1, "should support item access via data"

        with pytest.raises(AttributeError, match="object has no attribute 'a'"):
            # Shadowing is read-only
            _ = node.data.a = 99

        with pytest.raises(
            TypeError, match="'GenericNodeData' object does not support item assignment"
        ):
            # Index access is read-only
            _ = node.data["a"] = 99

        with pytest.raises(
            TypeError, match="'GenericNodeData' object does not support item assignment"
        ):
            _ = node.data["foo"] = 99

        # We need to access the dict directly to modify it
        node.data._dict["a"] = 99
        assert node.a == 99, "should reflect changes in dict"

    def test_generic_node_data_unpacked(self):
        tree = Tree(shadow_attrs=True)

        d: dict = {"a": 1, "b": 2}

        # We can also unpack the dict
        node = tree.add(GenericNodeData(**d))

        assert node.data._dict is not d, "unpacked dict should be stored as copy"
        assert node.data._dict == {"a": 1, "b": 2}
        assert node.a == 1, "GenericNodeData should support attribute access"

    def test_dataclass(self):

        from dataclasses import FrozenInstanceError, dataclass

        @dataclass
        class Item:
            name: str
            price: float
            count: int

        @dataclass(frozen=True)
        class FrozenItem:
            name: str
            price: float
            count: int

        tree = Tree(shadow_attrs=True)

        # We cannot simply add a dataclass, because it is mutable and unhashable
        with pytest.raises(TypeError, match="unhashable type: 'Item'"):
            _ = tree.add(Item("Let It Be", 12.34, 17))

        # But we can add frozen dataclasses
        item = FrozenItem("Let It Be", 12.34, 17)
        dict_node = tree.add(item)

        # Frozen dataclasses are immutable
        with pytest.raises(FrozenInstanceError):
            item.count += 1

        tree.print()

        assert isinstance(dict_node.data, FrozenItem)
        assert dict_node.data is item, "dataclass should be stored as reference"
        assert dict_node.price == 12.34, "should support attribute access via shadowing"
        with pytest.raises(AttributeError):
            _ = dict_node.foo
