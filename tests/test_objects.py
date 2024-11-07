# (c) 2021-2024 Martin Wendt; see https://github.com/mar10/nutree
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
""" """
# ruff: noqa: T201, T203 `print` found
# pyright: reportOptionalMemberAccess=false
# mypy: disable-error-code="annotation-unchecked"

import pytest
from nutree import Tree
from nutree.common import DictWrapper, UniqueConstraintError


class Item:
    def __init__(self, name, price, count):
        self.name = name
        self.price = float(price)
        self.count = int(count)

    def __repr__(self):
        return f"Item<{self.name!r}, {self.price:.2f}$>"


class TestObjects:
    def setup_method(self, method):
        self.tree = Tree("fixture")

    def teardown_method(self, method):
        self.tree = None

    def test_objects(self):
        assert self.tree is not None
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

    def test_forward_attrs_off(self):
        tree = Tree("fixture")

        records = tree.add("Records")
        let_it_be_item = Item("Let It Be", 12.34, 17)
        let_it_be_node = records.add(let_it_be_item)

        assert let_it_be_node.data is let_it_be_item
        assert let_it_be_node.data.name == "Let It Be"
        assert let_it_be_node.data.price == 12.34
        # Note caveat: `node.name` is not forwarded, but a native property:
        assert let_it_be_node.name == "Item<'Let It Be', 12.34$>"
        # Forwarding is off, so  `node.price` is unknown
        with pytest.raises(AttributeError):
            assert let_it_be_node.price == 12.34

    def test_forward_attrs_true(self):
        tree = Tree("fixture", forward_attrs=True)

        records = tree.add("Records")
        let_it_be_item = Item("Let It Be", 12.34, 17)
        let_it_be_node = records.add(let_it_be_item)

        assert let_it_be_node.data is let_it_be_item
        assert let_it_be_node.data.name == "Let It Be"
        assert let_it_be_node.data.price == 12.34

        # Note caveat: `node.name` is not forwardeded, but a native property:
        assert let_it_be_node.name == "Item<'Let It Be', 12.34$>"
        with pytest.raises(AttributeError):
            let_it_be_node.name = "foo"  # type: ignore

        # `node.price` is alliased to `node.data.price`
        assert let_it_be_node.price == 12.34

        # forward-attributes are readonly
        with pytest.raises(AttributeError):
            let_it_be_node.price = 9.99  # type: ignore


class TestDictWrapper:
    def setup_method(self):
        self.tree = Tree("fixture")

    def teardown_method(self):
        self.tree = None

    def test_constructor(self):
        d: dict = {"a": 1, "b": 2}

        with pytest.raises(TypeError, match="dict_inst must be a dictionary"):
            _ = DictWrapper("foo")  # type: ignore

        with pytest.raises(TypeError):
            _ = DictWrapper("foo", **d)  # type: ignore

        with pytest.raises(TypeError):
            _ = DictWrapper("foo", d)  # type: ignore

        with pytest.raises(ValueError):
            _ = DictWrapper(d, foo="bar")

        dw = DictWrapper(d)
        assert dw._dict is d, "dict should be stored as reference"

        with pytest.raises(AttributeError):
            _ = dw.a  # type: ignore
        with pytest.raises(AttributeError):
            _ = dw.foo  # type: ignore

        assert dw["a"] == 1, "DictWrapper should support item read access"
        with pytest.raises(KeyError):
            _ = dw["foo"]

        dw = DictWrapper(**d)
        assert dw._dict is not d, "unpacked dict should be stored as copy"

    def test_eq(self):
        d: dict = {"a": 1, "b": 2}
        dw = DictWrapper(d)

        assert dw is not d
        assert dw._dict is d

        assert dw == d
        assert dw == {"b": 2, "a": 1}

        assert dw != {"a": 1, "b": 3}
        assert dw != {"a": 1}
        assert dw != {"a": 1, "b": 2, "c": 3}

        d2: dict = {"a": 1, "b": 2}
        dw2 = DictWrapper(d2)
        assert dw._dict is not dw2._dict
        assert dw == dw2
        assert dw == DictWrapper({"b": 2, "a": 1})

        assert dw != DictWrapper({"a": 1, "b": 3})
        assert dw != DictWrapper({"a": 1})
        assert dw != DictWrapper({"a": 1, "b": 2, "c": 3})

    def test_dict(self):
        tree = Tree(forward_attrs=True)

        d: dict = {"a": 1, "b": 2}

        # We cannot simply add a dict, because it is unhashable
        with pytest.raises(TypeError, match="unhashable type: 'dict'"):
            _ = tree.add(d)

        # But we can wrap it in a DictWrapper instance
        node = tree.add(DictWrapper(d))
        with pytest.raises(UniqueConstraintError):
            _ = tree.add(DictWrapper(d))
        tree.print(repr="{node}")
        # raise
        # The dict is stored as reference

        assert isinstance(node.data, DictWrapper)
        assert node.data._dict is d, "dict should be stored as reference"

        with pytest.raises(AttributeError):
            _ = node.a  # should not support attribute access via forwarding

        with pytest.raises(AttributeError):
            # should not allow access to non-existing attributes
            _ = node.foo

        with pytest.raises(TypeError, match="'Node' object is not subscriptable"):
            # should NOT support item access via indexing
            _ = node["a"]  # type: ignore

        with pytest.raises(AttributeError):
            # should not support attribute access via data
            _ = node.data.a  # type: ignore

        with pytest.raises(AttributeError):
            # should not allow access to non-existing attributes
            _ = node.data.foo  # type: ignore

        assert node.data["a"] == 1, "should support item access via data"

        with pytest.raises(AttributeError, match="object has no attribute 'a'"):
            # Forwarding is read-only
            _ = node.data.a = 99  # type: ignore

        # Index access is writable
        node.data["a"] = 99
        assert node.data._dict["a"] == 99, "should reflect changes in dict"
        assert node.data["a"] == 99, "should reflect changes in dict via item access"

        node.data["foo"] = "bar"
        assert node.data._dict["foo"] == "bar"

        tree._self_check()

    def test_wrapped_dict_unpacked(self):
        tree = Tree(forward_attrs=True)

        d: dict = {"a": 1, "b": 2}

        # We can also unpack the dict
        node = tree.add(DictWrapper(**d))

        assert node.data._dict is not d, "unpacked dict should be stored as copy"
        assert node.data._dict == {"a": 1, "b": 2}
        with pytest.raises(AttributeError):
            _ = node.a
        assert node.data._dict["a"] == 1
        assert node.data["a"] == 1

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

        tree = Tree(forward_attrs=True)

        # We cannot simply add a dataclass, because it is mutable and unhashable
        with pytest.raises(TypeError, match="unhashable type: 'Item'"):
            _ = tree.add(Item("Let It Be", 12.34, 17))

        # But we can add frozen dataclasses
        item = FrozenItem("Let It Be", 12.34, 17)
        dict_node = tree.add(item)

        # Frozen dataclasses are immutable
        with pytest.raises(FrozenInstanceError):
            item.count += 1  # type: ignore

        # We can also add by passing the data_id as keyword argument:
        _ = tree.add(item, data_id="123-456")

        tree.print()

        assert isinstance(dict_node.data, FrozenItem)
        assert dict_node.data is item, "dataclass should be stored as reference"
        assert (
            dict_node.price == 12.34
        ), "should support attribute access via forwardinging"
        with pytest.raises(AttributeError):
            _ = dict_node.foo

    def test_callback(self):
        from dataclasses import dataclass

        d: dict = {"a": 1, "guid": "123-456"}

        @dataclass
        class Item:
            a: int
            guid: str

        dc = Item(2, "234-567")

        def _calc_id(tree, data):
            if isinstance(data, Item):
                return hash(data.guid)
            elif isinstance(data, dict):
                return hash(data["guid"])
            return hash(data)

        tree = Tree(calc_data_id=_calc_id, forward_attrs=True)

        n1 = tree.add(d)
        n2 = tree.add(dc)

        assert n1.data is d
        assert n1.data["a"] == 1

        assert n2.data is dc
        assert n2.a == 2
